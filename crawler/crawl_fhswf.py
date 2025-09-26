#!/usr/bin/env python3
"""
Crawl-Skript für fh-swf.de.
- Speichert alle Responses (HTML, PDF, Bilder...) unter TARGET_PATH (aus .env).
- Überspringt URLs mit "/intern/".
- Folgt nur Links/Redirects, die zu fh-swf.de gehören.
- Nutzt HTTPCACHE, damit bei wiederholten Läufen nur geänderte Ressourcen neu geladen werden.
- REDIRECT_ENABLED = False und handle_httpstatus_list erlaubt es dem Spider, 3xx
  Antworten zu sehen und nur interne Redirects manuell zu folgen.
"""

import os
import re
import hashlib
import fnmatch
from urllib.parse import urlparse, unquote
from pathlib import Path

from dotenv import load_dotenv
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import TextResponse

# --- Laden der .env ---
load_dotenv()  # liest .env im aktuellen Arbeitsverzeichnis
TARGET_PATH = os.getenv("TARGET_PATH", "").strip() or "./downloaded"
TARGET_PATH = os.path.abspath(TARGET_PATH)

STORAGE_PATH = os.getenv("STORAGE_PATH", os.path.join(TARGET_PATH, "data"))
STORAGE_PATH = os.path.abspath(STORAGE_PATH)

EXCLUDE_DOMAINS = os.getenv("EXCLUDE_DOMAINS", "").strip()
# z.B. EXCLUDE_DOMAINS="www7.fh-swf.de,static.bad.example"
EXCLUDE_DOMAINS_LIST = [d.strip() for d in EXCLUDE_DOMAINS.split(",") if d.strip()]

# --- Utility-Funktionen ---
def sanitize_path_component(s: str) -> str:
    s = unquote(s or "")
    s = s.replace("\\", "/")
    s = re.sub(r"[^A-Za-z0-9\-\._\u00C0-\u017F]+", "_", s)
    s = s.strip("._")
    return s or "_"

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
        base = m.group(1) if m else filename
        ext = m.group(2) if m and m.group(2) else ""
        comps[-1] = f"{base}_{qhash}{ext}"
    local_path = Path(base_dir) / netloc
    for c in comps:
        local_path /= c
    return str(local_path)

def hostname_of(url_or_netloc):
    parsed = urlparse(url_or_netloc)
    # parsed.hostname ist None wenn input nur 'example.com' gegeben wurde, also fallback:
    return parsed.hostname or (parsed.netloc.split(":")[0] if parsed.netloc else url_or_netloc.split(":")[0])

def is_blacklisted_host(hostname: str) -> bool:
    # hostname kann z.B. 'www7.fh-swf.de'
    if not hostname:
        return False
    for pat in EXCLUDE_DOMAINS_LIST:
        # Ermögliche einfache Wildcards, z.B. "*.bad.example"
        if fnmatch.fnmatch(hostname, pat):
            return True
    return False

# --- Spider ---
class FHSWFSpider(scrapy.Spider):
    name = "fhswf"
    allowed_domains = ["fh-swf.de", "www.fh-swf.de"]
    start_urls = [
        "https://www.fh-swf.de/",
        "https://fh-swf.de/",
    ]

    # Erlaube dem Spider ausdrücklich 3xx-Responses zu verarbeiten, damit die
    # manuelle Redirect-Logik greifen kann.
    handle_httpstatus_list = [301, 302, 303, 307, 308]

    custom_settings = {
        "LOG_LEVEL": "INFO",
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 0.2,
        "CONCURRENT_REQUESTS": 8,
        "USER_AGENT": "fhswf-crawler/1.0 (+https://www.fh-swf.de/)",
        "DOWNLOAD_TIMEOUT": 60,

        # Keine automatische Weiterverfolgung von Redirects (wir behandeln 3xx manuell)
        "REDIRECT_ENABLED": False,

        # HTTP cache: persistent unter TARGET_PATH/httpcache -> conditional GETs bei weiteren Läufen
        "HTTPCACHE_ENABLED": True,
        "HTTPCACHE_DIR": os.path.join(TARGET_PATH, "httpcache"),
        "HTTPCACHE_IGNORE_MISSING": False,
        "HTTPCACHE_POLICY": "scrapy.extensions.httpcache.RFC2616Policy",
        "HTTPCACHE_STORAGE": "scrapy.extensions.httpcache.FilesystemCacheStorage",

        # Optionale Persistenz der Crawl-Queue / Dupe-Filter:
        "JOBDIR": os.path.join(TARGET_PATH, "jobstate"),
    }

    def _is_internal_and_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        # Erstens: Domain muss zu fh-swf.de gehören
        if not host.endswith("fh-swf.de"):
            return False
        # Zweitens: Host darf nicht auf der Blacklist stehen
        if is_blacklisted_host(host):
            self.logger.debug("Excluded by blacklist: %s", host)
            return False
        return True

    def parse(self, response):
        url = response.url
        if "/intern/" in url:
            self.logger.debug("Skipping (intern): %s", url)
            return

        # Speichere Body in Datei
        try:
            local_path = url_to_local_path(url, STORAGE_PATH)
            local_file = Path(local_path)
            local_file.parent.mkdir(parents=True, exist_ok=True)
            with local_file.open("wb") as f:
                f.write(response.body)
            self.logger.info("Saved: %s -> %s", url, local_path)
        except Exception as e:
            self.logger.error("Failed to save %s: %s", url, e)

        # Wenn die Response ein Redirect-Response ist (3xx), dann prüfe Location und
        # folge nur, wenn das Ziel intern ist.
        if 300 <= response.status < 400:
            loc = response.headers.get("Location") or response.headers.get(b"location")
            if loc:
                try:
                    loc = loc.decode() if isinstance(loc, (bytes, bytearray)) else str(loc)
                except Exception:
                    loc = str(loc)
                target = response.urljoin(loc)
                if self._is_internal_and_allowed(target):
                    self.logger.info("Following internal redirect: %s -> %s", response.url, target)
                    yield scrapy.Request(target, callback=self.parse)
                else:
                    self.logger.info("Skipping external redirect: %s -> %s", response.url, target)
            return  # nach Redirect nichts weiter aus dieser Response extrahieren

        # Links nur aus TextResponses extrahieren (vermeidet NotSupported auf binären Antworten)
        if not isinstance(response, TextResponse):
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
                if self._is_internal_and_allowed(abs_url):
                    yield scrapy.Request(abs_url, callback=self.parse)
                else:
                    self.logger.debug("Not following external link: %s", abs_url)

# --- Runner ---
def main():
    print("TARGET_PATH =", TARGET_PATH)
    print("Starting crawl of fh-swf.de ...")
    process = CrawlerProcess()
    process.crawl(FHSWFSpider)
    process.start()

if __name__ == "__main__":
    main()