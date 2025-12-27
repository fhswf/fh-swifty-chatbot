#!/usr/bin/env python3
"""
Script pour indexer le contenu des nœuds Page avec Neo4j Vector Index.
- Utilise un embedding open source (SentenceTransformers) au lieu d'OpenAI
- Indexe la propriété markdown_content des nœuds Page
- Crée un index vectoriel pour la recherche de similarité
"""

import os
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from neo4j import GraphDatabase

# LangChain imports
from langchain_neo4j import Neo4jVector
from langchain_huggingface import HuggingFaceEmbeddings

# --- Configuration ---
load_dotenv()

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7689")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

# Configuration de l'embedding
# Utilisation d'un modèle open source multilingue pour supporter l'allemand
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "Qwen/Qwen3-Embedding-0.6B")
EMBEDDING_MODEL_KWARGS = {"device": "cpu"}  # Utiliser "cuda" si GPU disponible
EMBED_ENCODE_KWARGS = {"normalize_embeddings": True}  # Normaliser pour la similarité cosinus

# Configuration de l'index vectoriel
VECTOR_INDEX_NAME = os.getenv("VECTOR_INDEX_NAME", "page_vector_qwen_index")
KEYWORD_INDEX_NAME = os.getenv("KEYWORD_INDEX_NAME", "page_keyword")  # Index de mots-clés spécifique aux Pages
EMBEDDING_NODE_PROPERTY = "embedding_qwen"  # Nom de la propriété où stocker l'embedding

