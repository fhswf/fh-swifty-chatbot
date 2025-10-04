# FH-SWF Web Crawler

## Vue d'ensemble

Ce répertoire contient deux crawlers pour le site web fh-swf.de:

1. **crawl_fhswf.py** - Crawler de fichiers (sauvegarde sur disque)
2. **crawl_to_sqlite.py** - Crawler avec indexation SQLite (**NOUVEAU**)
3. **query_db.py** - Utilitaire pour explorer la base de données SQLite

## 🆕 Crawler SQLite (Recommandé)

Le nouveau crawler SQLite indexe tout le contenu du site dans une base de données structurée, permettant des recherches rapides et des analyses complexes.

### Caractéristiques

- ✅ Indexation de toutes les URLs et leur contenu
- ✅ Stockage des documents PDF dans la base de données
- ✅ Extraction et indexation de tous les liens (internes et externes)
- ✅ Recherche en texte intégral dans le contenu
- ✅ Métadonnées complètes (titres, descriptions, checksums)
- ✅ Cache HTTP pour éviter de re-télécharger les contenus inchangés
- ✅ Support des redirections internes
- ✅ Export des PDFs et des données

### Installation

#### Prérequis

- Python 3.11+
- Dépendances: `scrapy`, `python-dotenv`

```bash
pip install scrapy python-dotenv
# Ou avec uv
uv pip install scrapy python-dotenv
```

### Configuration

Créez un fichier `.env` dans le répertoire racine du projet:

```bash
# Chemin pour stocker le cache HTTP et la base de données
TARGET_PATH=./downloaded

# Chemin de la base de données SQLite (optionnel)
DB_PATH=./downloaded/crawl_index.db

# Domaines à exclure (séparés par des virgules)
EXCLUDE_DOMAINS=www7.fh-swf.de,static.bad.example
```

### Utilisation

#### Lancer le crawler

```bash
cd crawler
python crawl_to_sqlite.py
```

Le crawler va:
1. Créer/ouvrir la base de données SQLite
2. Crawler tout le site fh-swf.de
3. Indexer tous les contenus, liens et PDFs
4. Afficher les statistiques à la fin

#### Explorer la base de données

Utilisez l'utilitaire `query_db.py` pour explorer les données:

```bash
# Afficher les statistiques globales
python query_db.py stats

# Lister tous les PDFs
python query_db.py pdfs

# Lister avec limite personnalisée
python query_db.py pdfs --limit 100

# Rechercher dans le contenu des pages
python query_db.py search "informatique"
python query_db.py search "master" --limit 30

# Lister les domaines crawlés
python query_db.py domains

# Voir tous les liens d'une page
python query_db.py links "https://www.fh-swf.de/"

# Exporter la liste des PDFs en CSV
python query_db.py export-pdfs pdfs_list.csv

# Exporter un PDF spécifique
python query_db.py export-pdf "https://www.fh-swf.de/document.pdf" output.pdf
```

### Structure de la base de données

La base de données SQLite contient 5 tables principales:

#### 1. `urls`
Toutes les URLs crawlées avec métadonnées:
- url, domain, path, query_string
- status_code, content_type, content_length
- is_pdf, is_internal
- checksum, timestamps

#### 2. `page_content`
Contenu des pages HTML:
- html_content (BLOB)
- text_content (texte extrait)
- title, meta_description
- headers

#### 3. `links`
Relations entre les pages:
- source_url_id, target_url
- link_text, link_type (a, img, script, etc.)
- is_internal

#### 4. `pdf_documents`
Documents PDF complets:
- file_name, file_size
- content (BLOB)
- checksum, metadata

#### 5. `resources`
Autres ressources (images, CSS, JS):
- resource_type, file_name
- content (BLOB)
- checksum

### Exemples de requêtes SQL

Vous pouvez aussi requêter directement la base de données:

```bash
sqlite3 downloaded/crawl_index.db
```

