#!/usr/bin/env python3
"""
Script pour créer des nœuds Content à partir du contenu markdown des nœuds PDF et Page.
- Divise le contenu en chunks de maximum 2000 caractères
- Crée des nœuds Content avec les métadonnées appropriées
- Établit les relations avec les nœuds PDF/Page sources
"""

import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from dotenv import load_dotenv
from neo4j import GraphDatabase

# --- Configuration ---
load_dotenv()

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

# Configuration du chunking
MAX_CHUNK_SIZE = 2000
MIN_CONTENT_SIZE = 3000  # Seuil minimum pour diviser en chunks

class ContentChunker:
    """Gestionnaire pour créer des chunks de contenu à partir des nœuds PDF et Page"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            self.init_constraints()
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
    
    def split_content_into_chunks(self, content: str, max_size: int = MAX_CHUNK_SIZE) -> List[str]:
        """
        Divise le contenu en chunks de taille maximale spécifiée.
        Essaie de couper aux limites de phrases/paragraphes.
        """
        if not content or len(content.strip()) < MIN_CONTENT_SIZE:
            return [content] if content and content.strip() else []
        
        content = content.strip()
        chunks = []
        
        # Diviser par paragraphes d'abord
        paragraphs = content.split('\n\n')
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Si le paragraphe seul dépasse la taille max, le diviser par phrases
            if len(paragraph) > max_size:
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    if len(current_chunk) + len(sentence) + 2 <= max_size:
                        current_chunk += ("\n" if current_chunk else "") + sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence
            else:
                # Vérifier si on peut ajouter ce paragraphe au chunk actuel
                if len(current_chunk) + len(paragraph) + 2 <= max_size:
                    current_chunk += ("\n\n" if current_chunk else "") + paragraph
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph
        
        # Ajouter le dernier chunk s'il n'est pas vide
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return [chunk for chunk in chunks if chunk]
    
    def create_content_chunks(self, source_url: str, content: str, content_type: str, 
                            source_title: str = "", source_meta: str = "") -> int:
        """
        Crée des nœuds Content à partir du contenu markdown.
        Retourne le nombre de chunks créés.
        """
        if not self.driver:
            return 0
        
        chunks = self.split_content_into_chunks(content)
        if not chunks:
            print(f"⚠️  Aucun chunk créé pour {source_url}")
            return 0
        
        print(f"📄 Création de {len(chunks)} chunks pour {source_url} ({content_type})")
        
        try:
            with self.driver.session() as session:
                # Supprimer les anciens chunks pour cette source
                session.run("""
                    MATCH (c:Content {source_url: $source_url})
                    DETACH DELETE c
                """, source_url=source_url)
                
                # Créer les nouveaux chunks
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{source_url}#chunk_{i+1}"
                    
                    session.run("""
                        CREATE (c:Content {
                            chunk_id: $chunk_id,
                            source_url: $source_url,
                            content_type: $content_type,
                            chunk_content: $chunk_content,
                            chunk_order: $chunk_order,
                            chunk_size: $chunk_size,
                            total_chunks: $total_chunks,
                            source_title: $source_title,
                            source_meta: $source_meta,
                            created_at: datetime(),
                            updated_at: datetime()
                        })
                    """, {
                        'chunk_id': chunk_id,
                        'source_url': source_url,
                        'content_type': content_type,
                        'chunk_content': chunk,
                        'chunk_order': i + 1,
                        'chunk_size': len(chunk),
                        'total_chunks': len(chunks),
                        'source_title': source_title,
                        'source_meta': source_meta
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
                
                return len(chunks)
                
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
                           pdf.file_size as meta
                """)
                
                for record in result:
                    url = record["url"]
                    content = record["content"]
                    title = record["title"] or ""
                    meta = f"File size: {record['meta']} bytes" if record["meta"] else ""
                    
                    try:
                        chunks_created = self.create_content_chunks(
                            source_url=url,
                            content=content,
                            content_type="pdf",
                            source_title=title,
                            source_meta=meta
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
                           page.title as title,
                           page.meta_description as meta
                """)
                
                for record in result:
                    url = record["url"]
                    content = record["content"]
                    title = record["title"] or ""
                    meta = record["meta"] or ""
                    
                    try:
                        chunks_created = self.create_content_chunks(
                            source_url=url,
                            content=content,
                            content_type="webpage",
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
                    RETURN 
                        count{(:Content)} as total_chunks,
                        count{DISTINCT (:Content).source_url} as total_sources,
                        count{(:Content) WHERE content_type = 'pdf'} as pdf_chunks,
                        count{(:Content) WHERE content_type = 'webpage'} as webpage_chunks,
                        avg{(:Content).chunk_size} as avg_chunk_size,
                        max{(:Content).chunk_size} as max_chunk_size,
                        min{(:Content).chunk_size} as min_chunk_size
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
