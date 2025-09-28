## Scrapy crawler

### Input from gpt-5-mini

Hier ist ein einsatzbereites Scrapy-Skript, das die ganze Site fh-swf.de crawlt, alle Antworten (HTML, PDFs, Bilder usw.) in einem konfigurierbaren Zielverzeichnis speichert und alle URLs überspringt, die das Muster "/intern/" enthalten. Der Zielpfad wird aus einer .env-Datei gelesen (mit python-dotenv). Das Skript ist als einzelne Datei lauffähig.

Voraussetzungen:

Python 3.11+
pip install scrapy python-dotenv
Beispiel .env:
TARGET_PATH=/pfad/zum/speicherort

Speichere das Script z. B. als crawl_fhswf.py und starte es mit:
python crawl_fhswf.py

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