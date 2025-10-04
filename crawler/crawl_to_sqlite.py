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
import mimetypes
from datetime import datetime
from urllib.parse import urlparse, unquote
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import TextResponse, Response

# --- Configuration ---
load_dotenv()
TARGET_PATH = os.getenv("TARGET_PATH", "").strip() or "./downloaded"
TARGET_PATH = os.path.abspath(TARGET_PATH)

DB_PATH = os.getenv("DB_PATH", os.path.join(TARGET_PATH, "crawl_index.db"))
DB_PATH = os.path.abspath(DB_PATH)

EXCLUDE_DOMAINS = os.getenv("EXCLUDE_DOMAINS", "").strip()
EXCLUDE_DOMAINS_LIST = [d.strip() for d in EXCLUDE_DOMAINS.split(",") if d.strip()]

# --- Database Schema ---
class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Initialise la structure de la base de données"""
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
                html_content BLOB,
                text_content TEXT,
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
                file_size INTEGER,
                content BLOB,
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
                file_size INTEGER,
                content BLOB,
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
                            checksum: str) -> int:
        """Insère ou met à jour une URL et retourne son ID"""
        cursor = self.conn.cursor()
        parsed = urlparse(url)
        
        cursor.execute("""
            INSERT INTO urls (url, domain, path, query_string, status_code, 
                            content_type, content_length, is_pdf, is_internal, checksum)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                status_code = excluded.status_code,
                content_type = excluded.content_type,
                content_length = excluded.content_length,
                last_crawled = CURRENT_TIMESTAMP,
                checksum = excluded.checksum
            RETURNING id
        """, (url, parsed.netloc, parsed.path, parsed.query, status_code,
              content_type, content_length, is_pdf, is_internal, checksum))
        
        result = cursor.fetchone()
        url_id = result[0]
        self.conn.commit()
        return url_id
    
    def insert_page_content(self, url_id: int, html_content: bytes, 
                           text_content: str, title: str, meta_description: str,
                           headers: str):
        """Insère le contenu d'une page"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO page_content 
            (url_id, html_content, text_content, title, meta_description, headers)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (url_id, html_content, text_content, title, meta_description, headers))
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
    
    def insert_pdf(self, url_id: int, file_name: str, content: bytes, 
                   file_size: int, checksum: str):
        """Insère un document PDF"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO pdf_documents 
            (url_id, file_name, content, file_size, checksum)
            VALUES (?, ?, ?, ?, ?)
        """, (url_id, file_name, content, file_size, checksum))
        self.conn.commit()
    
    def insert_resource(self, url_id: int, resource_type: str, file_name: str,
                       content: bytes, file_size: int, checksum: str):
        """Insère une ressource (image, CSS, JS, etc.)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO resources 
            (url_id, resource_type, file_name, content, file_size, checksum)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (url_id, resource_type, file_name, content, file_size, checksum))
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

# --- Utility Functions ---
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
    text = " ".join(t.strip() for t in text_parts if t.strip())
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
        
        # Calculer le checksum
        checksum = compute_checksum(response.body)
        
        # Déterminer le type de contenu
        content_type = response.headers.get('Content-Type', b'').decode('utf-8', 'ignore')
        is_pdf = 'application/pdf' in content_type.lower() or url.lower().endswith('.pdf')
        
        # Insérer/mettre à jour l'URL
        url_id = self.db.insert_or_update_url(
            url=url,
            status_code=response.status,
            content_type=content_type,
            content_length=len(response.body),
            is_pdf=is_pdf,
            is_internal=self._is_internal_and_allowed(url),
            checksum=checksum
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
                
                # Enregistrer le lien de redirection
                self.db.insert_link(
                    source_url_id=url_id,
                    target_url=target,
                    link_text="[redirect]",
                    link_type="redirect",
                    is_internal=self._is_internal_and_allowed(target)
                )
                
                if self._is_internal_and_allowed(target):
                    self.logger.info("Following redirect: %s -> %s", url, target)
                    yield scrapy.Request(target, callback=self.parse)
            return
        
        # Traiter les PDFs
        if is_pdf:
            self.pdf_count += 1
            file_name = os.path.basename(urlparse(url).path) or f"document_{url_id}.pdf"
            self.db.insert_pdf(
                url_id=url_id,
                file_name=file_name,
                content=response.body,
                file_size=len(response.body),
                checksum=checksum
            )
            self.logger.info(f"✓ Saved PDF: {file_name} ({len(response.body)} bytes)")
            return
        
        # Traiter les pages HTML
        if isinstance(response, TextResponse):
            # Extraire les métadonnées
            title = response.xpath('//title/text()').get() or ""
            meta_desc = response.xpath('//meta[@name="description"]/@content').get() or ""
            text_content = extract_text_content(response)
            headers_str = str(dict(response.headers))
            
            # Sauvegarder le contenu de la page
            self.db.insert_page_content(
                url_id=url_id,
                html_content=response.body,
                text_content=text_content,
                title=title.strip(),
                meta_description=meta_desc.strip(),
                headers=headers_str
            )
            
            # Extraire et enregistrer tous les liens
            selectors = {
                "a": ("//a/@href", "//a/text()"),
                "link": ("//link/@href", None),
                "img": ("//img/@src", "//img/@alt"),
                "script": ("//script/@src", None),
                "iframe": ("//iframe/@src", None),
                "source": ("//source/@src", None),
            }
            
            seen_links = set()
            for link_type, (href_xpath, text_xpath) in selectors.items():
                hrefs = response.xpath(href_xpath).getall()
                texts = response.xpath(text_xpath).getall() if text_xpath else [None] * len(hrefs)
                
                for href, link_text in zip(hrefs, texts):
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
                    
                    # Enregistrer le lien
                    is_internal = self._is_internal_and_allowed(abs_url)
                    self.db.insert_link(
                        source_url_id=url_id,
                        target_url=abs_url,
                        link_text=link_text.strip() if link_text else None,
                        link_type=link_type,
                        is_internal=is_internal
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
            
            self.db.insert_resource(
                url_id=url_id,
                resource_type=resource_type,
                file_name=file_name,
                content=response.body,
                file_size=len(response.body),
                checksum=checksum
            )
    
    def closed(self, reason):
        """Appelé quand le spider se termine"""
        stats = self.db.get_stats()
        self.logger.info("=" * 60)
        self.logger.info("Crawl terminé!")
        self.logger.info(f"Raison: {reason}")
        self.logger.info("-" * 60)
        self.logger.info(f"URLs totales:     {stats['total_urls']}")
        self.logger.info(f"Pages HTML:       {stats['total_pages']}")
        self.logger.info(f"Documents PDF:    {stats['total_pdfs']}")
        self.logger.info(f"Liens totaux:     {stats['total_links']}")
        self.logger.info(f"Ressources:       {stats['total_resources']}")
        self.logger.info("-" * 60)
        self.logger.info(f"Base de données: {DB_PATH}")
        self.logger.info("=" * 60)
        
        self.db.close()

# --- Runner ---
def main():
    print("=" * 60)
    print("FH-SWF Crawler avec indexation SQLite")
    print("=" * 60)
    print(f"TARGET_PATH: {TARGET_PATH}")
    print(f"DB_PATH:     {DB_PATH}")
    print(f"Exclusions:  {EXCLUDE_DOMAINS_LIST or 'Aucune'}")
    print("=" * 60)
    print("Démarrage du crawl...")
    print()
    
    process = CrawlerProcess()
    process.crawl(FHSWFSQLiteSpider)
    process.start()

if __name__ == "__main__":
    main()

