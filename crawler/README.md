# FH-SWF Web Crawler

## Vue d'ensemble

Ce répertoire contient deux crawlers pour le site web fh-swf.de:

1. **crawl_fhswf.py** - Crawler de fichiers (sauvegarde sur disque)
2. **crawl_to_sqlite.py** - Crawler avec indexation SQLite + Neo4j (**NOUVEAU**)
3. **query_db.py** - Utilitaire pour explorer la base de données SQLite

## 🆕 Crawler SQLite + Neo4j (Recommandé)

Le nouveau crawler indexe tout le contenu du site dans SQLite pour les données structurées et optionnellement dans Neo4j pour la visualisation des relations entre pages.

### Caractéristiques

- ✅ **Sauvegarde triple**: Fichiers sur disque + SQLite + Neo4j (optionnel)
- ✅ Indexation de toutes les URLs et leur contenu
- ✅ Stockage des documents PDF (fichier + base de données)
- ✅ Sauvegarde de toutes les pages HTML sur disque
- ✅ Sauvegarde de toutes les images et ressources sur disque
- ✅ Extraction et indexation de tous les liens (internes et externes)
- ✅ **Neo4j**: Visualisation des relations entre pages sous forme de graphe
- ✅ Recherche en texte intégral dans le contenu
- ✅ Métadonnées complètes (titres, descriptions, checksums, chemins de fichiers)
- ✅ Cache HTTP pour éviter de re-télécharger les contenus inchangés
- ✅ Support des redirections internes
- ✅ Export des PDFs et des données

### Installation

#### Prérequis

- Python 3.11+
- Dépendances: `scrapy`, `python-dotenv`, `neo4j` (optionnel)
- Neo4j Server (optionnel, pour la visualisation des graphes)

```bash
pip install scrapy python-dotenv neo4j
# Ou avec uv
uv pip install scrapy python-dotenv neo4j
```

#### Installation de Neo4j (Optionnel)

**Option 1: Docker (Recommandé)**
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  -v $HOME/neo4j/data:/data \
  neo4j:latest
```

**Option 2: Neo4j Desktop**
Téléchargez depuis https://neo4j.com/download/

### Configuration

Créez un fichier `.env` dans le répertoire racine du projet:

```bash
# Chemin de base pour stocker les données, le cache HTTP et la base de données
TARGET_PATH=./downloaded

# Chemin pour sauvegarder les fichiers (HTML, PDF, images)
STORAGE_PATH=./downloaded/data

# Chemin de la base de données SQLite (optionnel, par défaut: TARGET_PATH/crawl_index.db)
DB_PATH=./downloaded/crawl_index.db

# Domaines à exclure du crawl (séparés par des virgules, supporte les wildcards)
EXCLUDE_DOMAINS=www7.fh-swf.de,static.bad.example

# === Configuration Neo4j (Optionnel) ===
# Activer Neo4j (true/false, 1/0, yes/no)
NEO4J_ENABLED=true

# URI de connexion Neo4j
NEO4J_URI=bolt://localhost:7687

# Identifiants Neo4j
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

