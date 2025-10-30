# cluster_starters.py
from dotenv import load_dotenv
load_dotenv()

import os, re, json, math, random
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone

import numpy as np
from langsmith import Client

# --- CONFIG ---
PROJECT        = os.getenv("LANGCHAIN_PROJECT", "fh-swf-bot")
LOOKBACK_DAYS  = int(os.getenv("STARTERS_LOOKBACK_DAYS", "30"))
MAX_CLUSTERS   = int(os.getenv("STARTERS_MAX", "6"))   # wie viele Starters
OUT_PATH       = os.getenv("STARTERS_OUT", "starters.json")
USE_OPENAI_EMB = os.getenv("USE_OPENAI_EMB", "1") == "1"  # sonst sentence-transformers
OPENAI_EMB_MODEL = os.getenv("OPENAI_EMB_MODEL", "text-embedding-3-small")  # günstig & gut
SEED           = 7

random.seed(SEED)
np.random.seed(SEED)

ICON_PATTERNS = [
    (re.compile(r"(dual|d[uü]al|betrieb|praxis)", re.I), "/public/university.svg"),
    (re.compile(r"(sprechstunde|prof|dozent|gawron)", re.I), "/public/professor.svg"),
    (re.compile(r"(raum|zimmer|p\d{3}|belegung|stundenplan)", re.I), "/public/time.svg"),
    (re.compile(r"(pr(ü|u)f|klausur|anmeldung)", re.I), "/public/schedule.svg"),
    (re.compile(r"(informatik|studieng(ä|a)nge|bachelor|master)", re.I), "/public/study.svg"),
]
DEFAULT_ICON = "/public/study.svg"

def pick_icon(text: str) -> str:
    for rx, icon in ICON_PATTERNS:
        if rx.search(text or ""):
            return icon
    return DEFAULT_ICON

def normalize_question(q: str) -> str:
    q = (q or "").strip()
    q = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "<date>", q)
    q = re.sub(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b", "<date>", q)
    q = re.sub(r"\b\d{1,2}:\d{2}\b", "<time>", q)
    q = re.sub(r"\bp\d{3}\b", "<room>", q, flags=re.I)
    q = re.sub(r"\b\d+\b", "<num>", q)
    q = re.sub(r"[^\wäöüÄÖÜß<> ]+", " ", q)
    q = re.sub(r"\s+", " ", q).strip()
    return q

def load_runs_and_feedback():
    from datetime import timezone
    from collections import defaultdict
    client = Client()

    since = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)

    def as_aware_utc(dt):
        """macht datetime vergleichbar (aware, UTC)."""
        if dt is None:
            return None
        if dt.tzinfo is None:
            # Annahme: LangSmith liefert naive Zeiten in UTC
            return dt.replace(tzinfo=timezone.utc)
        # auf UTC normieren
        return dt.astimezone(timezone.utc)

    runs = []
    for run in client.list_runs(project_name=PROJECT, limit=2000):
        # nur unsere Root-Runs
        if getattr(run, "name", "") != "chat_turn":
            continue

        rt = as_aware_utc(getattr(run, "start_time", None))
        # wenn start_time vorhanden ist, lokal nach since filtern
        if rt and rt < since:
            continue

        runs.append(run)

    # Feedback je Run sammeln
    fb_by_run = defaultdict(list)
    for fb in client.list_feedback(project_name=PROJECT):
        rid = getattr(fb, "run_id", None)
        if rid:
            fb_by_run[str(rid)].append(fb)

    rows = []
    for r in runs:
        inputs = getattr(r, "inputs", {}) or {}
        q = (inputs.get("user_message") or "").strip()
        if not q:
            continue

        fbs = fb_by_run.get(str(r.id), [])
        pos = sum(1 for f in fbs if (getattr(f, "score", None) or 0) >= 1)
        neg = sum(
            1
            for f in fbs
            if getattr(f, "score", None) is not None and getattr(f, "score") <= 0
        )
        score = pos - neg

        rows.append({"run_id": str(r.id), "question": q, "score": score})

    return rows