```sql
-- Trouver tous les PDFs de plus de 1 MB
SELECT u.url, p.file_name, p.file_size 
FROM pdf_documents p
JOIN urls u ON p.url_id = u.id
WHERE p.file_size > 1048576
ORDER BY p.file_size DESC;

-- Trouver les pages avec le plus de liens
SELECT u.url, COUNT(*) as link_count
FROM links l
JOIN urls u ON l.source_url_id = u.id
GROUP BY u.url
ORDER BY link_count DESC
LIMIT 10;

-- Recherche en texte intégral
SELECT u.url, p.title
FROM page_content p
JOIN urls u ON p.url_id = u.id
WHERE p.text_content LIKE '%informatik%'
LIMIT 20;

-- Statistiques par domaine
SELECT domain, 
       COUNT(*) as total,
       SUM(CASE WHEN is_pdf = 1 THEN 1 ELSE 0 END) as pdfs
FROM urls
GROUP BY domain;
```

### Avantages du crawler SQLite

✅ **Recherche rapide**: Index sur les colonnes importantes  
✅ **Analyse de données**: Requêtes SQL complexes possibles  
✅ **Export facile**: CSV, JSON, ou extraction directe des PDFs  
✅ **Graphe de liens**: Analyse des relations entre pages  
✅ **Pas de doublons**: Vérification par checksum  
✅ **Incrémental**: Re-crawl uniquement les pages modifiées  
✅ **Portable**: Un seul fichier .db contient tout  

---

## Crawler de fichiers (Original)

### Description

Le crawler original `crawl_fhswf.py` sauvegarde tous les fichiers sur disque en préservant la structure des URLs.

### Prérequis

Python 3.11+
pip install scrapy python-dotenv

### Configuration .env

```bash
TARGET_PATH=/pfad/zum/speicherort
```

### Utilisation

```bash
python crawl_fhswf.py
```

Script (crawl_fhswf.py):