**Explication des chemins:**
- `TARGET_PATH`: Répertoire racine pour tous les fichiers du crawler
- `STORAGE_PATH`: Où sauvegarder physiquement les fichiers HTML, PDF, images (préserve la structure des URLs)
- `DB_PATH`: Où sauvegarder la base de données SQLite avec l'index et les métadonnées
- `NEO4J_ENABLED`: Active/désactive la sauvegarde dans Neo4j
- `NEO4J_URI`: Adresse du serveur Neo4j (bolt:// pour connexion directe)
- `NEO4J_USER` / `NEO4J_PASSWORD`: Identifiants de connexion Neo4j

### Utilisation

#### Lancer le crawler

```bash
cd crawler
python crawl_to_sqlite.py
```

Le crawler va:
1. Créer/ouvrir la base de données SQLite
2. Se connecter à Neo4j (si activé)
3. Créer la structure de répertoires dans STORAGE_PATH
4. Crawler tout le site fh-swf.de
5. Sauvegarder chaque fichier sur disque (STORAGE_PATH)
6. Indexer tous les contenus, liens et PDFs dans SQLite
7. Sauvegarder les relations dans Neo4j (si activé)
8. Afficher les statistiques à la fin (SQLite + Neo4j)

**Système de sauvegarde double:**
- **Fichiers sur disque** (`STORAGE_PATH/`): Tous les fichiers sont sauvegardés physiquement
  - Préserve la structure des URLs: `www.fh-swf.de/path/to/page.html`
  - Fichiers directement utilisables sans base de données
  - Peut être servi par un serveur web statique
  
- **Base de données** (`DB_PATH`): Index et métadonnées
  - Contenu complet des pages (HTML + texte extrait)
  - Documents PDF en BLOB
  - Toutes les images et ressources en BLOB
  - Graphe complet des liens entre les pages
  - Recherche rapide en texte intégral
  - Métadonnées: checksums, dates, types MIME, chemins des fichiers

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
- file_path (chemin du fichier sauvegardé sur disque)
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
- file_path (chemin du fichier PDF sur disque)
- content (BLOB - contenu du PDF dans la base de données)
- checksum, metadata

#### 5. `resources`
Autres ressources (images, CSS, JS):
- resource_type, file_name
- file_path (chemin de la ressource sur disque)
- content (BLOB - contenu de la ressource dans la base de données)
- checksum

### Exemples de requêtes SQL

Vous pouvez aussi requêter directement la base de données:

```bash
sqlite3 downloaded/crawl_index.db
```

```sql
-- Trouver tous les PDFs de plus de 1 MB avec leurs chemins de fichiers
SELECT u.url, p.file_name, p.file_path, p.file_size 
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

-- Lister toutes les images sauvegardées avec leurs chemins
SELECT u.url, r.file_path, r.file_size
FROM resources r
JOIN urls u ON r.url_id = u.id
WHERE r.resource_type LIKE 'image/%'
ORDER BY r.file_size DESC;

-- Obtenir le chemin de fichier pour une URL spécifique
SELECT url, file_path 
FROM urls 
WHERE url = 'https://www.fh-swf.de/example.html';
```

### Utilisation de Neo4j (Optionnel)

Si vous avez activé Neo4j (`NEO4J_ENABLED=true`), les données sont également sauvegardées dans une base de données graphe pour une visualisation et une analyse des relations.

#### Structure du graphe Neo4j

**Nœuds:**
- `URL`: Représente toutes les URLs crawlées
  - Propriétés: url, domain, path, status_code, content_type, is_pdf, checksum, etc.
- `Page`: Contenu des pages HTML
  - Propriétés: title, meta_description, text_content
- `PDF`: Documents PDF
  - Propriétés: file_name, file_size, checksum, file_path
- `Resource`: Images, CSS, JS
  - Propriétés: resource_type, file_name, file_size

**Relations:**
- `LINKS_TO`: Lien d'une URL vers une autre
  - Propriétés: link_text, link_type (a, img, script), is_internal
- `REDIRECTS_TO`: Redirection HTTP
- `HAS_CONTENT`: URL → Page
- `HAS_PDF`: URL → PDF
- `HAS_RESOURCE`: URL → Resource

#### Accès à Neo4j Browser

Ouvrez votre navigateur à: http://localhost:7474

**Identifiants par défaut:**
- Username: `neo4j`
- Password: celui que vous avez configuré

#### Exemples de requêtes Cypher

```cypher
// Voir toutes les URLs crawlées (limité à 100)
MATCH (u:URL)
RETURN u
LIMIT 100;

// Trouver toutes les pages qui linkent vers une URL spécifique
MATCH (source:URL)-[r:LINKS_TO]->(target:URL {url: 'https://www.fh-swf.de/'})
RETURN source.url, r.link_text, r.link_type;

// Visualiser le graphe de navigation autour de la page d'accueil
MATCH path = (u:URL {url: 'https://www.fh-swf.de/'})-[:LINKS_TO*1..2]-(related:URL)
RETURN path
LIMIT 50;

// Trouver les pages les plus liées (PageRank simple)
MATCH (u:URL)<-[:LINKS_TO]-(source)
RETURN u.url, u.domain, count(source) as incoming_links
ORDER BY incoming_links DESC
LIMIT 20;

// Trouver tous les PDFs et leurs tailles
MATCH (u:URL)-[:HAS_PDF]->(pdf:PDF)
RETURN u.url, pdf.file_name, pdf.file_size, pdf.file_path
ORDER BY pdf.file_size DESC;

// Rechercher des pages par titre
MATCH (u:URL)-[:HAS_CONTENT]->(p:Page)
WHERE p.title CONTAINS 'Informatik'
RETURN u.url, p.title;

// Analyser les redirections
MATCH path = (source:URL)-[:REDIRECTS_TO*]->(target:URL)
RETURN path;

// Trouver les pages orphelines (aucun lien entrant interne)
MATCH (u:URL)
WHERE NOT exists((u)<-[:LINKS_TO]-(:URL))
  AND u.is_internal = true
RETURN u.url, u.title
LIMIT 20;

// Statistiques par domaine
MATCH (u:URL)
RETURN u.domain, 
       count(*) as total_urls,
       sum(CASE WHEN u.is_pdf THEN 1 ELSE 0 END) as pdf_count
ORDER BY total_urls DESC;

// Trouver le chemin le plus court entre deux pages
MATCH path = shortestPath(
  (start:URL {url: 'https://www.fh-swf.de/'})-[:LINKS_TO*]->
  (end:URL {url: 'https://www.fh-swf.de/de/studieren/studiengaenge'})
)
RETURN path;
```

#### Avantages de Neo4j

✅ **Visualisation graphique**: Voir les relations entre pages  
✅ **Requêtes de graphe**: Trouver des chemins, des communautés  
✅ **PageRank**: Identifier les pages importantes  
✅ **Détection de liens brisés**: Pages sans liens entrants  
✅ **Analyse de la navigation**: Comment les utilisateurs pourraient naviguer  

### Avantages du crawler SQLite + Neo4j

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