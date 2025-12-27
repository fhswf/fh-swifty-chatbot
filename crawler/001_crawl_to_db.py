#!/usr/bin/env python3
"""
Crawler pour fh-swf.de qui indexe tout dans une base de données SQLite.
- Indexe tous les liens et documents PDF
- Sauvegarde le contenu, les métadonnées et les relations
- Utilise SQLite pour un accès rapide et des requêtes structurées
"""

import os
import re
import hashlib
import sqlite3
from urllib.parse import urlparse, unquote
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import TextResponse, Response
from neo4j import GraphDatabase

from html_to_markdown import convert_to_markdown
import pymupdf4llm

# --- Configuration ---
load_dotenv()
TARGET_PATH = os.getenv("TARGET_PATH", "").strip() or "./downloaded_v4"
TARGET_PATH = os.path.abspath(TARGET_PATH)

DB_PATH = os.getenv("DB_PATH", os.path.join(TARGET_PATH, "crawl_index.db"))
DB_PATH = os.path.abspath(DB_PATH)

STORAGE_PATH = os.getenv("STORAGE_PATH", os.path.join(TARGET_PATH, "data"))
STORAGE_PATH = os.path.abspath(STORAGE_PATH)

EXCLUDE_DOMAINS = os.getenv("EXCLUDE_DOMAINS", "").strip()
EXCLUDE_DOMAINS_LIST = [d.strip() for d in EXCLUDE_DOMAINS.split(",") if d.strip()]

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7689")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")
NEO4J_ENABLED = os.getenv("NEO4J_ENABLED", "true").lower() in ["true", "1", "yes"]

