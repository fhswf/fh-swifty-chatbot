#!/usr/bin/env python3
"""
Script utilitaire pour explorer et requêter la base de données du crawler.
"""

import os
import sys
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Configuration
load_dotenv()
TARGET_PATH = os.getenv("TARGET_PATH", "").strip() or "./downloaded"
DB_PATH = os.getenv("DB_PATH", os.path.join(TARGET_PATH, "crawl_index.db"))
DB_PATH = os.path.abspath(DB_PATH)


class CrawlDatabase:
    def __init__(self, db_path: str):
        if not os.path.exists(db_path):
            print(f"❌ Base de données introuvable: {db_path}")
            sys.exit(1)
        
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def get_stats(self):
        """Affiche les statistiques globales"""
        print("\n" + "=" * 70)
        print("STATISTIQUES DU CRAWL")
        print("=" * 70)
        
        # URLs totales
        self.cursor.execute("SELECT COUNT(*) FROM urls")
        total_urls = self.cursor.fetchone()[0]
        print(f"📊 URLs totales:          {total_urls:>10}")
        
        # Pages HTML
        self.cursor.execute("SELECT COUNT(*) FROM page_content")
        total_pages = self.cursor.fetchone()[0]
        print(f"📄 Pages HTML:            {total_pages:>10}")
        
        # PDFs
        self.cursor.execute("SELECT COUNT(*) FROM urls WHERE is_pdf = 1")
        total_pdfs = self.cursor.fetchone()[0]
        print(f"📕 Documents PDF:         {total_pdfs:>10}")
        
        # Taille totale des PDFs
        self.cursor.execute("SELECT SUM(file_size) FROM pdf_documents")
        result = self.cursor.fetchone()[0]
        pdf_size = result if result else 0
        print(f"💾 Taille PDFs:           {self._format_size(pdf_size):>10}")
        
        # Liens
        self.cursor.execute("SELECT COUNT(*) FROM links")
        total_links = self.cursor.fetchone()[0]
        print(f"🔗 Liens totaux:          {total_links:>10}")
        
        # Liens internes
        self.cursor.execute("SELECT COUNT(*) FROM links WHERE is_internal = 1")
        internal_links = self.cursor.fetchone()[0]
        print(f"🔗 Liens internes:        {internal_links:>10}")
        
        # Liens externes
        external_links = total_links - internal_links
        print(f"🔗 Liens externes:        {external_links:>10}")
        
        # Ressources
        self.cursor.execute("SELECT COUNT(*) FROM resources")
        total_resources = self.cursor.fetchone()[0]
        print(f"🖼️  Ressources:            {total_resources:>10}")
        
        # Domaines
        self.cursor.execute("SELECT COUNT(DISTINCT domain) FROM urls")
        total_domains = self.cursor.fetchone()[0]
        print(f"🌐 Domaines:              {total_domains:>10}")
        
        # Dernière mise à jour
        self.cursor.execute("SELECT MAX(last_crawled) FROM urls")
        last_crawl = self.cursor.fetchone()[0]
        if last_crawl:
            print(f"🕐 Dernier crawl:         {last_crawl}")
        
        print("=" * 70 + "\n")
    
    def list_pdfs(self, limit: int = 50):
        """Liste tous les PDFs crawlés"""
        print(f"\n📕 DOCUMENTS PDF (limite: {limit})")
        print("-" * 100)
        
        self.cursor.execute("""
            SELECT u.url, p.file_name, p.file_size, u.last_crawled
            FROM pdf_documents p
            JOIN urls u ON p.url_id = u.id
            ORDER BY p.file_size DESC
            LIMIT ?
        """, (limit,))
        
        rows = self.cursor.fetchall()
        
        if not rows:
            print("Aucun PDF trouvé.")
            return
        
        for i, row in enumerate(rows, 1):
            size = self._format_size(row['file_size'])
            print(f"{i:3}. {row['file_name']}")
            print(f"     URL:    {row['url']}")
            print(f"     Taille: {size}")
            print(f"     Date:   {row['last_crawled']}")
            print()
    
    def search_pages(self, query: str, limit: int = 20):
        """Recherche dans le contenu texte des pages"""
        print(f"\n🔍 RECHERCHE: '{query}' (limite: {limit})")
        print("-" * 100)
        
        self.cursor.execute("""
            SELECT u.url, p.title, p.text_content, u.last_crawled
            FROM page_content p
            JOIN urls u ON p.url_id = u.id
            WHERE p.text_content LIKE ? OR p.title LIKE ?
            ORDER BY u.last_crawled DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit))
        
        rows = self.cursor.fetchall()
        
        if not rows:
            print(f"Aucun résultat pour '{query}'")
            return
        
        for i, row in enumerate(rows, 1):
            title = row['title'] or "(sans titre)"
            # Extraire un snippet du texte
            text = row['text_content'] or ""
            idx = text.lower().find(query.lower())
            if idx >= 0:
                start = max(0, idx - 50)
                end = min(len(text), idx + 100)
                snippet = "..." + text[start:end] + "..."
            else:
                snippet = text[:150] + "..." if len(text) > 150 else text
            
            print(f"{i:3}. {title}")
            print(f"     URL: {row['url']}")
            print(f"     {snippet}")
            print()
    
    def list_domains(self):
        """Liste tous les domaines crawlés"""
        print("\n🌐 DOMAINES CRAWLÉS")
        print("-" * 70)
        
        self.cursor.execute("""
            SELECT domain, COUNT(*) as count, 
                   SUM(CASE WHEN is_pdf = 1 THEN 1 ELSE 0 END) as pdf_count
            FROM urls
            GROUP BY domain
            ORDER BY count DESC
        """)
        
        rows = self.cursor.fetchall()
        
        for row in rows:
            print(f"{row['domain']:40} | URLs: {row['count']:>5} | PDFs: {row['pdf_count']:>4}")
        print()
    
    def get_page_links(self, url: str):
        """Affiche tous les liens d'une page spécifique"""
        print(f"\n🔗 LIENS DE: {url}")
        print("-" * 100)
        
        # Trouver l'URL ID
        self.cursor.execute("SELECT id FROM urls WHERE url = ?", (url,))
        result = self.cursor.fetchone()
        
        if not result:
            print(f"❌ URL non trouvée: {url}")
            return
        
        url_id = result['id']
        
        # Récupérer les liens
        self.cursor.execute("""
            SELECT target_url, link_text, link_type, is_internal
            FROM links
            WHERE source_url_id = ?
            ORDER BY link_type, target_url
        """, (url_id,))
        
        rows = self.cursor.fetchall()
        
        if not rows:
            print("Aucun lien trouvé.")
            return
        
        print(f"Total: {len(rows)} liens\n")
        
        current_type = None
        for row in rows:
            if row['link_type'] != current_type:
                current_type = row['link_type']
                print(f"\n[{current_type.upper()}]")
            
            internal = "🔗" if row['is_internal'] else "🌐"
            link_text = row['link_text'] or ""
            if link_text and len(link_text) > 50:
                link_text = link_text[:47] + "..."
            
            print(f"  {internal} {row['target_url']}")
            if link_text:
                print(f"     Text: {link_text}")
    
    def export_pdf_list(self, output_file: str):
        """Exporte la liste des PDFs dans un fichier CSV"""
        import csv
        
        self.cursor.execute("""
            SELECT u.url, p.file_name, p.file_size, u.last_crawled
            FROM pdf_documents p
            JOIN urls u ON p.url_id = u.id
            ORDER BY u.url
        """)
        
        rows = self.cursor.fetchall()
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['URL', 'File Name', 'Size (bytes)', 'Crawled At'])
            
            for row in rows:
                writer.writerow([row['url'], row['file_name'], row['file_size'], row['last_crawled']])
        
        print(f"✓ Liste des PDFs exportée vers: {output_file}")
        print(f"  {len(rows)} PDFs exportés")
    
    def export_pdf_content(self, url: str, output_file: str):
        """Exporte le contenu d'un PDF spécifique"""
        self.cursor.execute("""
            SELECT p.content, p.file_name
            FROM pdf_documents p
            JOIN urls u ON p.url_id = u.id
            WHERE u.url = ?
        """, (url,))
        
        result = self.cursor.fetchone()
        
        if not result:
            print(f"❌ PDF non trouvé: {url}")
            return
        
        content = result['content']
        file_name = result['file_name']
        
        with open(output_file, 'wb') as f:
            f.write(content)
        
        print(f"✓ PDF exporté: {file_name}")
        print(f"  Destination: {output_file}")
        print(f"  Taille: {self._format_size(len(content))}")
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Formate une taille en bytes de manière lisible"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def close(self):
        self.conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Utilitaire pour explorer la base de données du crawler FH-SWF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  %(prog)s stats                              # Affiche les statistiques
  %(prog)s pdfs                               # Liste tous les PDFs
  %(prog)s search "informatique"              # Recherche dans le contenu
  %(prog)s domains                            # Liste les domaines
  %(prog)s links "https://www.fh-swf.de/"     # Affiche les liens d'une page
  %(prog)s export-pdfs pdfs.csv               # Exporte la liste des PDFs
  %(prog)s export-pdf <URL> output.pdf        # Exporte un PDF spécifique
        """
    )
    
    parser.add_argument('command', choices=['stats', 'pdfs', 'search', 'domains', 'links', 'export-pdfs', 'export-pdf'],
                       help='Commande à exécuter')
    parser.add_argument('args', nargs='*', help='Arguments de la commande')
    parser.add_argument('--limit', type=int, default=50, help='Limite de résultats (défaut: 50)')
    parser.add_argument('--db', type=str, default=DB_PATH, help=f'Chemin vers la base de données (défaut: {DB_PATH})')
    
    args = parser.parse_args()
    
    db = CrawlDatabase(args.db)
    
    try:
        if args.command == 'stats':
            db.get_stats()
        
        elif args.command == 'pdfs':
            db.list_pdfs(limit=args.limit)
        
        elif args.command == 'search':
            if not args.args:
                print("❌ Erreur: Veuillez spécifier un terme de recherche")
                sys.exit(1)
            query = ' '.join(args.args)
            db.search_pages(query, limit=args.limit)
        
        elif args.command == 'domains':
            db.list_domains()
        
        elif args.command == 'links':
            if not args.args:
                print("❌ Erreur: Veuillez spécifier une URL")
                sys.exit(1)
            url = args.args[0]
            db.get_page_links(url)
        
        elif args.command == 'export-pdfs':
            if not args.args:
                print("❌ Erreur: Veuillez spécifier un fichier de sortie")
                sys.exit(1)
            output_file = args.args[0]
            db.export_pdf_list(output_file)
        
        elif args.command == 'export-pdf':
            if len(args.args) < 2:
                print("❌ Erreur: Veuillez spécifier l'URL et le fichier de sortie")
                sys.exit(1)
            url = args.args[0]
            output_file = args.args[1]
            db.export_pdf_content(url, output_file)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