```Python
#!/usr/bin/env python3
"""
Crawl-Skript für fh-swf.de.
Speichert alle gecrawlten Ressourcen (HTML, PDFs, Bilder, ...) in einem
Zielverzeichnis, das über die Umgebungsvariable TARGET_PATH (in .env) gesetzt wird.
URLs, die "/intern/" enthalten, werden übersprungen.
"""

import os
import re
import hashlib
from urllib.parse import urlparse, unquote
from pathlib import Path

from dotenv import load_dotenv
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import TextResponse  # <- wichtig: für Typprüfung

# --- Laden der .env ---
load_dotenv()  # liest .env in Arbeitsverzeichnis
TARGET_PATH = os.getenv("TARGET_PATH", "").strip()
if not TARGET_PATH:
    TARGET_PATH = "./downloaded"  # Fallback
TARGET_PATH = os.path.abspath(TARGET_PATH)

# --- Utility-Funktionen ---


def sanitize_path_component(s: str) -> str:
    s = unquote(s)
    s = s.replace("\\", "/")
    s = re.sub(r"[^A-Za-z0-9\-\._\u00C0-\u017F]+", "_", s)
    s = s.strip("._")
    if not s:
        s = "_"
    return s


def url_to_local_path(url: str, base_dir: str) -> str:
    parsed = urlparse(url)
    netloc = sanitize_path_component(parsed.netloc)
    path = parsed.path or "/"

    comps = [sanitize_path_component(c) for c in path.split("/") if c != ""]
    if path.endswith("/") or (len(comps) == 0):
        comps.append("index.html")
    else:
        last = comps[-1]
        if not re.search(r"\.[A-Za-z0-9]{1,6}$", last):
            comps[-1] = last + ".html"

    if parsed.query:
        qhash = hashlib.sha1(parsed.query.encode("utf-8")).hexdigest()[:8]
        filename = comps[-1]
        m = re.match(r"^(.*?)(\.[A-Za-z0-9]{1,6})?$", filename)
        if m:
            base = m.group(1)
            ext = m.group(2) or ""
            comps[-1] = f"{base}_{qhash}{ext}"

    local_path = Path(base_dir) / netloc
    for c in comps:
        local_path /= c
    return str(local_path)


# --- Spider ---
class FHSWFSpider(scrapy.Spider):
    name = "fhswf"
    allowed_domains = ["fh-swf.de", "www.fh-swf.de"]
    start_urls = [
        "https://www.fh-swf.de/",
        "https://fh-swf.de/",
    ]

    custom_settings = {
        "LOG_LEVEL": "INFO",
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 0.2,
        "CONCURRENT_REQUESTS": 8,
        "USER_AGENT": "fhswf-crawler/1.0 (+https://www.fh-swf.de/)",
        "DOWNLOAD_TIMEOUT": 60,
    }

    def parse(self, response):
        url = response.url
        if "/intern/" in url:
            self.logger.debug("Skipping (intern): %s", url)
            return

        # Speichere Response-Body in Datei (binär)
        try:
            local_path = url_to_local_path(url, TARGET_PATH)
            local_file = Path(local_path)
            local_file.parent.mkdir(parents=True, exist_ok=True)
            with local_file.open("wb") as f:
                f.write(response.body)
            self.logger.info("Saved: %s -> %s", url, local_path)
        except Exception as e:
            self.logger.error("Failed to save %s: %s", url, e)

        # WICHTIG: Links nur aus TextResponse extrahieren (HTML/XML). Bei PDFs/Bildern führt
        # response.xpath sonst zu scrapy.exceptions.NotSupported.
        if not isinstance(response, TextResponse):
            # Keine Link-Extraktion für Binär-Inhalte (PDF, Bilder, etc.)
            return

        selectors = [
            "//a/@href",
            "//link/@href",
            "//img/@src",
            "//script/@src",
            "//iframe/@src",
            "//source/@src",
        ]
        seen = set()
        for sel in selectors:
            for href in response.xpath(sel).getall():
                if not href:
                    continue
                href = href.strip()
                if href.startswith(("mailto:", "tel:", "javascript:", "data:")):
                    continue
                abs_url = response.urljoin(href)
                if abs_url in seen:
                    continue
                seen.add(abs_url)

                if "/intern/" in abs_url:
                    continue

                parsed = urlparse(abs_url)
                if parsed.netloc.endswith("fh-swf.de"):
                    yield scrapy.Request(abs_url, callback=self.parse)


# --- Runner ---
def main():
    print("TARGET_PATH =", TARGET_PATH)
    print("Starting crawl of fh-swf.de ...")
    process = CrawlerProcess()
    process.crawl(FHSWFSpider)
    process.start()


if __name__ == "__main__":
    main()
```

Erläuterungen / Hinweise:

Das Skript speichert jede heruntergeladene Response unter TARGET_PATH//. Beispiele:
https://www.fh-swf.de/ → TARGET_PATH/www.fh-swf.de/index.html
https://www.fh-swf.de/images/logo.png → TARGET_PATH/www.fh-swf.de/images/logo.png
URLs mit "/intern/" werden nicht angefordert und nicht gespeichert.
Robots.txt wird standardmäßig beachtet (ROBOTSTXT_OBEY = True). Falls du das nicht möchtest, setze es auf False in custom_settings.
Die Speicherung erfolgt direkt im Spider (keine FilesPipeline). Das ist einfach und bewahrt die ursprüngliche Pfadstruktur.
Wenn du stattdessen nur bestimmte Dateitypen (z. B. PDFs, Bilder) mit Scrapy-Pipelines herunterladen willst, kann ich das Script anpassen und die FilesPipeline mit FILES_STORE verwenden.
Wenn du möchtest, kann ich:

das Verhalten so ändern, dass nur bestimmte Extensions gespeichert werden (z. B. pdf, docx, jpg),
oder die Original-URL-Pfade noch genauer erhalten (z. B. Query-Parameter in Ordnerstruktur),
oder ein Scrapy-Projekt mit Pipelines und Logging-Optionen anlegen.