# --- Database Schema ---
class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Initialise la structure de la base de données"""
        # Créer le répertoire parent s'il n'existe pas
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"✓ Répertoire créé: {db_dir}")
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Table pour les URLs crawlées
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                domain TEXT NOT NULL,
                path TEXT,
                query_string TEXT,
                status_code INTEGER,
                content_type TEXT,
                content_length INTEGER,
                file_path TEXT,
                last_crawled TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_pdf BOOLEAN DEFAULT 0,
                is_internal BOOLEAN DEFAULT 1,
                checksum TEXT,
                UNIQUE(url)
            )
        """)
        
        # Table pour le contenu des pages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS page_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_id INTEGER NOT NULL,
                text_content TEXT,
                markdown_content TEXT,
                title TEXT,
                meta_description TEXT,
                headers TEXT,
                FOREIGN KEY (url_id) REFERENCES urls(id) ON DELETE CASCADE
            )
        """)
        
        # Table pour les liens entre pages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url_id INTEGER NOT NULL,
                target_url TEXT NOT NULL,
                target_url_id INTEGER,
                link_text TEXT,
                link_type TEXT,
                is_internal BOOLEAN DEFAULT 0,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_url_id) REFERENCES urls(id) ON DELETE CASCADE,
                FOREIGN KEY (target_url_id) REFERENCES urls(id) ON DELETE SET NULL
            )
        """)
        
        # Table pour les documents PDF
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pdf_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_id INTEGER NOT NULL,
                file_name TEXT,
                file_path TEXT,
                file_size INTEGER,
                markdown_content TEXT,
                checksum TEXT,
                metadata TEXT,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (url_id) REFERENCES urls(id) ON DELETE CASCADE
            )
        """)
        
        # Table pour les images et autres ressources
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_id INTEGER NOT NULL,
                resource_type TEXT,
                file_name TEXT,
                file_path TEXT,
                file_size INTEGER,
                checksum TEXT,
                FOREIGN KEY (url_id) REFERENCES urls(id) ON DELETE CASCADE
            )
        """)
        
        # Index pour améliorer les performances
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_urls_domain ON urls(domain)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_urls_is_pdf ON urls(is_pdf)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_urls_last_crawled ON urls(last_crawled)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_links_source ON links(source_url_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_links_target ON links(target_url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_links_internal ON links(is_internal)")
        
        self.conn.commit()
        print(f"✓ Base de données initialisée: {self.db_path}")
    
    def insert_or_update_url(self, url: str, status_code: int, content_type: str,
                            content_length: int, is_pdf: bool, is_internal: bool,
                            checksum: str, file_path: str = None) -> int:
        """Insère ou met à jour une URL et retourne son ID"""
        cursor = self.conn.cursor()
        parsed = urlparse(url)
        
        cursor.execute("""
            INSERT INTO urls (url, domain, path, query_string, status_code, 
                            content_type, content_length, is_pdf, is_internal, checksum, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                status_code = excluded.status_code,
                content_type = excluded.content_type,
                content_length = excluded.content_length,
                last_crawled = CURRENT_TIMESTAMP,
                checksum = excluded.checksum,
                file_path = excluded.file_path
            RETURNING id
        """, (url, parsed.netloc, parsed.path, parsed.query, status_code,
              content_type, content_length, is_pdf, is_internal, checksum, file_path))
        
        result = cursor.fetchone()
        url_id = result[0]
        self.conn.commit()
        return url_id
    
    def insert_page_content(self, url_id: int, text_content: str, markdown_content: str, 
                           title: str, meta_description: str, headers: str):
        """Insère le contenu d'une page"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO page_content 
            (url_id, text_content, markdown_content, title, meta_description, headers)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (url_id, text_content, markdown_content, title, meta_description, headers))
        self.conn.commit()
    
    def insert_link(self, source_url_id: int, target_url: str, link_text: str,
                   link_type: str, is_internal: bool):
        """Insère un lien entre deux pages"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO links 
            (source_url_id, target_url, link_text, link_type, is_internal)
            VALUES (?, ?, ?, ?, ?)
        """, (source_url_id, target_url, link_text or "", link_type, is_internal))
        self.conn.commit()
    
    def insert_pdf(self, url_id: int, file_name: str, markdown_content: str, 
                   file_size: int, checksum: str, file_path: str = None):
        """Insère un document PDF"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO pdf_documents 
            (url_id, file_name, markdown_content, file_size, checksum, file_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (url_id, file_name, markdown_content, file_size, checksum, file_path))
        self.conn.commit()
    
    def insert_resource(self, url_id: int, resource_type: str, file_name: str,
                        file_size: int, checksum: str, file_path: str = None):
        """Insère une ressource (image, CSS, JS, etc.)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO resources 
            (url_id, resource_type, file_name, file_size, checksum, file_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (url_id, resource_type, file_name, file_size, checksum, file_path))
        self.conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du crawl"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total URLs
        cursor.execute("SELECT COUNT(*) FROM urls")
        stats['total_urls'] = cursor.fetchone()[0]
        
        # Total PDFs
        cursor.execute("SELECT COUNT(*) FROM urls WHERE is_pdf = 1")
        stats['total_pdfs'] = cursor.fetchone()[0]
        
        # Total Links
        cursor.execute("SELECT COUNT(*) FROM links")
        stats['total_links'] = cursor.fetchone()[0]
        
        # Pages HTML
        cursor.execute("SELECT COUNT(*) FROM page_content")
        stats['total_pages'] = cursor.fetchone()[0]
        
        # Ressources
        cursor.execute("SELECT COUNT(*) FROM resources")
        stats['total_resources'] = cursor.fetchone()[0]
        
        return stats
    
    def close(self):
        """Ferme la connexion à la base de données"""
        if self.conn:
            self.conn.close()

# --- Neo4j Manager ---
class Neo4jManager:
    """Gestionnaire de connexion et opérations Neo4j"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # Vérifier la connexion
            self.driver.verify_connectivity()
            self.init_constraints()
            print(f"✓ Connexion à Neo4j établie: {uri}")
        except Exception as e:
            print(f"⚠️  Erreur de connexion à Neo4j: {e}")
            print("   Le crawler continuera sans Neo4j.")
            self.driver = None
    
    def init_constraints(self):
        """Crée les contraintes et index dans Neo4j"""
        if not self.driver:
            return
        
        with self.driver.session() as session:
            # Contraintes d'unicité
            constraints = [
                "CREATE CONSTRAINT url_unique IF NOT EXISTS FOR (u:URL) REQUIRE u.url IS UNIQUE",
                "CREATE CONSTRAINT page_unique IF NOT EXISTS FOR (p:Page) REQUIRE p.url IS UNIQUE",
                "CREATE CONSTRAINT pdf_unique IF NOT EXISTS FOR (p:PDF) REQUIRE p.url IS UNIQUE",
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception:
                    # Contrainte peut déjà exister
                    pass
            
            # Index pour améliorer les performances
            indexes = [
                "CREATE INDEX url_domain IF NOT EXISTS FOR (u:URL) ON (u.domain)",
                "CREATE INDEX url_checksum IF NOT EXISTS FOR (u:URL) ON (u.checksum)",
                "CREATE INDEX page_title IF NOT EXISTS FOR (p:Page) ON (p.title)",
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                except Exception:
                    pass
    
    def create_url_node(self, url: str, status_code: int, content_type: str,
                       content_length: int, is_pdf: bool, is_internal: bool,
                       checksum: str, file_path: str = None) -> bool:
        """Crée ou met à jour un nœud URL"""
        if not self.driver:
            return False
        
        try:
            parsed = urlparse(url)
            
            with self.driver.session() as session:
                session.run("""
                    MERGE (u:URL {url: $url})
                    SET u.domain = $domain,
                        u.path = $path,
                        u.query_string = $query_string,
                        u.status_code = $status_code,
                        u.content_type = $content_type,
                        u.content_length = $content_length,
                        u.is_pdf = $is_pdf,
                        u.is_internal = $is_internal,
                        u.checksum = $checksum,
                        u.file_path = $file_path,
                        u.last_crawled = datetime(),
                        u.first_seen = coalesce(u.first_seen, datetime())
                """, {
                    'url': url,
                    'domain': parsed.netloc,
                    'path': parsed.path,
                    'query_string': parsed.query,
                    'status_code': status_code,
                    'content_type': content_type,
                    'content_length': content_length,
                    'is_pdf': is_pdf,
                    'is_internal': is_internal,
                    'checksum': checksum,
                    'file_path': file_path
                })
            return True
        except Exception as e:
            print(f"Erreur Neo4j create_url_node: {e}")
            return False
    
    def create_page_content(self, url: str, text_content: str, markdown_content: str,
                            title: str, meta_description: str):
        """Crée un nœud Page et le lie à l'URL"""
        if not self.driver:
            return
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (u:URL {url: $url})
                    MERGE (p:Page {url: $url})
                    SET p.title = $title,
                        p.meta_description = $meta_description,
                        p.text_content = $text_content,
                        p.markdown_content = $markdown_content,
                        p.updated_at = datetime()
                    MERGE (u)-[:HAS_CONTENT]->(p)
                """, {
                    'url': url,
                    'title': title,
                    'meta_description': meta_description,
                    'text_content': text_content,
                    'markdown_content': markdown_content
                })
        except Exception as e:
            print(f"Erreur Neo4j create_page_content: {e}")
    
    def create_link(self, source_url: str, target_url: str, link_text: str,
                   link_type: str, is_internal: bool):
        """Crée une relation LINKS_TO entre deux URLs avec les propriétés link_to_redirect et link_to_pdf"""
        if not self.driver:
            return
        
        try:
            with self.driver.session() as session:
                # Récupérer les propriétés du nœud target s'il existe
                target_info = session.run("""
                    MATCH (target:URL {url: $target_url})
                    RETURN target.status_code as status_code, 
                           target.content_type as content_type
                """, {'target_url': target_url}).single()
                
                # Déterminer link_to_redirect (true si status_code = 302)
                link_to_redirect = False
                if target_info and target_info.get('status_code') == 302:
                    link_to_redirect = True
                
                # Déterminer link_to_pdf (true si content_type contient application/pdf)
                link_to_pdf = False
                if target_info and target_info.get('content_type'):
                    content_type = target_info.get('content_type', '').lower()
                    if 'application/pdf' in content_type:
                        link_to_pdf = True
                
                # Créer les nœuds URL si nécessaire et la relation
                session.run("""
                    MERGE (source:URL {url: $source_url})
                    MERGE (target:URL {url: $target_url})
                    ON CREATE SET target.is_internal = $is_internal,
                                  target.first_seen = datetime()
                    MERGE (source)-[r:LINKS_TO]->(target)
                    SET r.link_text = $link_text,
                        r.link_type = $link_type,
                        r.is_internal = $is_internal,
                        r.link_to_redirect = $link_to_redirect,
                        r.link_to_pdf = $link_to_pdf,
                        r.discovered_at = coalesce(r.discovered_at, datetime())
                """, {
                    'source_url': source_url,
                    'target_url': target_url,
                    'link_text': link_text or "",
                    'link_type': link_type,
                    'is_internal': is_internal,
                    'link_to_redirect': link_to_redirect,
                    'link_to_pdf': link_to_pdf
                })
        except Exception as e:
            print(f"Erreur Neo4j create_link: {e}")
    
    def create_pdf_node(self, url: str, file_name: str, markdown_content: str, file_size: int, 
                       checksum: str, file_path: str = None):
        """Crée un nœud PDF et le lie à l'URL"""
        if not self.driver:
            return
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (u:URL {url: $url})
                    MERGE (pdf:PDF {url: $url})
                    SET pdf.file_name = $file_name,
                        pdf.markdown_content = $markdown_content,
                        pdf.file_size = $file_size,
                        pdf.checksum = $checksum,
                        pdf.file_path = $file_path,
                        pdf.indexed_at = datetime()
                    MERGE (u)-[:HAS_PDF]->(pdf)
                """, {
                    'url': url,
                    'file_name': file_name,
                    'markdown_content': markdown_content,
                    'file_size': file_size,
                    'checksum': checksum,
                    'file_path': file_path
                })
        except Exception as e:
            print(f"Erreur Neo4j create_pdf_node: {e}")
    
    def create_resource_node(self, url: str, resource_type: str, file_name: str,
                            file_size: int, checksum: str, file_path: str = None):
        """Crée un nœud Resource et le lie à l'URL"""
        if not self.driver:
            return
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (u:URL {url: $url})
                    MERGE (r:Resource {url: $url})
                    SET r.resource_type = $resource_type,
                        r.file_name = $file_name,
                        r.file_size = $file_size,
                        r.checksum = $checksum,
                        r.file_path = $file_path,
                        r.indexed_at = datetime()
                    MERGE (u)-[:HAS_RESOURCE]->(r)
                """, {
                    'url': url,
                    'resource_type': resource_type,
                    'file_name': file_name,
                    'file_size': file_size,
                    'checksum': checksum,
                    'file_path': file_path
                })
        except Exception as e:
            print(f"Erreur Neo4j create_resource_node: {e}")
    
    def create_redirect(self, source_url: str, target_url: str):
        """Crée une relation REDIRECTS_TO"""
        if not self.driver:
            return
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (source:URL {url: $source_url})
                    MERGE (target:URL {url: $target_url})
                    MERGE (source)-[r:REDIRECTS_TO]->(target)
                    SET r.discovered_at = coalesce(r.discovered_at, datetime())
                """, {
                    'source_url': source_url,
                    'target_url': target_url
                })
        except Exception as e:
            print(f"Erreur Neo4j create_redirect: {e}")
    
    def create_page_has_pdf(self, page_url: str, pdf_url: str, link_text: str, link_type: str):
        """
        Crée une relation PAGE_HAS_PDF entre un nœud Page et un nœud PDF.
        Crée le nœud PDF s'il n'existe pas encore.
        """
        if not self.driver:
            return
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (page:Page {url: $page_url})
                    MERGE (pdf:PDF {url: $pdf_url})
                    MERGE (page)-[r:PAGE_HAS_PDF]->(pdf)
                    SET r.link_text = $link_text,
                        r.link_type = $link_type
                """, {
                    'page_url': page_url,
                    'pdf_url': pdf_url,
                    'link_text': link_text or "",
                    'link_type': link_type
                })
        except Exception as e:
            print(f"Erreur Neo4j create_page_has_pdf: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques depuis Neo4j"""
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    RETURN 
                        count{(:URL)} as total_urls,
                        count{(:Page)} as total_pages,
                        count{(:PDF)} as total_pdfs,
                        count{(:Resource)} as total_resources,
                        count{()-[:LINKS_TO]->()} as total_links
                """)
                record = result.single()
                return {
                    'total_urls': record['total_urls'],
                    'total_pages': record['total_pages'],
                    'total_pdfs': record['total_pdfs'],
                    'total_resources': record['total_resources'],
                    'total_links': record['total_links']
                }
        except Exception as e:
            print(f"Erreur Neo4j get_stats: {e}")
            return {}
    
    def close(self):
        """Ferme la connexion à Neo4j"""
        if self.driver:
            self.driver.close()
            print("✓ Connexion Neo4j fermée")

# --- Utility Functions ---
def sanitize_path_component(s: str) -> str:
    """Nettoie un composant de chemin pour le système de fichiers"""
    s = unquote(s or "")
    s = s.replace("\\", "/")
    s = re.sub(r"[^A-Za-z0-9\-\._\u00C0-\u017F]+", "_", s)
    s = s.strip("._")
    return s or "_"

def url_to_local_path(url: str, base_dir: str) -> str:
    """Convertit une URL en chemin de fichier local"""
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
        base = m.group(1) if m else filename
        ext = m.group(2) if m and m.group(2) else ""
        comps[-1] = f"{base}_{qhash}{ext}"
    
    local_path = Path(base_dir) / netloc
    for c in comps:
        local_path /= c
    return str(local_path)

def save_file_to_disk(url: str, content: bytes, base_dir: str) -> Optional[str]:
    """Sauvegarde un fichier sur le disque et retourne le chemin"""
    try:
        local_path = url_to_local_path(url, base_dir)
        local_file = Path(local_path)
        local_file.parent.mkdir(parents=True, exist_ok=True)
        with local_file.open("wb") as f:
            f.write(content)
        return local_path
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de {url}: {e}")
        return None

def compute_checksum(content: bytes) -> str:
    """Calcule le hash SHA256 du contenu"""
    return hashlib.sha256(content).hexdigest()

def extract_text_content(response: TextResponse) -> str:
    """Extrait le texte visible d'une page HTML"""
    # Supprime les scripts et styles
    text_parts = response.xpath("""
        //body//text()[
            not(ancestor::script) and 
            not(ancestor::style) and 
            not(ancestor::noscript)
        ]
    """).getall()
    text = "\n".join(t.strip() for t in text_parts if t.strip())
    return re.sub(r'\s+', ' ', text)

def is_internal_url(url: str, base_domain: str = "fh-swf.de") -> bool:
    """Vérifie si l'URL est interne au domaine"""
    parsed = urlparse(url)
    return parsed.netloc.endswith(base_domain) if parsed.netloc else True

def is_blacklisted_host(hostname: str, blacklist: list) -> bool:
    """Vérifie si l'hôte est dans la blacklist"""
    if not hostname:
        return False
    import fnmatch
    for pat in blacklist:
        if fnmatch.fnmatch(hostname, pat):
            return True
    return False

def html_to_markdown(file_path: str) -> str:
    try:
        content = Path(file_path).read_text()
        markdown_content = convert_to_markdown(content, preprocess_html=True, preprocessing_preset='aggressive')
    except Exception as e:
        markdown_content = f"Error converting HTML to markdown: {e}"
    return markdown_content

def extract_link_text(response: TextResponse, link_element) -> Optional[str]:
    """
    Extrait le texte d'un lien de manière robuste.
    Essaie plusieurs stratégies:
    1. Texte dans span.link__text ou span[class*="link__text"]
    2. Texte direct du lien (//a/text())
    3. Attribut title ou aria-label
    4. Texte de tous les descendants (string())
    """
    if not link_element:
        return None
    
    # Stratégie 1: Chercher dans span.link__text ou span avec classe contenant "link__text"
    link_text = link_element.xpath('.//span[contains(@class, "link__text")]//text()').get()
    if link_text and link_text.strip():
        return link_text.strip()
    
    # Stratégie 2: Texte direct du lien
    link_text = link_element.xpath('.//text()').get()
    if link_text and link_text.strip():
        return link_text.strip()
    
    # Stratégie 3: Utiliser string() pour obtenir tout le texte des descendants
    link_text = link_element.xpath('string(.)').get()
    if link_text and link_text.strip():
        return link_text.strip()
    
    # Stratégie 4: Attributs title ou aria-label
    link_text = link_element.xpath('./@title').get()
    if link_text and link_text.strip():
        return link_text.strip()
    
    link_text = link_element.xpath('./@aria-label').get()
    if link_text and link_text.strip():
        return link_text.strip()
    
    return None

# --- Spider ---
class FHSWFSQLiteSpider(scrapy.Spider):
    name = "fhswf_sqlite"
    allowed_domains = ["fh-swf.de", "www.fh-swf.de"]
    start_urls = [
        "https://www.fh-swf.de/",
        "https://fh-swf.de/",
    ]
    
    handle_httpstatus_list = [301, 302, 303, 307, 308]
    
    custom_settings = {
        "LOG_LEVEL": "INFO",
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 0.2,
        "CONCURRENT_REQUESTS": 8,
        "USER_AGENT": "fhswf-crawler/2.0 (+https://www.fh-swf.de/)",
        "DOWNLOAD_TIMEOUT": 60,
        "REDIRECT_ENABLED": False,
        
        # HTTP Cache pour éviter de re-télécharger
        "HTTPCACHE_ENABLED": True,
        "HTTPCACHE_DIR": os.path.join(TARGET_PATH, "httpcache"),
        "HTTPCACHE_POLICY": "scrapy.extensions.httpcache.RFC2616Policy",
        "HTTPCACHE_STORAGE": "scrapy.extensions.httpcache.FilesystemCacheStorage",
        
        "JOBDIR": os.path.join(TARGET_PATH, "jobstate"),
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = DatabaseManager(DB_PATH)
        
        # Initialiser Neo4j si activé
        self.neo4j = None
        if NEO4J_ENABLED:
            self.neo4j = Neo4jManager(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        
        self.crawled_count = 0
        self.pdf_count = 0
    
    def _is_internal_and_allowed(self, url: str) -> bool:
        """Vérifie si l'URL est interne et autorisée"""
        parsed = urlparse(url)
        host = parsed.hostname or ""
        
        if not host.endswith("fh-swf.de"):
            return False
        
        if is_blacklisted_host(host, EXCLUDE_DOMAINS_LIST):
            self.logger.debug("Excluded by blacklist: %s", host)
            return False
        
        return True
    
    def parse(self, response: Response):
        """Parse la réponse et stocke dans la base de données"""
        url = response.url
        
        # Skip /intern/
        if "/intern/" in url:
            self.logger.debug("Skipping (intern): %s", url)
            return
        
        # Sauvegarder le fichier sur le disque
        file_path = save_file_to_disk(url, response.body, STORAGE_PATH)
        
        # Calculer le checksum
        checksum = compute_checksum(response.body)
        
        # Déterminer le type de contenu
        content_type = response.headers.get('Content-Type', b'').decode('utf-8', 'ignore')
        is_pdf = 'application/pdf' in content_type.lower() or url.lower().endswith('.pdf')
        is_html = 'text/html' in content_type.lower() or url.lower().endswith('.html') or url.lower().endswith('.php')
        
        # Insérer/mettre à jour l'URL dans SQLite
        url_id = self.db.insert_or_update_url(
            url=url,
            status_code=response.status,
            content_type=content_type,
            content_length=len(response.body),
            is_pdf=is_pdf,
            is_internal=self._is_internal_and_allowed(url),
            checksum=checksum,
            file_path=file_path
        )
        
        # Insérer/mettre à jour l'URL dans Neo4j
        if self.neo4j:
            self.neo4j.create_url_node(
                url=url,
                status_code=response.status,
                content_type=content_type,
                content_length=len(response.body),
                is_pdf=is_pdf,
                is_internal=self._is_internal_and_allowed(url),
                checksum=checksum,
                file_path=file_path
            )
        
        self.crawled_count += 1
        self.logger.info(f"[{self.crawled_count}] Crawled: {url} (ID: {url_id})")
        
        # Gérer les redirections
        if 300 <= response.status < 400:
            loc = response.headers.get("Location") or response.headers.get(b"location")
            if loc:
                try:
                    loc = loc.decode() if isinstance(loc, bytes) else str(loc)
                except Exception:
                    loc = str(loc)
                target = response.urljoin(loc)
                
                # Enregistrer le lien de redirection dans SQLite
                self.db.insert_link(
                    source_url_id=url_id,
                    target_url=target,
                    link_text="[redirect]",
                    link_type="redirect",
                    is_internal=self._is_internal_and_allowed(target)
                )
                
                # Enregistrer la redirection dans Neo4j
                if self.neo4j:
                    self.neo4j.create_redirect(source_url=url, target_url=target)
                
                if self._is_internal_and_allowed(target):
                    self.logger.info("Following redirect: %s -> %s", url, target)
                    yield scrapy.Request(target, callback=self.parse)
            return
        
        # Traiter les PDFs
        if is_pdf:
            self.pdf_count += 1
            file_name = os.path.basename(urlparse(url).path) or f"document_{url_id}.pdf"

            try:
                markdown_content = pymupdf4llm.to_markdown(file_path)
            except Exception as e:
                markdown_content = f"Error converting PDF to markdown: {e}"
                self.logger.error(f"Error converting PDF to markdown: {e}")

            # SQLite
            self.db.insert_pdf(
                url_id=url_id,
                file_name=file_name,
                markdown_content=markdown_content,
                file_size=len(response.body),
                checksum=checksum,
                file_path=file_path
            )
            
            # Neo4j
            if self.neo4j:
                self.neo4j.create_pdf_node(
                    url=url,
                    file_name=file_name,
                    markdown_content=markdown_content,
                    file_size=len(response.body),
                    checksum=checksum,
                    file_path=file_path
                )
            
            self.logger.info(f"✓ Saved PDF: {file_name} ({len(response.body)} bytes) -> {file_path}")
            return
        
        # Traiter les pages HTML
        if is_html:
            # Extraire les métadonnées
            title = response.xpath('//title/text()').get() or ""
            meta_desc = response.xpath('//meta[@name="description"]/@content').get() or ""
            text_content = extract_text_content(response)
            headers_str = str(dict(response.headers))

            print("=" * 70)
            markdown_content = html_to_markdown(file_path)
            
            # Sauvegarder le contenu de la page dans SQLite
            self.db.insert_page_content(
                url_id=url_id,
                text_content=text_content,
                markdown_content=markdown_content,
                title=title.strip(),
                meta_description=meta_desc.strip(),
                headers=headers_str
            )
            
            # Sauvegarder le contenu de la page dans Neo4j
            if self.neo4j:
                self.neo4j.create_page_content(
                    url=url,
                    text_content=text_content,
                    markdown_content=markdown_content,
                    title=title.strip(),
                    meta_description=meta_desc.strip()
                )
            
            # Extraire et enregistrer tous les liens
            selectors = {
                "a": ("//a", "@href"),  # Pour les liens <a>, on récupère l'élément complet
                "link": ("//link", "@href"),
                "img": ("//img", "@src"),
                "script": ("//script", "@src"),
                "iframe": ("//iframe", "@src"),
                "source": ("//source", "@src"),
            }
            
            seen_links = set()
            for link_type, (element_xpath, href_attr) in selectors.items():
                elements = response.xpath(element_xpath)
                
                for element in elements:
                    href = element.xpath(f'./{href_attr}').get()
                    if not href or href.strip() == "":
                        continue
                    
                    href = href.strip()
                    
                    # Skip protocoles spéciaux
                    if href.startswith(("mailto:", "tel:", "javascript:", "data:")):
                        continue
                    
                    # Construire l'URL absolue
                    abs_url = response.urljoin(href)
                    
                    # Skip si déjà vu dans cette page
                    if abs_url in seen_links:
                        continue
                    seen_links.add(abs_url)
                    
                    # Skip /intern/
                    if "/intern/" in abs_url:
                        continue
                    
                    # Extraire le texte du lien de manière robuste
                    if link_type == "a":
                        link_text = extract_link_text(response, element)
                    elif link_type == "img":
                        link_text = element.xpath('./@alt').get()
                    else:
                        link_text = None
                    
                    # Enregistrer le lien dans SQLite
                    is_internal = self._is_internal_and_allowed(abs_url)
                    self.db.insert_link(
                        source_url_id=url_id,
                        target_url=abs_url,
                        link_text=link_text.strip() if link_text else None,
                        link_type=link_type,
                        is_internal=is_internal
                    )
                    
                    # Enregistrer le lien dans Neo4j
                    if self.neo4j:
                        self.neo4j.create_link(
                            source_url=url,
                            target_url=abs_url,
                            link_text=link_text.strip() if link_text else None,
                            link_type=link_type,
                            is_internal=is_internal
                        )
                        
                        # Si le lien pointe vers un PDF, créer la relation PAGE_HAS_PDF
                        # Vérifier d'abord par l'extension, puis par le nœud target s'il existe
                        is_pdf_link = abs_url.lower().endswith('.pdf')
                        if not is_pdf_link:
                            # Vérifier si le nœud target existe et est un PDF
                            try:
                                with self.neo4j.driver.session() as session:
                                    result = session.run("""
                                        MATCH (target:URL {url: $target_url})
                                        RETURN target.is_pdf as is_pdf,
                                               target.content_type as content_type
                                    """, {'target_url': abs_url}).single()
                                    if result:
                                        is_pdf_link = (result.get('is_pdf') is True) or \
                                                     ('application/pdf' in (result.get('content_type') or '').lower())
                            except Exception:
                                pass
                        
                        if is_pdf_link:
                            self.neo4j.create_page_has_pdf(
                                page_url=url,
                                pdf_url=abs_url,
                                link_text=link_text.strip() if link_text else None,
                                link_type=link_type
                            )
                    
                    # Suivre les liens internes
                    if is_internal:
                        yield scrapy.Request(abs_url, callback=self.parse)
                    else:
                        self.logger.debug("External link: %s", abs_url)
        
        else:
            # Autres ressources (images, CSS, JS, etc.)
            resource_type = content_type.split(';')[0].strip() if content_type else 'unknown'
            file_name = os.path.basename(urlparse(url).path) or f"resource_{url_id}"
            
            # SQLite
            self.db.insert_resource(
                url_id=url_id,
                resource_type=resource_type,
                file_name=file_name,
                file_size=len(response.body),
                checksum=checksum,
                file_path=file_path
            )
            
            # Neo4j
            if self.neo4j:
                self.neo4j.create_resource_node(
                    url=url,
                    resource_type=resource_type,
                    file_name=file_name,
                    file_size=len(response.body),
                    checksum=checksum,
                    file_path=file_path
                )
            
            self.logger.debug(f"✓ Saved resource: {file_name} -> {file_path}")
    
    def closed(self, reason):
        """Appelé quand le spider se termine"""
        stats = self.db.get_stats()
        self.logger.info("=" * 60)
        self.logger.info("Crawl terminé!")
        self.logger.info(f"Raison: {reason}")
        self.logger.info("-" * 60)
        self.logger.info("SQLite Stats:")
        self.logger.info(f"  URLs totales:     {stats['total_urls']}")
        self.logger.info(f"  Pages HTML:       {stats['total_pages']}")
        self.logger.info(f"  Documents PDF:    {stats['total_pdfs']}")
        self.logger.info(f"  Liens totaux:     {stats['total_links']}")
        self.logger.info(f"  Ressources:       {stats['total_resources']}")
        self.logger.info(f"  Base de données: {DB_PATH}")
        
        # Stats Neo4j
        if self.neo4j:
            neo4j_stats = self.neo4j.get_stats()
            if neo4j_stats:
                self.logger.info("-" * 60)
                self.logger.info("Neo4j Stats:")
                self.logger.info(f"  URLs totales:     {neo4j_stats.get('total_urls', 0)}")
                self.logger.info(f"  Pages HTML:       {neo4j_stats.get('total_pages', 0)}")
                self.logger.info(f"  Documents PDF:    {neo4j_stats.get('total_pdfs', 0)}")
                self.logger.info(f"  Liens totaux:     {neo4j_stats.get('total_links', 0)}")
                self.logger.info(f"  Ressources:       {neo4j_stats.get('total_resources', 0)}")
        
        self.logger.info("=" * 60)
        
        self.db.close()
        if self.neo4j:
            self.neo4j.close()

# --- Runner ---
def main():
    print("=" * 70)
    print("FH-SWF Crawler avec indexation SQLite + Neo4j + Sauvegarde fichiers")
    print("=" * 70)
    print(f"TARGET_PATH:  {TARGET_PATH}")
    print(f"STORAGE_PATH: {STORAGE_PATH}")
    print(f"DB_PATH:      {DB_PATH}")
    print(f"Exclusions:   {EXCLUDE_DOMAINS_LIST or 'Aucune'}")
    print("-" * 70)
    print(f"Neo4j:        {'✓ ACTIVÉ' if NEO4J_ENABLED else '✗ DÉSACTIVÉ'}")
    if NEO4J_ENABLED:
        print(f"Neo4j URI:    {NEO4J_URI}")
        print(f"Neo4j User:   {NEO4J_USER}")
    print("=" * 70)
    print("📁 Tous les fichiers (HTML, PDF, images) seront sauvegardés dans STORAGE_PATH")
    print("🗄️  Toutes les métadonnées et le contenu seront indexés dans SQLite")
    if NEO4J_ENABLED:
        print("🕸️  Les relations entre pages seront également sauvegardées dans Neo4j")
    print("=" * 70)
    print("Démarrage du crawl...")
    print()
    
    process = CrawlerProcess()
    process.crawl(FHSWFSQLiteSpider)
    process.start()

if __name__ == "__main__":
    main()

