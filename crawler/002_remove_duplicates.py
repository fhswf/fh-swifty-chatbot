#!/usr/bin/env python3
"""
Script pour supprimer les doublons de nœuds Page et PDF dans Neo4j.
- Pages dupliquées: même title et meta_description
- PDFs dupliqués: même file_name et markdown_content
- Garde une seule version de chaque nœud (la plus récente)
- Transfère les relations des nœuds supprimés vers le nœud conservé
"""

import os
from typing import Dict, Any, List, Tuple

from dotenv import load_dotenv
from neo4j import GraphDatabase

# --- Configuration ---
load_dotenv()

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7689")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

class DuplicateRemover:
    """Gestionnaire pour supprimer les doublons de nœuds Page et PDF"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            print(f"✓ Connexion à Neo4j établie: {uri}")
        except Exception as e:
            print(f"⚠️  Erreur de connexion à Neo4j: {e}")
            raise
    
    def find_duplicate_pages(self) -> List[Dict[str, Any]]:
        """
        Trouve les groupes de pages dupliquées (même title et meta_description).
        Retourne une liste de groupes de doublons.
        """
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                # Trouver les groupes de pages avec le même title et meta_description
                result = session.run("""
                    MATCH (p:Page)
                    WHERE p.title IS NOT NULL 
                    AND p.meta_description IS NOT NULL
                    AND p.title <> ""
                    AND p.meta_description <> ""
                    WITH p.title as title, 
                         p.meta_description as meta_description,
                         collect(p) as pages
                    WHERE size(pages) > 1
                    RETURN title, meta_description, pages
                """)
                
                duplicates = []
                for record in result:
                    pages = record["pages"]
                    # Extraire les URLs et dates de mise à jour
                    page_info = []
                    for page in pages:
                        url = page.get("url", "")
                        updated_at = page.get("updated_at", "")
                        page_info.append({
                            'url': url,
                            'updated_at': updated_at
                        })
                    
                    # Trier par updated_at (le plus récent en premier)
                    page_info.sort(key=lambda x: x['updated_at'] or "", reverse=True)
                    
                    duplicates.append({
                        'title': record["title"],
                        'meta_description': record["meta_description"],
                        'pages': page_info,
                        'count': len(page_info)
                    })
                
                return duplicates
                
        except Exception as e:
            print(f"❌ Erreur lors de la recherche des pages dupliquées: {e}")
            return []
    
    def find_duplicate_pdfs(self) -> List[Dict[str, Any]]:
        """
        Trouve les groupes de PDFs dupliqués (même file_name et markdown_content).
        Retourne une liste de groupes de doublons.
        Note: La comparaison de markdown_content peut être lente pour de très longs contenus.
        """
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                # Trouver les groupes de PDFs avec le même file_name et markdown_content
                # Utiliser size() pour éviter de charger tout le contenu en mémoire
                result = session.run("""
                    MATCH (pdf:PDF)
                    WHERE pdf.file_name IS NOT NULL 
                    AND pdf.markdown_content IS NOT NULL
                    AND pdf.file_name <> ""
                    AND size(pdf.markdown_content) > 0
                    WITH pdf.file_name as file_name, 
                         pdf.markdown_content as markdown_content,
                         collect(pdf) as pdfs
                    WHERE size(pdfs) > 1
                    RETURN file_name, markdown_content, pdfs
                """)
                
                duplicates = []
                for record in result:
                    pdfs = record["pdfs"]
                    # Extraire les URLs et dates d'indexation
                    pdf_info = []
                    for pdf in pdfs:
                        url = pdf.get("url", "")
                        indexed_at = pdf.get("indexed_at", "")
                        pdf_info.append({
                            'url': url,
                            'indexed_at': indexed_at
                        })
                    
                    # Trier par indexed_at (le plus récent en premier)
                    pdf_info.sort(key=lambda x: x['indexed_at'] or "", reverse=True)
                    
                    duplicates.append({
                        'file_name': record["file_name"],
                        'markdown_content_length': len(record["markdown_content"]),
                        'pdfs': pdf_info,
                        'count': len(pdf_info)
                    })
                
                return duplicates
                
        except Exception as e:
            print(f"❌ Erreur lors de la recherche des PDFs dupliqués: {e}")
            return []
    
    def remove_duplicate_pages(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Supprime les pages dupliquées en gardant la plus récente.
        Transfère les relations des pages supprimées vers la page conservée.
        """
        if not self.driver:
            return {"groups": 0, "removed": 0, "errors": 0}
        
        stats = {"groups": 0, "removed": 0, "errors": 0}
        duplicates = self.find_duplicate_pages()
        
        if not duplicates:
            print("✓ Aucune page dupliquée trouvée")
            return stats
        
        stats["groups"] = len(duplicates)
        print(f"📄 Trouvé {len(duplicates)} groupe(s) de pages dupliquées")
        
        try:
            with self.driver.session() as session:
                for group in duplicates:
                    pages = group['pages']
                    if len(pages) < 2:
                        continue
                    
                    # La première page est la plus récente (gardée)
                    keep_url = pages[0]['url']
                    remove_urls = [p['url'] for p in pages[1:]]
                    
                    if dry_run:
                        print(f"  [DRY RUN] Garder: {keep_url}")
                        for url in remove_urls:
                            print(f"  [DRY RUN] Supprimer: {url}")
                        stats["removed"] += len(remove_urls)
                        continue
                    
                    # Pour chaque page à supprimer, transférer les relations
                    for remove_url in remove_urls:
                        try:
                            # Transférer les relations HAS_CONTENT vers la page conservée
                            session.run("""
                                MATCH (remove:Page {url: $remove_url})-[r:HAS_CONTENT]->(c:Content)
                                MATCH (keep:Page {url: $keep_url})
                                MERGE (keep)-[:HAS_CONTENT]->(c)
                                DELETE r
                            """, {
                                'remove_url': remove_url,
                                'keep_url': keep_url
                            })
                            
                            # Transférer les relations PAGE_HAS_PDF vers la page conservée
                            session.run("""
                                MATCH (remove:Page {url: $remove_url})-[r:PAGE_HAS_PDF]->(pdf:PDF)
                                MATCH (keep:Page {url: $keep_url})
                                MERGE (keep)-[new_r:PAGE_HAS_PDF]->(pdf)
                                SET new_r.link_text = r.link_text,
                                    new_r.link_type = r.link_type
                                DELETE r
                            """, {
                                'remove_url': remove_url,
                                'keep_url': keep_url
                            })
                            
                            # Transférer les relations LINKS_TO (si la page est source)
                            session.run("""
                                MATCH (remove:Page {url: $remove_url})-[r:LINKS_TO]->(target)
                                MATCH (keep:Page {url: $keep_url})
                                MERGE (keep)-[new_r:LINKS_TO]->(target)
                                SET new_r += properties(r)
                                DELETE r
                            """, {
                                'remove_url': remove_url,
                                'keep_url': keep_url
                            })
                            
                            # Transférer les relations LINKS_TO (si la page est cible)
                            session.run("""
                                MATCH (source)-[r:LINKS_TO]->(remove:Page {url: $remove_url})
                                MATCH (keep:Page {url: $keep_url})
                                MERGE (source)-[new_r:LINKS_TO]->(keep)
                                SET new_r += properties(r)
                                DELETE r
                            """, {
                                'remove_url': remove_url,
                                'keep_url': keep_url
                            })
                            
                            # Supprimer la page dupliquée
                            session.run("""
                                MATCH (p:Page {url: $remove_url})
                                DETACH DELETE p
                            """, {
                                'remove_url': remove_url
                            })
                            
                            stats["removed"] += 1
                            
                        except Exception as e:
                            print(f"❌ Erreur lors de la suppression de {remove_url}: {e}")
                            stats["errors"] += 1
                    
                    if stats["removed"] <= 5:
                        print(f"✓ Groupe: '{group['title'][:50]}...' -> Gardé: {keep_url}, Supprimé: {len(remove_urls)}")
                
        except Exception as e:
            print(f"❌ Erreur lors de la suppression des pages dupliquées: {e}")
            stats["errors"] += 1
        
        return stats
    
    def remove_duplicate_pdfs(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Supprime les PDFs dupliqués en gardant le plus récent.
        Transfère les relations des PDFs supprimés vers le PDF conservé.
        """
        if not self.driver:
            return {"groups": 0, "removed": 0, "errors": 0}
        
        stats = {"groups": 0, "removed": 0, "errors": 0}
        duplicates = self.find_duplicate_pdfs()
        
        if not duplicates:
            print("✓ Aucun PDF dupliqué trouvé")
            return stats
        
        stats["groups"] = len(duplicates)
        print(f"📄 Trouvé {len(duplicates)} groupe(s) de PDFs dupliqués")
        
        try:
            with self.driver.session() as session:
                for group in duplicates:
                    pdfs = group['pdfs']
                    if len(pdfs) < 2:
                        continue
                    
                    # Le premier PDF est le plus récent (gardé)
                    keep_url = pdfs[0]['url']
                    remove_urls = [p['url'] for p in pdfs[1:]]
                    
                    if dry_run:
                        print(f"  [DRY RUN] Garder: {keep_url}")
                        for url in remove_urls:
                            print(f"  [DRY RUN] Supprimer: {url}")
                        stats["removed"] += len(remove_urls)
                        continue
                    
                    # Pour chaque PDF à supprimer, transférer les relations
                    for remove_url in remove_urls:
                        try:
                            # Transférer les relations HAS_PDF vers le PDF conservé
                            session.run("""
                                MATCH (u:URL)-[r:HAS_PDF]->(remove:PDF {url: $remove_url})
                                MATCH (keep:PDF {url: $keep_url})
                                MERGE (u)-[:HAS_PDF]->(keep)
                                DELETE r
                            """, {
                                'remove_url': remove_url,
                                'keep_url': keep_url
                            })
                            
                            # Transférer les relations PAGE_HAS_PDF vers le PDF conservé
                            session.run("""
                                MATCH (page:Page)-[r:PAGE_HAS_PDF]->(remove:PDF {url: $remove_url})
                                MATCH (keep:PDF {url: $keep_url})
                                MERGE (page)-[new_r:PAGE_HAS_PDF]->(keep)
                                SET new_r.link_text = r.link_text,
                                    new_r.link_type = r.link_type
                                DELETE r
                            """, {
                                'remove_url': remove_url,
                                'keep_url': keep_url
                            })
                            
                            # Transférer les relations HAS_CONTENT vers le PDF conservé
                            session.run("""
                                MATCH (remove:PDF {url: $remove_url})-[r:HAS_CONTENT]->(c:Content)
                                MATCH (keep:PDF {url: $keep_url})
                                MERGE (keep)-[:HAS_CONTENT]->(c)
                                DELETE r
                            """, {
                                'remove_url': remove_url,
                                'keep_url': keep_url
                            })
                            
                            # Supprimer le PDF dupliqué
                            session.run("""
                                MATCH (pdf:PDF {url: $remove_url})
                                DETACH DELETE pdf
                            """, {
                                'remove_url': remove_url
                            })
                            
                            stats["removed"] += 1
                            
                        except Exception as e:
                            print(f"❌ Erreur lors de la suppression de {remove_url}: {e}")
                            stats["errors"] += 1
                    
                    if stats["removed"] <= 5:
                        print(f"✓ Groupe: '{group['file_name']}' -> Gardé: {keep_url}, Supprimé: {len(remove_urls)}")
                
        except Exception as e:
            print(f"❌ Erreur lors de la suppression des PDFs dupliqués: {e}")
            stats["errors"] += 1
        
        return stats
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques sur les nœuds Page et PDF"""
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    RETURN 
                        count{(:Page)} as total_pages,
                        count{(:PDF)} as total_pdfs,
                        count{(:Page)-[:PAGE_HAS_PDF]->()} as page_pdf_relations,
                        count{(:PDF)<-[:PAGE_HAS_PDF]-()} as pdf_page_relations
                """)
                
                record = result.single()
                return {
                    'total_pages': record['total_pages'],
                    'total_pdfs': record['total_pdfs'],
                    'page_pdf_relations': record['page_pdf_relations'],
                    'pdf_page_relations': record['pdf_page_relations']
                }
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des stats: {e}")
            return {}
    
    def close(self):
        """Ferme la connexion à Neo4j"""
        if self.driver:
            self.driver.close()
            print("✓ Connexion Neo4j fermée")

def main():
    """Fonction principale"""
    import sys
    
    # Vérifier si --dry-run est passé en argument
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    
    print("=" * 70)
    print("FH-SWF Duplicate Remover - Suppression des doublons Page et PDF")
    print("=" * 70)
    print(f"Neo4j URI:     {NEO4J_URI}")
    print(f"Neo4j User:    {NEO4J_USER}")
    print(f"Mode:          {'DRY RUN (simulation)' if dry_run else 'EXÉCUTION RÉELLE'}")
    print("=" * 70)
    
    try:
        # Initialiser le gestionnaire
        remover = DuplicateRemover(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        
        # Afficher les statistiques avant
        print("\n📊 STATISTIQUES AVANT SUPPRESSION")
        print("=" * 70)
        before_stats = remover.get_stats()
        if before_stats:
            print(f"Total Pages:           {before_stats.get('total_pages', 0)}")
            print(f"Total PDFs:            {before_stats.get('total_pdfs', 0)}")
            print(f"Relations PAGE_HAS_PDF: {before_stats.get('page_pdf_relations', 0)}")
        
        # Rechercher et supprimer les pages dupliquées
        print("\n" + "=" * 70)
        print("🔍 RECHERCHE DES PAGES DUPLIQUÉES")
        print("=" * 70)
        page_duplicates = remover.find_duplicate_pages()
        print(f"✓ Groupes de pages dupliquées trouvés: {len(page_duplicates)}")
        if page_duplicates:
            total_duplicate_pages = sum(g['count'] - 1 for g in page_duplicates)
            print(f"✓ Pages dupliquées à supprimer: {total_duplicate_pages}")
        
        # Rechercher et supprimer les PDFs dupliqués
        print("\n" + "=" * 70)
        print("🔍 RECHERCHE DES PDFS DUPLIQUÉS")
        print("=" * 70)
        pdf_duplicates = remover.find_duplicate_pdfs()
        print(f"✓ Groupes de PDFs dupliqués trouvés: {len(pdf_duplicates)}")
        if pdf_duplicates:
            total_duplicate_pdfs = sum(g['count'] - 1 for g in pdf_duplicates)
            print(f"✓ PDFs dupliqués à supprimer: {total_duplicate_pdfs}")
        
        if dry_run:
            print("\n" + "=" * 70)
            print("⚠️  MODE DRY RUN - Aucune suppression effectuée")
            print("=" * 70)
            print("Pour effectuer la suppression, exécutez sans --dry-run")
        else:
            # Supprimer les pages dupliquées
            print("\n" + "=" * 70)
            print("🗑️  SUPPRESSION DES PAGES DUPLIQUÉES")
            print("=" * 70)
            page_stats = remover.remove_duplicate_pages(dry_run=False)
            print(f"✓ Groupes traités: {page_stats['groups']}")
            print(f"✓ Pages supprimées: {page_stats['removed']}")
            if page_stats['errors'] > 0:
                print(f"❌ Erreurs: {page_stats['errors']}")
            
            # Supprimer les PDFs dupliqués
            print("\n" + "=" * 70)
            print("🗑️  SUPPRESSION DES PDFS DUPLIQUÉS")
            print("=" * 70)
            pdf_stats = remover.remove_duplicate_pdfs(dry_run=False)
            print(f"✓ Groupes traités: {pdf_stats['groups']}")
            print(f"✓ PDFs supprimés: {pdf_stats['removed']}")
            if pdf_stats['errors'] > 0:
                print(f"❌ Erreurs: {pdf_stats['errors']}")
        
        # Afficher les statistiques après
        print("\n" + "=" * 70)
        print("📊 STATISTIQUES APRÈS SUPPRESSION")
        print("=" * 70)
        after_stats = remover.get_stats()
        if after_stats:
            print(f"Total Pages:           {after_stats.get('total_pages', 0)}")
            print(f"Total PDFs:            {after_stats.get('total_pdfs', 0)}")
            print(f"Relations PAGE_HAS_PDF: {after_stats.get('page_pdf_relations', 0)}")
            
            if before_stats:
                pages_removed = before_stats.get('total_pages', 0) - after_stats.get('total_pages', 0)
                pdfs_removed = before_stats.get('total_pdfs', 0) - after_stats.get('total_pdfs', 0)
                print(f"\nPages supprimées:      {pages_removed}")
                print(f"PDFs supprimés:        {pdfs_removed}")
        
        print("=" * 70)
        print("✅ Traitement terminé avec succès!")
        
        remover.close()
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

