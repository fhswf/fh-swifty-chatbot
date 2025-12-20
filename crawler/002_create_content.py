#!/usr/bin/env python3
"""
Script pour créer des nœuds Content à partir du contenu markdown des nœuds PDF et Page.
- Divise le contenu en chunks de maximum 2000 caractères
- Crée des nœuds Content avec les métadonnées appropriées
- Établit les relations avec les nœuds PDF/Page sources
"""

import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from neo4j import GraphDatabase

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# --- Configuration ---
load_dotenv()

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7689")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

# Configuration du chunking
MAX_CHUNK_SIZE = 5000
CHUNK_OVERLAP = 500  # Chevauchement entre chunks pour préserver le contexte
MIN_CONTENT_SIZE = 8000  # Seuil minimum pour diviser en chunks

class ContentChunker:
    """Gestionnaire pour créer des chunks de contenu à partir des nœuds PDF et Page"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            self.init_constraints()
            self.init_text_splitters()
            print(f"✓ Connexion à Neo4j établie: {uri}")
        except Exception as e:
            print(f"⚠️  Erreur de connexion à Neo4j: {e}")
            raise
    
    def init_constraints(self):
        """Crée les contraintes et index pour les nœuds Content"""
        if not self.driver:
            return
        
        with self.driver.session() as session:
            # Contraintes d'unicité
            constraints = [
                "CREATE CONSTRAINT content_unique IF NOT EXISTS FOR (c:Content) REQUIRE c.chunk_id IS UNIQUE",
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception:
                    # Contrainte peut déjà exister
                    pass
            
            # Index pour améliorer les performances
            indexes = [
                "CREATE INDEX content_type IF NOT EXISTS FOR (c:Content) ON (c.content_type)",
                "CREATE INDEX content_source_url IF NOT EXISTS FOR (c:Content) ON (c.source_url)",
                "CREATE INDEX content_chunk_order IF NOT EXISTS FOR (c:Content) ON (c.chunk_order)",
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                except Exception:
                    pass
    
    def init_text_splitters(self):
        """Initialise les splitters LangChain"""
        # Splitter général pour le texte
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=MAX_CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
    
    def split_content_into_chunks(self, content: str) -> List[Document]:
        """
        Divise le contenu en chunks en utilisant LangChain.
        """
        if not content or len(content.strip()) < MIN_CONTENT_SIZE:
            return [Document(page_content=content)] if content and content.strip() else []
        
        content = content.strip()
        
        try:
            return self.recursive_splitter.split_documents([Document(page_content=content)])    
        except Exception:
            return [Document(page_content=content)]
    
    def create_content_chunks(self, source_url: str, content: str, content_type: str, 
                            last_seen: str, source_title: str = "", source_meta: str = "") -> int:
        """
        Crée des nœuds Content à partir du contenu markdown.
        Retourne le nombre de chunks créés.
        """
        if not self.driver:
            return 0
        
        chunk_docs = self.split_content_into_chunks(content)
        
        print(f"📄 Création de {len(chunk_docs)} chunks pour {source_url} ({content_type})")
        
        try:
            with self.driver.session() as session:
                # Supprimer les anciens chunks pour cette source
                session.run("""
                    MATCH (c:Content {source_url: $source_url})
                    DETACH DELETE c
                """, source_url=source_url)
                
                # Créer les nouveaux chunks
                for i, doc in enumerate(chunk_docs):
                    chunk_id = f"{source_url}#chunk_{i+1}"
                    chunk_content = doc.page_content
                    chunk_metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                    
                    session.run("""
                        CREATE (c:Content {
                            chunk_id: $chunk_id,
                            source_url: $source_url,
                            content_type: $content_type,
                            chunk_content: $chunk_content,
                            chunk_order: $chunk_order,
                            chunk_size: $chunk_size,
                            total_chunks: $total_chunks,
                            last_seen: $last_seen,
                            source_title: $source_title,
                            source_meta: $source_meta,
                            chunk_metadata: $chunk_metadata
                        })
                    """, {
                        'chunk_id': chunk_id,
                        'source_url': source_url,
                        'content_type': content_type,
                        'chunk_content': chunk_content,
                        'chunk_order': i + 1,
                        'chunk_size': len(chunk_content),
                        'total_chunks': len(chunk_docs),
                        'last_seen': last_seen,
                        'source_title': source_title,
                        'source_meta': source_meta,
                        'chunk_metadata': str(chunk_metadata)
                    })
                
                # Créer les relations avec les nœuds sources
                if content_type == "pdf":
                    session.run("""
                        MATCH (pdf:PDF {url: $source_url})
                        MATCH (c:Content {source_url: $source_url})
                        MERGE (pdf)-[:HAS_CONTENT]->(c)
                    """, source_url=source_url)
                elif content_type == "webpage":
                    session.run("""
                        MATCH (page:Page {url: $source_url})
                        MATCH (c:Content {source_url: $source_url})
                        MERGE (page)-[:HAS_CONTENT]->(c)
                    """, source_url=source_url)
                
                return len(chunk_docs)
                
        except Exception as e:
            print(f"❌ Erreur lors de la création des chunks pour {source_url}: {e}")
            return 0
    
    def process_pdf_nodes(self) -> Dict[str, int]:
        """Traite tous les nœuds PDF et crée des chunks de contenu"""
        if not self.driver:
            return {"processed": 0, "chunks_created": 0, "errors": 0}
        
        stats = {"processed": 0, "chunks_created": 0, "errors": 0}
        
        try:
            with self.driver.session() as session:
                # Récupérer tous les nœuds PDF avec du contenu markdown
                result = session.run("""
                    MATCH (pdf:PDF)
                    WHERE pdf.markdown_content IS NOT NULL 
                    AND pdf.markdown_content <> ""
                    RETURN pdf.url as url, 
                           pdf.markdown_content as content,
                           pdf.file_name as title,
                           pdf.file_size as meta,
                           pdf.indexed_at as last_seen
                """)
                
                for record in result:
                    url = record["url"]
                    content = record["content"]
                    title = record["title"] or ""
                    meta = f"File size: {record['meta']} bytes" if record["meta"] else ""
                    last_seen = record["last_seen"]
                    
                    try:
                        chunks_created = self.create_content_chunks(
                            source_url=url,
                            content=content,
                            content_type="pdf",
                            source_title=title,
                            source_meta=meta,
                            last_seen=last_seen
                        )
                        stats["chunks_created"] += chunks_created
                        stats["processed"] += 1
                        
                        if chunks_created > 0:
                            print(f"✓ PDF: {title} -> {chunks_created} chunks")
                        
                    except Exception as e:
                        print(f"❌ Erreur PDF {url}: {e}")
                        stats["errors"] += 1
                
        except Exception as e:
            print(f"❌ Erreur lors du traitement des PDFs: {e}")
            stats["errors"] += 1
        
        return stats
    
    def process_page_nodes(self) -> Dict[str, int]:
        """Traite tous les nœuds Page et crée des chunks de contenu"""
        if not self.driver:
            return {"processed": 0, "chunks_created": 0, "errors": 0}
        
        stats = {"processed": 0, "chunks_created": 0, "errors": 0}
        
        try:
            with self.driver.session() as session:
                # Récupérer tous les nœuds Page avec du contenu markdown
                result = session.run("""
                    MATCH (page:Page)
                    WHERE page.markdown_content IS NOT NULL 
                    AND page.markdown_content <> ""
                    RETURN page.url as url, 
                           page.markdown_content as content,
                           page.updated_at as last_seen,
                           page.title as title,
                           page.meta_description as meta
                """)
                
                for record in result:
                    url = record["url"]
                    content = record["content"]
                    title = record["title"] or ""
                    meta = record["meta"] or ""
                    last_seen = record["last_seen"]
                    
                    try:
                        chunks_created = self.create_content_chunks(
                            source_url=url,
                            content=content,
                            content_type="webpage",
                            last_seen=last_seen,
                            source_title=title,
                            source_meta=meta
                        )
                        stats["chunks_created"] += chunks_created
                        stats["processed"] += 1
                        
                        if chunks_created > 0:
                            print(f"✓ Page: {title} -> {chunks_created} chunks")
                        
                    except Exception as e:
                        print(f"❌ Erreur Page {url}: {e}")
                        stats["errors"] += 1
                
        except Exception as e:
            print(f"❌ Erreur lors du traitement des Pages: {e}")
            stats["errors"] += 1
        
        return stats
    
    def get_content_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques des nœuds Content"""
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (c:Content)
                    RETURN 
                        count(c) as total_chunks,
                        count(DISTINCT c.source_url) as total_sources,
                        count(CASE WHEN c.content_type = 'pdf' THEN 1 END) as pdf_chunks,
                        count(CASE WHEN c.content_type = 'webpage' THEN 1 END) as webpage_chunks,
                        avg(c.chunk_size) as avg_chunk_size,
                        max(c.chunk_size) as max_chunk_size,
                        min(c.chunk_size) as min_chunk_size
                """)
                record = result.single()
                return {
                    'total_chunks': record['total_chunks'],
                    'total_sources': record['total_sources'],
                    'pdf_chunks': record['pdf_chunks'],
                    'webpage_chunks': record['webpage_chunks'],
                    'avg_chunk_size': round(record['avg_chunk_size'], 2) if record['avg_chunk_size'] else 0,
                    'max_chunk_size': record['max_chunk_size'],
                    'min_chunk_size': record['min_chunk_size']
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
    print("FH-SWF Content Chunker - Création de chunks de contenu")
    print("=" * 70)
    print(f"Neo4j URI:     {NEO4J_URI}")
    print(f"Neo4j User:    {NEO4J_USER}")
    print(f"Max chunk size: {MAX_CHUNK_SIZE} caractères")
    print(f"Chunk overlap: {CHUNK_OVERLAP} caractères")
    print(f"Min content size: {MIN_CONTENT_SIZE} caractères")
    print("=" * 70)
    
    try:
        # Initialiser le chunker
        chunker = ContentChunker(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        
        # Traiter les nœuds PDF
        print("\n📄 Traitement des nœuds PDF...")
        pdf_stats = chunker.process_pdf_nodes()
        print(f"✓ PDFs traités: {pdf_stats['processed']}")
        print(f"✓ Chunks créés: {pdf_stats['chunks_created']}")
        if pdf_stats['errors'] > 0:
            print(f"❌ Erreurs: {pdf_stats['errors']}")
        
        # Traiter les nœuds Page
        print("\n🌐 Traitement des nœuds Page...")
        page_stats = chunker.process_page_nodes()
        print(f"✓ Pages traitées: {page_stats['processed']}")
        print(f"✓ Chunks créés: {page_stats['chunks_created']}")
        if page_stats['errors'] > 0:
            print(f"❌ Erreurs: {page_stats['errors']}")
        
        # Afficher les statistiques finales
        print("\n" + "=" * 70)
        print("📊 STATISTIQUES FINALES")
        print("=" * 70)
        
        content_stats = chunker.get_content_stats()
        if content_stats:
            print(f"Total chunks:        {content_stats.get('total_chunks', 0)}")
            print(f"Sources traitées:    {content_stats.get('total_sources', 0)}")
            print(f"Chunks PDF:          {content_stats.get('pdf_chunks', 0)}")
            print(f"Chunks Webpage:      {content_stats.get('webpage_chunks', 0)}")
            print(f"Taille moyenne:     {content_stats.get('avg_chunk_size', 0)} caractères")
            print(f"Taille max:          {content_stats.get('max_chunk_size', 0)} caractères")
            print(f"Taille min:          {content_stats.get('min_chunk_size', 0)} caractères")
        
        print("=" * 70)
        print("✅ Traitement terminé avec succès!")
        
        chunker.close()
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
