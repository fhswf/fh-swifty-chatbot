#!/usr/bin/env python3
"""
Script pour mettre à jour les propriétés link_to_redirect et link_to_pdf 
sur toutes les relations LINKS_TO existantes dans Neo4j.
- link_to_redirect: true si le status_code du nœud target est 302, sinon false
- link_to_pdf: true si le content_type du nœud target contient application/pdf
"""

import os
from typing import Dict, Any

from dotenv import load_dotenv
from neo4j import GraphDatabase

# --- Configuration ---
load_dotenv()

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7689")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

class LinkPropertiesUpdater:
    """Gestionnaire pour mettre à jour les propriétés des relations LINKS_TO"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            print(f"✓ Connexion à Neo4j établie: {uri}")
        except Exception as e:
            print(f"⚠️  Erreur de connexion à Neo4j: {e}")
            raise
    
    def update_all_link_properties(self) -> Dict[str, int]:
        """
        Met à jour toutes les relations LINKS_TO avec les propriétés link_to_redirect et link_to_pdf.
        Retourne des statistiques sur le traitement.
        """
        if not self.driver:
            return {"processed": 0, "updated": 0, "errors": 0}
        
        stats = {"processed": 0, "updated": 0, "errors": 0}
        
        try:
            with self.driver.session() as session:
                # Récupérer toutes les relations LINKS_TO avec les propriétés du nœud target
                result = session.run("""
                    MATCH (source:URL)-[r:LINKS_TO]->(target:URL)
                    RETURN source.url as source_url,
                           target.url as target_url,
                           target.status_code as status_code,
                           target.content_type as content_type,
                           id(r) as rel_id
                """)
                
                for record in result:
                    stats["processed"] += 1
                    
                    try:
                        source_url = record["source_url"]
                        target_url = record["target_url"]
                        status_code = record["status_code"]
                        content_type = record.get("content_type") or ""
                        rel_id = record["rel_id"]
                        
                        # Déterminer link_to_redirect (true si status_code = 302)
                        link_to_redirect = (status_code == 302) if status_code else False
                        
                        # Déterminer link_to_pdf (true si content_type contient application/pdf)
                        link_to_pdf = False
                        if content_type and 'application/pdf' in content_type.lower():
                            link_to_pdf = True
                        
                        # Mettre à jour la relation
                        session.run("""
                            MATCH (source:URL {url: $source_url})-[r:LINKS_TO]->(target:URL {url: $target_url})
                            SET r.link_to_redirect = $link_to_redirect,
                                r.link_to_pdf = $link_to_pdf
                        """, {
                            'source_url': source_url,
                            'target_url': target_url,
                            'link_to_redirect': link_to_redirect,
                            'link_to_pdf': link_to_pdf
                        })
                        
                        stats["updated"] += 1
                        
                        # Afficher un exemple pour les 10 premiers
                        if stats["updated"] <= 10:
                            print(f"✓ {source_url[:50]}... -> {target_url[:50]}... | redirect={link_to_redirect}, pdf={link_to_pdf}")
                        
                    except Exception as e:
                        print(f"❌ Erreur lors de la mise à jour de la relation: {e}")
                        stats["errors"] += 1
                
        except Exception as e:
            print(f"❌ Erreur lors du traitement des relations: {e}")
            stats["errors"] += 1
        
        return stats
    
    def get_link_properties_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques sur les propriétés des liens"""
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH ()-[r:LINKS_TO]->()
                    RETURN 
                        count(r) as total_links,
                        count(CASE WHEN r.link_to_redirect = true THEN 1 END) as links_to_redirect,
                        count(CASE WHEN r.link_to_pdf = true THEN 1 END) as links_to_pdf,
                        count(CASE WHEN r.link_to_redirect IS NULL THEN 1 END) as missing_redirect,
                        count(CASE WHEN r.link_to_pdf IS NULL THEN 1 END) as missing_pdf
                """)
                
                record = result.single()
                if record:
                    return {
                        'total_links': record['total_links'],
                        'links_to_redirect': record['links_to_redirect'],
                        'links_to_pdf': record['links_to_pdf'],
                        'missing_redirect': record['missing_redirect'],
                        'missing_pdf': record['missing_pdf']
                    }
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des stats: {e}")
            return {}
        
        return {}
    
    def close(self):
        """Ferme la connexion à Neo4j"""
        if self.driver:
            self.driver.close()
            print("✓ Connexion Neo4j fermée")

def main():
    """Fonction principale"""
    print("=" * 70)
    print("FH-SWF Link Properties Updater - Mise à jour des propriétés LINKS_TO")
    print("=" * 70)
    print(f"Neo4j URI:     {NEO4J_URI}")
    print(f"Neo4j User:    {NEO4J_USER}")
    print("=" * 70)
    
    try:
        # Initialiser le gestionnaire
        updater = LinkPropertiesUpdater(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        
        # Afficher les statistiques avant
        print("\n📊 STATISTIQUES AVANT MISE À JOUR")
        print("=" * 70)
        before_stats = updater.get_link_properties_stats()
        if before_stats:
            print(f"Total liens:           {before_stats.get('total_links', 0)}")
            print(f"Liens vers redirect:  {before_stats.get('links_to_redirect', 0)}")
            print(f"Liens vers PDF:       {before_stats.get('links_to_pdf', 0)}")
            print(f"Propriétés manquantes (redirect): {before_stats.get('missing_redirect', 0)}")
            print(f"Propriétés manquantes (pdf):       {before_stats.get('missing_pdf', 0)}")
        
        # Mettre à jour toutes les relations
        print("\n🔄 Mise à jour des relations LINKS_TO...")
        update_stats = updater.update_all_link_properties()
        print(f"✓ Relations traitées: {update_stats['processed']}")
        print(f"✓ Relations mises à jour: {update_stats['updated']}")
        if update_stats['errors'] > 0:
            print(f"❌ Erreurs: {update_stats['errors']}")
        
        # Afficher les statistiques après
        print("\n" + "=" * 70)
        print("📊 STATISTIQUES APRÈS MISE À JOUR")
        print("=" * 70)
        after_stats = updater.get_link_properties_stats()
        if after_stats:
            print(f"Total liens:           {after_stats.get('total_links', 0)}")
            print(f"Liens vers redirect:  {after_stats.get('links_to_redirect', 0)}")
            print(f"Liens vers PDF:       {after_stats.get('links_to_pdf', 0)}")
            print(f"Propriétés manquantes (redirect): {after_stats.get('missing_redirect', 0)}")
            print(f"Propriétés manquantes (pdf):       {after_stats.get('missing_pdf', 0)}")
        
        print("=" * 70)
        print("✅ Traitement terminé avec succès!")
        
        updater.close()
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