class PageIndexer:
    """Gestionnaire pour indexer les pages avec Neo4j Vector Index"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = None
        self.embeddings = None
        self.vector_store = None
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            print(f"✓ Connexion à Neo4j établie: {uri}")
        except Exception as e:
            print(f"⚠️  Erreur de connexion à Neo4j: {e}")
            raise
        
        # Initialiser l'embedding open source
        try:
            print(f"📦 Chargement du modèle d'embedding: {EMBEDDING_MODEL_NAME}")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL_NAME,
                model_kwargs=EMBEDDING_MODEL_KWARGS,
                encode_kwargs=EMBED_ENCODE_KWARGS
            )
            print(f"✓ Modèle d'embedding chargé")
        except Exception as e:
            print(f"❌ Erreur lors du chargement du modèle d'embedding: {e}")
            raise
    
    def check_page_nodes(self) -> Dict[str, Any]:
        """Vérifie les nœuds Page disponibles"""
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (p:Page)
                    WHERE p.markdown_content IS NOT NULL 
                    AND p.markdown_content <> ""
                    RETURN 
                        count(p) as total_page_nodes,
                        count(DISTINCT p.url) as total_sources,
                        avg(size(p.markdown_content)) as avg_content_length,
                        count(CASE WHEN p.embedding_qwen IS NOT NULL THEN 1 END) as already_indexed
                """)
                record = result.single()
                return {
                    'total_page_nodes': record['total_page_nodes'],
                    'total_sources': record['total_sources'],
                    'avg_content_length': round(record['avg_content_length'], 2) if record['avg_content_length'] else 0,
                    'already_indexed': record['already_indexed']
                }
        except Exception as e:
            print(f"❌ Erreur lors de la vérification des nœuds Page: {e}")
            return {}
    
    def index_pages(self) -> Dict[str, Any]:
        """
        Indexe le contenu des nœuds Page en utilisant Neo4jVector.from_existing_graph.
        Cette méthode lit les nœuds Page existants, calcule les embeddings et les stocke.
        """
        if not self.driver or not self.embeddings:
            return {"indexed": 0, "errors": 0}
        
        stats = {"indexed": 0, "errors": 0}
        
        try:
            print(f"🔍 Indexation des nœuds Page avec l'index: {VECTOR_INDEX_NAME}")
            print(f"   Propriété de texte: markdown_content")
            print(f"   Propriété d'embedding: {EMBEDDING_NODE_PROPERTY}")
            
            # Utiliser from_existing_graph pour indexer les nœuds Page existants
            # Cette méthode:
            # 1. Lit les nœuds Page avec markdown_content
            # 2. Calcule les embeddings pour chaque markdown_content
            # 3. Stocke les embeddings dans la propriété embedding_node_property
            # 4. Crée un index vectoriel Neo4j
            # Note: Utiliser un index de mots-clés spécifique pour éviter les conflits
            self.vector_store = Neo4jVector.from_existing_graph(
                embedding=self.embeddings,
                url=NEO4J_URI,
                username=NEO4J_USER,
                password=NEO4J_PASSWORD,
                index_name=VECTOR_INDEX_NAME,
                keyword_index_name=KEYWORD_INDEX_NAME,  # Index de mots-clés spécifique aux Pages
                search_type="hybrid",
                node_label="Page",
                text_node_properties=["markdown_content"],  # Propriété à indexer
                embedding_node_property=EMBEDDING_NODE_PROPERTY,  # Où stocker l'embedding
            )
            
            # Vérifier combien de nœuds ont été indexés
            page_stats = self.check_page_nodes()
            stats["indexed"] = page_stats.get("already_indexed", 0)
            
            print(f"✓ Index vectoriel créé avec succès")
            print(f"✓ {stats['indexed']} nœuds Page indexés")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'indexation: {e}")
            stats["errors"] = 1
            import traceback
            traceback.print_exc()
        
        return stats
    
    def test_similarity_search(self, query: str = "Studium", k: int = 3) -> list:
        """Teste la recherche de similarité avec une requête"""
        if not self.vector_store:
            print("⚠️  L'index vectoriel n'est pas initialisé")
            return []
        
        try:
            print(f"\n🔍 Test de recherche de similarité:")
            print(f"   Requête: '{query}'")
            print(f"   Nombre de résultats: {k}")
            
            results = self.vector_store.similarity_search(query, k=k)
            
            print(f"\n✓ {len(results)} résultats trouvés:")
            for i, doc in enumerate(results, 1):
                print(f"\n--- Résultat {i} ---")
                # Extraire le contenu et les métadonnées
                content = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                print(f"Contenu: {content}")
                if doc.metadata:
                    print(f"Métadonnées: {doc.metadata}")
            
            return results
            
        except Exception as e:
            print(f"❌ Erreur lors de la recherche de similarité: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de l'index vectoriel"""
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                # Vérifier si l'index existe
                index_check = session.run("""
                    SHOW INDEXES
                    YIELD name, type, state, populationPercent
                    WHERE name = $index_name
                    RETURN name, type, state, populationPercent
                """, index_name=VECTOR_INDEX_NAME)
                
                index_info = index_check.single()
                
                # Statistiques des nœuds indexés
                page_stats = self.check_page_nodes()
                
                return {
                    'index_name': index_info['name'] if index_info else None,
                    'index_type': index_info['type'] if index_info else None,
                    'index_state': index_info['state'] if index_info else None,
                    'population_percent': index_info['populationPercent'] if index_info else None,
                    **page_stats
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
    print("=" * 70)
    print("FH-SWF Page Indexer - Indexation vectorielle avec Neo4j")
    print("=" * 70)
    print(f"Neo4j URI:           {NEO4J_URI}")
    print(f"Neo4j User:           {NEO4J_USER}")
    print(f"Modèle d'embedding:  {EMBEDDING_MODEL_NAME}")
    print(f"Index vectoriel:     {VECTOR_INDEX_NAME}")
    print(f"Propriété texte:     markdown_content")
    print(f"Propriété embedding: {EMBEDDING_NODE_PROPERTY}")
    print("=" * 70)
    
    try:
        # Initialiser l'indexeur
        indexer = PageIndexer(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        
        # Vérifier les nœuds Page disponibles
        print("\n📊 Vérification des nœuds Page...")
        page_stats = indexer.check_page_nodes()
        if page_stats:
            print(f"✓ Nœuds Page disponibles: {page_stats.get('total_page_nodes', 0)}")
            print(f"✓ Sources distinctes: {page_stats.get('total_sources', 0)}")
            print(f"✓ Taille moyenne du contenu: {page_stats.get('avg_content_length', 0)} caractères")
            print(f"✓ Déjà indexés: {page_stats.get('already_indexed', 0)}")
        
        if page_stats.get('total_page_nodes', 0) == 0:
            print("\n⚠️  Aucun nœud Page trouvé. Exécutez d'abord 001_crawl_to_db.py")
            indexer.close()
            return 1
        
        # Indexer les pages
        print("\n🔍 Indexation des pages...")
        index_stats = indexer.index_pages()
        
        if index_stats.get("errors", 0) > 0:
            print(f"❌ Erreurs lors de l'indexation: {index_stats['errors']}")
        else:
            print(f"✓ Indexation terminée avec succès")
        
        # Afficher les statistiques de l'index
        print("\n" + "=" * 70)
        print("📊 STATISTIQUES DE L'INDEX")
        print("=" * 70)
        
        index_stats_final = indexer.get_index_stats()
        if index_stats_final:
            if index_stats_final.get('index_name'):
                print(f"Nom de l'index:        {index_stats_final.get('index_name')}")
                print(f"Type:                  {index_stats_final.get('index_type')}")
                print(f"État:                  {index_stats_final.get('index_state')}")
                if index_stats_final.get('population_percent') is not None:
                    print(f"Population:            {index_stats_final.get('population_percent')}%")
            print(f"Nœuds indexés:          {index_stats_final.get('already_indexed', 0)}")
            print(f"Total nœuds Page:       {index_stats_final.get('total_page_nodes', 0)}")
            print(f"Sources distinctes:     {index_stats_final.get('total_sources', 0)}")
        
        # Test de recherche de similarité
        print("\n" + "=" * 70)
        print("🧪 TEST DE RECHERCHE DE SIMILARITÉ")
        print("=" * 70)
        
        test_query = "Studium"
        indexer.test_similarity_search(test_query, k=3)
        
        print("\n" + "=" * 70)
        print("✅ Indexation terminée avec succès!")
        print("=" * 70)
        
        indexer.close()
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

