#!/usr/bin/env python3
"""
Script pour attribuer des catégories hiérarchiques aux nœuds Content à partir de leur source_url.
- Extrait les segments du chemin URL comme catégories de niveau 1, 2, 3, 4...
- Ajoute les propriétés category_level_1, category_level_2, etc. aux nœuds Content
- Permet une organisation hiérarchique du contenu basée sur la structure URL
"""

import os
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from dotenv import load_dotenv
from neo4j import GraphDatabase

# --- Configuration ---
load_dotenv()

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7689")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

# Configuration
MAX_CATEGORY_LEVELS = 10  # Nombre maximum de niveaux de catégories à extraire

class CategoryAssigner:
    """Gestionnaire pour attribuer des catégories aux nœuds Content à partir de leur URL"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            self.init_indexes()
            print(f"✓ Connexion à Neo4j établie: {uri}")
        except Exception as e:
            print(f"⚠️  Erreur de connexion à Neo4j: {e}")
            raise
    
    def init_indexes(self):
        """Crée les index pour améliorer les performances de recherche par catégorie"""
        if not self.driver:
            return
        
        with self.driver.session() as session:
            # Index pour les catégories de niveau 1
            indexes = [
                "CREATE INDEX content_category_level_1 IF NOT EXISTS FOR (c:Content) ON (c.category_level_1)",
                "CREATE INDEX content_category_level_2 IF NOT EXISTS FOR (c:Content) ON (c.category_level_2)",
                "CREATE INDEX content_category_level_3 IF NOT EXISTS FOR (c:Content) ON (c.category_level_3)",
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                except Exception:
                    # Index peut déjà exister
                    pass
    
    def extract_categories_from_url(self, url: str) -> Dict[str, Optional[str]]:
        """
        Extrait les catégories hiérarchiques à partir de l'URL.
        Les segments du chemin deviennent les catégories de différents niveaux.
        
        Exemple:
        URL: https://www.fh-swf.de/de/studium/studiengaenge/informatik/index.html
        -> category_level_1: "de"
        -> category_level_2: "studium"
        -> category_level_3: "studiengaenge"
        -> category_level_4: "informatik"
        """
        categories = {}
        
        try:
            parsed = urlparse(url)
            path = parsed.path.strip('/')
            
            if not path:
                return categories
            
            # Diviser le chemin en segments
            segments = [seg for seg in path.split('/') if seg and seg.strip()]
            
            # Filtrer les segments non pertinents (comme index.html, index.php, etc.)
            filtered_segments = []
            for seg in segments:
                # Ignorer les fichiers avec extensions communes
                if '.' in seg:
                    ext = seg.split('.')[-1].lower()
                    if ext in ['html', 'htm', 'php', 'aspx', 'jsp', 'pdf', 'xml']:
                        continue
                filtered_segments.append(seg)
            
            # Attribuer les segments aux niveaux de catégories
            for i, segment in enumerate(filtered_segments[:MAX_CATEGORY_LEVELS], start=1):
                categories[f'category_level_{i}'] = segment
            
            # S'assurer que tous les niveaux jusqu'au maximum sont définis (None si pas de segment)
            for i in range(1, MAX_CATEGORY_LEVELS + 1):
                if f'category_level_{i}' not in categories:
                    categories[f'category_level_{i}'] = None
            
        except Exception as e:
            print(f"⚠️  Erreur lors de l'extraction des catégories pour {url}: {e}")
            # Retourner un dictionnaire avec toutes les catégories à None
            for i in range(1, MAX_CATEGORY_LEVELS + 1):
                categories[f'category_level_{i}'] = None
        
        return categories
    
    def assign_categories_to_content(self, chunk_id: str, categories: Dict[str, Optional[str]]) -> bool:
        """
        Attribue les catégories à un nœud Content spécifique.
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                # Construire la requête SET dynamiquement
                set_clauses = []
                params = {'chunk_id': chunk_id}
                
                for level, value in categories.items():
                    set_clauses.append(f"c.{level} = ${level}")
                    params[level] = value
                
                query = f"""
                    MATCH (c:Content)
                    WHERE c.chunk_id = $chunk_id
                    SET {', '.join(set_clauses)}
                """
                
                session.run(query, params)
                return True
                
        except Exception as e:
            print(f"❌ Erreur lors de l'attribution des catégories pour {chunk_id}: {e}")
            return False
    
    def process_all_content_nodes(self) -> Dict[str, int]:
        """
        Traite tous les nœuds Content et leur attribue des catégories.
        Retourne des statistiques sur le traitement.
        """
        if not self.driver:
            return {"processed": 0, "updated": 0, "errors": 0}
        
        stats = {"processed": 0, "updated": 0, "errors": 0}
        
        try:
            with self.driver.session() as session:
                # Récupérer tous les nœuds Content avec leur source_url
                result = session.run("""
                    MATCH (c:Content)
                    WHERE c.source_url IS NOT NULL
                    RETURN c.chunk_id as chunk_id, 
                           c.source_url as source_url
                """)
                
                for record in result:
                    chunk_id = record["chunk_id"]
                    source_url = record["source_url"]
                    
                    stats["processed"] += 1
                    
                    try:
                        # Extraire les catégories de l'URL
                        categories = self.extract_categories_from_url(source_url)
                        
                        # Attribuer les catégories au nœud Content
                        if self.assign_categories_to_content(chunk_id, categories):
                            stats["updated"] += 1
                            
                            # Afficher un exemple de catégories extraites (pour les 10 premiers)
                            if stats["updated"] <= 10:
                                non_null_categories = {k: v for k, v in categories.items() if v is not None}
                                if non_null_categories:
                                    print(f"✓ {chunk_id[:50]}... -> {non_null_categories}")
                        else:
                            stats["errors"] += 1
                            
                    except Exception as e:
                        print(f"❌ Erreur lors du traitement de {chunk_id}: {e}")
                        stats["errors"] += 1
                
        except Exception as e:
            print(f"❌ Erreur lors du traitement des nœuds Content: {e}")
            stats["errors"] += 1
        
        return stats
    
    def get_category_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques sur les catégories attribuées"""
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                # Statistiques par niveau de catégorie
                stats = {}
                
                for level in range(1, 6):  # Statistiques pour les 5 premiers niveaux
                    result = session.run(f"""
                        MATCH (c:Content)
                        WHERE c.category_level_{level} IS NOT NULL
                        RETURN 
                            count(DISTINCT c.category_level_{level}) as unique_categories,
                            count(c) as total_content
                    """)
                    
                    record = result.single()
                    if record:
                        stats[f'level_{level}'] = {
                            'unique_categories': record['unique_categories'],
                            'total_content': record['total_content']
                        }
                
                # Top catégories par niveau
                top_categories = {}
                for level in range(1, 4):  # Top pour les 3 premiers niveaux
                    result = session.run(f"""
                        MATCH (c:Content)
                        WHERE c.category_level_{level} IS NOT NULL
                        WITH c.category_level_{level} as category, count(c) as count
                        ORDER BY count DESC
                        LIMIT 10
                        RETURN collect({{category: category, count: count}}) as top
                    """)
                    
                    record = result.single()
                    if record:
                        top_categories[f'level_{level}'] = record['top']
                
                stats['top_categories'] = top_categories
                
                return stats
                
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
    print("=" * 70)
    print("FH-SWF Category Assigner - Attribution de catégories aux nœuds Content")
    print("=" * 70)
    print(f"Neo4j URI:     {NEO4J_URI}")
    print(f"Neo4j User:    {NEO4J_USER}")
    print(f"Max levels:    {MAX_CATEGORY_LEVELS}")
    print("=" * 70)
    
    try:
        # Initialiser le gestionnaire de catégories
        assigner = CategoryAssigner(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        
        # Traiter tous les nœuds Content
        print("\n📋 Traitement des nœuds Content...")
        process_stats = assigner.process_all_content_nodes()
        print(f"✓ Nœuds traités: {process_stats['processed']}")
        print(f"✓ Nœuds mis à jour: {process_stats['updated']}")
        if process_stats['errors'] > 0:
            print(f"❌ Erreurs: {process_stats['errors']}")
        
        # Afficher les statistiques finales
        print("\n" + "=" * 70)
        print("📊 STATISTIQUES DES CATÉGORIES")
        print("=" * 70)
        
        category_stats = assigner.get_category_stats()
        if category_stats:
            for level in range(1, 6):
                level_key = f'level_{level}'
                if level_key in category_stats:
                    stats = category_stats[level_key]
                    print(f"Niveau {level}:")
                    print(f"  - Catégories uniques: {stats.get('unique_categories', 0)}")
                    print(f"  - Contenu total: {stats.get('total_content', 0)}")
            
            if 'top_categories' in category_stats:
                print("\n🏆 TOP CATÉGORIES:")
                for level in range(1, 4):
                    level_key = f'level_{level}'
                    if level_key in category_stats['top_categories']:
                        print(f"\nNiveau {level}:")
                        for item in category_stats['top_categories'][level_key][:5]:
                            print(f"  - {item['category']}: {item['count']} contenus")
        
        print("=" * 70)
        print("✅ Traitement terminé avec succès!")
        
        assigner.close()
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