def embed_texts(texts: list[str]) -> np.ndarray:
    if USE_OPENAI_EMB:
        # OpenAI-Embeddings
        from langchain_openai import OpenAIEmbeddings
        model = OPENAI_EMB_MODEL
        emb = OpenAIEmbeddings(model=model)
        vecs = emb.embed_documents(texts)
        return np.array(vecs, dtype=np.float32)
    else:
        # Lokale Embeddings (keine externen Kosten, aber größeres Modell)
        from sentence_transformers import SentenceTransformer
        model_name = os.getenv("LOCAL_EMB_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        model = SentenceTransformer(model_name)
        vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
        return np.array(vecs, dtype=np.float32)

def cluster_kmeans(X: np.ndarray, k: int):
    from sklearn.cluster import KMeans
    k = max(2, min(k, len(X)))
    km = KMeans(n_clusters=k, n_init=10, random_state=SEED)
    labels = km.fit_predict(X)
    centers = km.cluster_centers_
    return labels, centers

def tfidf_keywords(texts: list[str], topk: int = 4) -> list[list[str]]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    vec = TfidfVectorizer(max_features=5000, ngram_range=(1,2), stop_words=None)
    tf = vec.fit_transform(texts)
    terms = np.array(vec.get_feature_names_out())
    keywords_per_doc = []
    for i in range(tf.shape[0]):
        row = tf.getrow(i)
        if row.nnz == 0:
            keywords_per_doc.append([])
            continue
        idxs = row.indices[row.data.argsort()[::-1]][:topk]
        keywords_per_doc.append(terms[idxs].tolist())
    return keywords_per_doc

def label_clusters_by_keywords(texts, labels):
    # einfache Heuristik: häufigste TF-IDF-Terme pro Cluster
    kws_per_doc = tfidf_keywords(texts, topk=5)
    cluster_kws = defaultdict(Counter)
    for txt, lab, kws in zip(texts, labels, kws_per_doc):
        for kw in kws:
            cluster_kws[lab][kw] += 1
    titles = {}
    for lab, counter in cluster_kws.items():
        top = [w for w,_ in counter.most_common(3)]
        if top:
            titles[lab] = " / ".join(top)
        else:
            titles[lab] = f"Thema {lab+1}"
    return titles

def main():
    rows = load_runs_and_feedback()
    if not rows:
        print("Keine Daten aus LangSmith gefunden.")
        return

    # Texte + Gewichte (Gewicht aus Feedback; min 1)
    texts = [normalize_question(r["question"]) for r in rows]
    weights = [max(1.0, 1.0 + 0.5 * r["score"]) for r in rows]  # pos Feedback etwas stärker
    # Kleinigkeit: Duplikate reduzieren (optional)
    uniq_map = {}
    for i, t in enumerate(texts):
        if t not in uniq_map:
            uniq_map[t] = {"idxs": [], "weight": 0.0}
        uniq_map[t]["idxs"].append(i)
        uniq_map[t]["weight"] += weights[i]

    uniq_texts = list(uniq_map.keys())
    uniq_weights = [uniq_map[t]["weight"] for t in uniq_texts]

    # Embeddings
    X = embed_texts(uniq_texts)

    # K bestimmen (heuristisch): min( MAX_CLUSTERS*2 , sqrt(N) ), dann auf MAX_CLUSTERS reduzieren
    est_k = max(2, min(int(math.sqrt(len(uniq_texts))) or 2, MAX_CLUSTERS * 2))
    labels, _ = cluster_kmeans(X, est_k)

    # Cluster-Scores & Repräsentanten wählen
    cluster_items = defaultdict(list)
    for t, w, lab in zip(uniq_texts, uniq_weights, labels):
        cluster_items[lab].append((t, w))

    # Cluster-Titel heuristisch
    titles = label_clusters_by_keywords(uniq_texts, labels)

    # pro Cluster Top-Item (höchstes Gewicht) → repräsentative Frage
    reps = []
    for lab, items in cluster_items.items():
        items.sort(key=lambda x: x[1], reverse=True)
        top_text, top_weight = items[0]
        reps.append({
            "cluster": int(lab),
            "title": titles.get(lab, f"Thema {lab+1}"),
            "message": top_text,
            "weight": float(top_weight),
        })

    # auf MAX_CLUSTERS beschränken
    reps.sort(key=lambda x: x["weight"], reverse=True)
    reps = reps[:MAX_CLUSTERS]

    def make_label_from_question(q: str, max_len=40) -> str:
        q = q.strip().rstrip("?!.")
        # Nimm die ersten 5–7 Wörter für ein kurzes, natürliches Label
        words = q.split()
        label = " ".join(words[:7])
        if len(words) > 7:
            label += "…"
        return label[0].upper() + label[1:]

    starters = []
    for r in reps:
        msg = r["message"]
        label = make_label_from_question(msg)
        starters.append({
            "label": label,
            "message": msg,
            "icon": pick_icon(msg),
            "cluster": r["cluster"],
            "score": round(r["weight"], 2),
        })


    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "project": PROJECT,
            "generated_at": datetime.utcnow().isoformat()+"Z",
            "method": "kmeans+tfidf",
            "items": starters
        }, f, ensure_ascii=False, indent=2)

    print(f"OK: {len(starters)} Cluster-Starters → {OUT_PATH}")

if __name__ == "__main__":
    main()
