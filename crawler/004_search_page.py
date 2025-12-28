#!/usr/bin/env python3
"""
Script pour rechercher dans les nœuds Page avec Neo4j Vector Index.
- Permet à l'utilisateur d'entrer une requête
- Retourne les 20 pages les plus similaires via la recherche vectorielle
- Affiche les résultats avec les métadonnées et scores de similarité
"""

import os
import sys
from typing import List, Dict, Any, Optional

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

# Configuration de l'embedding (doit correspondre à celle utilisée dans 002_index_page.py)
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "intfloat/multilingual-e5-small")
EMBEDDING_MODEL_KWARGS = {"device": "cpu"}  # Utiliser "cuda" si GPU disponible
EMBED_ENCODE_KWARGS = {"normalize_embeddings": True}  # Normaliser pour la similarité cosinus

# Configuration de l'index vectoriel (doit correspondre à 002_index_page.py)
VECTOR_INDEX_NAME = os.getenv("VECTOR_INDEX_NAME", "page_vector_qwen_index")
EMBEDDING_NODE_PROPERTY = "embedding_e5"  # Nom de la propriété où l'embedding est stocké

# Nombre de résultats par défaut
DEFAULT_K = 20

class PageSearcher:
    """Gestionnaire pour rechercher dans les nœuds Page avec Neo4j Vector Index"""
    
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
        
        # Initialiser l'embedding (doit être le même que celui utilisé pour l'indexation)
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
        
        # Charger l'index vectoriel existant
        try:
            print(f"🔍 Chargement de l'index vectoriel: {VECTOR_INDEX_NAME}")
            # Spécifier text_node_property="markdown_content" car nos nœuds Page utilisent
            # markdown_content au lieu de "text" par défaut
            # Utiliser une retrieval_query personnalisée pour mapper markdown_content vers text
            retrieval_query = """
            RETURN node.markdown_content AS text, score, 
                   node {.*, markdown_content: Null, embedding_e5: Null, id: Null} AS metadata
            """
            self.vector_store = Neo4jVector.from_existing_index(
                embedding=self.embeddings,
                url=uri,
                username=user,
                password=password,
                index_name=VECTOR_INDEX_NAME,
                node_label="Page",
                text_node_property="markdown_content",  # Utiliser markdown_content au lieu de text
                embedding_node_property=EMBEDDING_NODE_PROPERTY,
                retrieval_query=retrieval_query,  # Requête personnalisée pour mapper markdown_content
            )
            print(f"✓ Index vectoriel chargé avec succès")
        except Exception as e:
            print(f"❌ Erreur lors du chargement de l'index: {e}")
            print(f"   Assurez-vous d'avoir exécuté 002_index_page.py au préalable")
            raise
    
    def search(self, query: str, k: int = DEFAULT_K) -> List[Dict[str, Any]]:
        """
        Recherche les documents les plus similaires à la requête.
        
        Args:
            query: La requête de recherche
            k: Nombre de résultats à retourner (défaut: 20)
        
        Returns:
            Liste de dictionnaires contenant les résultats avec scores
        """
        if not self.vector_store:
            raise ValueError("L'index vectoriel n'est pas initialisé")
        
        try:
            # Recherche avec scores de similarité
            results_with_scores = self.vector_store.similarity_search_with_score(query, k=k)
            
            # Formater les résultats
            formatted_results = []
            for i, (doc, score) in enumerate(results_with_scores, 1):
                # Extraire les métadonnées du document
                metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                
                # Extraire le contenu
                content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
                
                # Extraire les propriétés des nœuds Page depuis les métadonnées
                # Les métadonnées peuvent contenir les propriétés du nœud Neo4j
                url = metadata.get('url') or 'N/A'
                title = metadata.get('title') or 'N/A'
                meta_description = metadata.get('meta_description') or 'N/A'
                updated_at = metadata.get('updated_at') or 'N/A'
                
                result = {
                    'rank': i,
                    'score': float(score),
                    'content': content,
                    'metadata': metadata,
                    'url': url,
                    'title': title,
                    'meta_description': meta_description,
                    'updated_at': updated_at,
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Erreur lors de la recherche: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def display_results(self, results: List[Dict[str, Any]], query: str):
        """Affiche les résultats de recherche de manière formatée"""
        if not results:
            print(f"\n❌ Aucun résultat trouvé pour la requête: '{query}'")
            return
        
        print("\n" + "=" * 80)
        print(f"🔍 RÉSULTATS DE RECHERCHE POUR: '{query}'")
        print(f"📊 {len(results)} document(s) trouvé(s)")
        print("=" * 80)
        
        for result in results:
            print(f"\n{'─' * 80}")
            print(f"📄 Résultat #{result['rank']} (Score: {result['score']:.4f})")
            print(f"{'─' * 80}")
            print(f"📍 URL: {result['url']}")
            if result['title'] != 'N/A':
                print(f"📝 Titre: {result['title']}")
            if result['meta_description'] != 'N/A':
                print(f"📋 Description: {result['meta_description'][:200]}..." if len(result['meta_description']) > 200 else f"📋 Description: {result['meta_description']}")
            if result['updated_at'] != 'N/A':
                print(f"🕒 Mis à jour: {result['updated_at']}")
            print(f"\n📄 Contenu (markdown):")
            print(f"{'─' * 80}")
            
            # Afficher le contenu avec une limite de caractères
            content = result['content']
            max_length = 500
            if len(content) > max_length:
                print(f"{content[:max_length]}...")
                print(f"\n[... {len(content) - max_length} caractères supplémentaires ...]")
            else:
                print(content)
            
            # Afficher les métadonnées supplémentaires si disponibles
            if result['metadata']:
                other_metadata = {k: v for k, v in result['metadata'].items() 
                                if k not in ['url', 'title', 'meta_description', 'updated_at', 'markdown_content', 'embedding_e5', 'text_content']}
                if other_metadata:
                    print(f"\n📋 Métadonnées supplémentaires: {other_metadata}")
        
        print(f"\n{'─' * 80}")
        print(f"✅ Recherche terminée - {len(results)} résultat(s) affiché(s)")
        print(f"{'─' * 80}\n")
    
    def interactive_search(self):
        """Mode interactif pour rechercher du contenu"""
        print("\n" + "=" * 80)
        print("🔍 MODE RECHERCHE INTERACTIF")
        print("=" * 80)
        print("Entrez votre requête de recherche (ou 'quit'/'exit' pour quitter)")
        print("=" * 80)
        
        while True:
            try:
                # Demander la requête à l'utilisateur
                query = input("\n🔍 Votre requête: ").strip()
                
                if not query:
                    print("⚠️  Veuillez entrer une requête valide")
                    continue
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Au revoir!")
                    break
                
                # Demander le nombre de résultats (optionnel)
                k_input = input(f"📊 Nombre de résultats (défaut: {DEFAULT_K}): ").strip()
                k = int(k_input) if k_input.isdigit() else DEFAULT_K
                k = max(1, min(k, 100))  # Limiter entre 1 et 100
                
                # Effectuer la recherche
                print(f"\n⏳ Recherche en cours... (k={k})")
                results = self.search(query, k=k)
                
                # Afficher les résultats
                self.display_results(results, query)
                
            except KeyboardInterrupt:
                print("\n\n👋 Interruption - Au revoir!")
                break
            except Exception as e:
                print(f"\n❌ Erreur: {e}")
                import traceback
                traceback.print_exc()
    
    def close(self):
        """Ferme la connexion à Neo4j"""
        if self.driver:
            self.driver.close()
            print("✓ Connexion Neo4j fermée")

def main():
    """Fonction principale"""
    print("=" * 80)
    print("FH-SWF Page Searcher - Recherche vectorielle dans les Pages")
    print("=" * 80)
    print(f"Neo4j URI:           {NEO4J_URI}")
    print(f"Neo4j User:          {NEO4J_USER}")
    print(f"Modèle d'embedding:  {EMBEDDING_MODEL_NAME}")
    print(f"Index vectoriel:     {VECTOR_INDEX_NAME}")
    print(f"Résultats par défaut: {DEFAULT_K}")
    print("=" * 80)
    
    try:
        # Initialiser le chercheur
        searcher = PageSearcher(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        
        # Vérifier si une requête est fournie en argument
        if len(sys.argv) > 1:
            # Mode non-interactif: requête fournie en argument
            query = " ".join(sys.argv[1:])
            k_input = os.getenv("SEARCH_K", str(DEFAULT_K))
            k = int(k_input) if k_input.isdigit() else DEFAULT_K
            k = max(1, min(k, 100))
            
            print(f"\n🔍 Recherche pour: '{query}'")
            print(f"📊 Nombre de résultats: {k}")
            
            results = searcher.search(query, k=k)
            searcher.display_results(results, query)
        else:
            # Mode interactif
            searcher.interactive_search()
        
        searcher.close()
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

