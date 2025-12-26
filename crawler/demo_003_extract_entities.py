#!/usr/bin/env python3
"""
Script pour extraire des entités et relations à partir des nœuds Content.
- Utilise l'API OpenAI via langchain-openai pour l'extraction d'entités
- Lit chunk_content et source_url des nœuds Content
- Crée des nœuds Entity et des relationships dans Neo4j
- Basé sur l'ontologie publique de l'université
"""

import os
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from dotenv import load_dotenv
from neo4j import GraphDatabase

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# --- Configuration ---
load_dotenv()

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7689")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))

# Configuration du traitement
BATCH_SIZE = int(os.getenv("ENTITY_BATCH_SIZE", "10"))  # Nombre de chunks à traiter par batch
MAX_CHUNKS_PER_RUN = int(os.getenv("MAX_CHUNKS_PER_RUN", "100"))  # Limite pour éviter les coûts
SKIP_ALREADY_PROCESSED = os.getenv("SKIP_ALREADY_PROCESSED", "true").lower() in ["true", "1", "yes"]

# --- Modèles Pydantic pour la structure de sortie ---

class EntityProperty(BaseModel):
    """Propriété d'une entité"""
    name: str = Field(description="Nom de la propriété")
    value: str = Field(description="Valeur de la propriété")
    type: str = Field(default="String", description="Type de la propriété (String, Integer, Float, Date, Boolean)")

class Entity(BaseModel):
    """Entité extraite du texte"""
    entity_id: str = Field(description="Identifiant unique de l'entité (généré ou dérivé du nom)")
    entity_type: str = Field(description="Type d'entité selon l'ontologie (ex: Hochschule, Studiengang, Fachbereich, etc.)")
    name: str = Field(description="Nom de l'entité")
    properties: List[EntityProperty] = Field(default_factory=list, description="Propriétés de l'entité")
    confidence: float = Field(default=0.8, description="Niveau de confiance (0.0-1.0)")

class Relationship(BaseModel):
    """Relation entre deux entités"""
    source_entity_id: str = Field(description="ID de l'entité source")
    target_entity_id: str = Field(description="ID de l'entité cible")
    relationship_type: str = Field(description="Type de relation (ex: GEHOERT_ZU, BIETET_AN, HAT_STANDORT, etc.)")
    properties: List[EntityProperty] = Field(default_factory=list, description="Propriétés de la relation")
    confidence: float = Field(default=0.8, description="Niveau de confiance (0.0-1.0)")

class EntityExtractionResult(BaseModel):
    """Résultat de l'extraction d'entités et relations"""
    entities: List[Entity] = Field(default_factory=list, description="Liste des entités extraites")
    relationships: List[Relationship] = Field(default_factory=list, description="Liste des relations extraites")
    confidence: float = Field(default=0.8, description="Confiance globale de l'extraction")

# --- Prompt Template ---

EXTRACTION_PROMPT = """Du bist ein Experte für die Extraktion von Entitäten und Beziehungen aus Universitäts-Texten.

Analysiere den folgenden Text und extrahiere alle relevanten Entitäten und Beziehungen gemäß der Ontologie für öffentliche Universitäts-Informationen.

**Wichtige Entitätstypen:**
- Hochschule, Standort, Campus, Gebäude
- Fachbereich, Institut, Serviceeinrichtung, Bibliothek, Mensa
- Studiengang, Modul, Studienrichtung
- Zulassungsvoraussetzung, Bewerbungsfrist, Bewerbungsverfahren, Numerus Clausus
- Professor, Dozent, Kontaktperson
- Öffentliche Veranstaltung, Vortrag, Tag der offenen Tür
- News-Artikel, Pressemitteilung
- Forschungsprojekt, Forschungsgebiet, Publikation
- FAQ-Eintrag, Hilfeartikel, Anleitung
- Öffentliches Formular, Öffentliches Dokument, Broschüre
- Studienberatung, Kontaktformular
- Studentenleben, Studentenverein, Wohnheim
- Stellenausschreibung, Karrieremöglichkeit
- Partnerorganisation, Austauschprogramm
- Semesterbeitrag, Studiengebühr, Gebührenordnung, Stipendium, Finanzierungsmöglichkeit

**Wichtige Beziehungstypen:**
- HAT_STANDORT, HAT_CAMPUS, BEFINDET_SICH_AUF
- GEHOERT_ZU, IST_TEIL_VON
- BIETET_AN, HAT_MODUL, HAT_RICHTUNG
- ERFORDERT, HAT_BEWERBUNGSFRIST, HAT_NC
- ARBEITET_IN, LEITET, IST_KONTAKTPERSON_FUER
- ORGANISIERT, FINDET_STATT_IM, RICHTET_SICH_AN
- FORSCHT_IN, DURCHFUEHRT, PUBLIZIERT
- BIETET_SERVICE, IST_VERFÜGBAR_AN
- ERHEBT, BESTEHT_AUS, HAT_GEBUEHR
- REGELT, BIETET_STIPENDIUM, AKZEPTIERT

**Text zu analysieren:**
{text}

**Quelle (URL):**
{source_url}

Extrahiere alle relevanten Entitäten und Beziehungen. Verwende deutsche Begriffe für die Entitätstypen und Beziehungstypen.
Für entity_id, verwende einen eindeutigen Identifier basierend auf dem Namen (z.B. "hochschule_fh_suedwestfalen" oder "studiengang_informatik_bachelor").

Antworte im JSON-Format entsprechend dem Schema.
"""

class EntityExtractor:
    """Gestionnaire pour extraire des entités et relations depuis le contenu"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = None
        self.llm = None
        self.parser = None
        
        # Connexion Neo4j
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            self.init_constraints()
            print(f"✓ Connexion à Neo4j établie: {uri}")
        except Exception as e:
            print(f"⚠️  Erreur de connexion à Neo4j: {e}")
            raise
        
        # Initialiser OpenAI
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY n'est pas défini dans les variables d'environnement")
        
        try:
            self.llm = ChatOpenAI(
                model=OPENAI_MODEL,
                temperature=OPENAI_TEMPERATURE,
                api_key=OPENAI_API_KEY
            )
            self.parser = PydanticOutputParser(pydantic_object=EntityExtractionResult)
            print(f"✓ Modèle OpenAI initialisé: {OPENAI_MODEL}")
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation d'OpenAI: {e}")
            raise
    
    def init_constraints(self):
        """Crée les contraintes et index pour les nœuds Entity"""
        if not self.driver:
            return
        
        with self.driver.session() as session:
            # Contraintes d'unicité
            constraints = [
                "CREATE CONSTRAINT entity_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE",
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception:
                    pass
            
            # Index pour améliorer les performances
            indexes = [
                "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.entity_type)",
                "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
                "CREATE INDEX content_processed IF NOT EXISTS FOR (c:Content) ON (c.entities_extracted)",
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                except Exception:
                    pass
    
    def extract_entities_from_text(self, text: str, source_url: str) -> Optional[EntityExtractionResult]:
        """Extrait les entités et relations d'un texte en utilisant OpenAI"""
        if not self.llm or not text or len(text.strip()) < 100:
            return None
        
        try:
            # Créer le prompt avec le format attendu
            prompt = ChatPromptTemplate.from_template(EXTRACTION_PROMPT + "\n\n{format_instructions}")
            format_instructions = self.parser.get_format_instructions()
            messages = prompt.format_messages(
                text=text[:8000],  # Limiter à 8000 caractères
                source_url=source_url,
                format_instructions=format_instructions
            )
            
            # Appeler OpenAI
            response = self.llm.invoke(messages)
            
            # Parser la réponse
            try:
                result = self.parser.parse(response.content)
                return result
            except Exception as parse_error:
                # Si le parsing échoue, essayer d'extraire le JSON manuellement
                print(f"⚠️  Erreur de parsing, tentative d'extraction manuelle: {parse_error}")
                content = response.content
                
                # Essayer d'extraire le JSON entre ```json et ```
                json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # Essayer d'extraire juste le JSON
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                    else:
                        json_str = content
                
                try:
                    data = json.loads(json_str)
                    result = EntityExtractionResult(**data)
                    return result
                except Exception:
                    print(f"⚠️  Impossible de parser la réponse JSON")
                    return None
            
        except Exception as e:
            print(f"⚠️  Erreur lors de l'extraction pour {source_url}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def create_entity_node(self, entity: Entity, source_url: str) -> bool:
        """Crée un nœud Entity dans Neo4j"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                # Créer l'entité avec toutes ses propriétés
                properties_dict = {
                    "entity_id": entity.entity_id,
                    "entity_type": entity.entity_type,
                    "name": entity.name,
                    "confidence": entity.confidence,
                    "extracted_at": datetime.now().isoformat(),
                    "source_url": source_url
                }
                
                # Ajouter les propriétés dynamiques
                for prop in entity.properties:
                    properties_dict[prop.name] = prop.value
                
                # Créer le nœud
                query = f"""
                    MERGE (e:Entity {{entity_id: $entity_id}})
                    SET e += $properties
                """
                
                session.run(query, {
                    "entity_id": entity.entity_id,
                    "properties": properties_dict
                })
                
                return True
                
        except Exception as e:
            print(f"❌ Erreur lors de la création de l'entité {entity.entity_id}: {e}")
            return False
    
    def create_relationship(self, relationship: Relationship, source_url: str) -> bool:
        """Crée une relation entre deux entités dans Neo4j"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                # Vérifier que les deux entités existent
                check_query = """
                    MATCH (source:Entity {entity_id: $source_id})
                    MATCH (target:Entity {entity_id: $target_id})
                    RETURN count(*) as count
                """
                result = session.run(check_query, {
                    "source_id": relationship.source_entity_id,
                    "target_id": relationship.target_entity_id
                })
                
                if result.single()["count"] == 0:
                    # Au moins une entité n'existe pas
                    return False
                
                # Créer la relation avec propriétés
                rel_properties = {
                    "confidence": relationship.confidence,
                    "extracted_at": datetime.now().isoformat(),
                    "source_url": source_url
                }
                
                for prop in relationship.properties:
                    rel_properties[prop.name] = prop.value
                
                # Créer la relation (utiliser le type de relation comme label)
                # Note: Neo4j nécessite que le type de relation soit dans la requête, pas en paramètre
                rel_type = relationship.relationship_type
                # Nettoyer le type de relation pour éviter les caractères invalides
                rel_type_clean = rel_type.replace(" ", "_").replace("-", "_").upper()
                
                # Construire la requête avec le type de relation
                query = f"""
                    MATCH (source:Entity {{entity_id: $source_id}})
                    MATCH (target:Entity {{entity_id: $target_id}})
                    MERGE (source)-[r:`{rel_type_clean}`]->(target)
                    SET r += $properties
                """
                
                session.run(query, {
                    "source_id": relationship.source_entity_id,
                    "target_id": relationship.target_entity_id,
                    "properties": rel_properties
                })
                
                return True
                
        except Exception as e:
            print(f"❌ Erreur lors de la création de la relation {relationship.relationship_type}: {e}")
            return False
    
    def link_content_to_entities(self, content_chunk_id: str, entity_ids: List[str]):
        """Crée des relations entre un Content et les entités extraites"""
        if not self.driver or not entity_ids:
            return
        
        try:
            with self.driver.session() as session:
                for entity_id in entity_ids:
                    session.run("""
                        MATCH (c:Content {chunk_id: $chunk_id})
                        MATCH (e:Entity {entity_id: $entity_id})
                        MERGE (c)-[:MENTIONS]->(e)
                    """, {
                        "chunk_id": content_chunk_id,
                        "entity_id": entity_id
                    })
        except Exception as e:
            print(f"⚠️  Erreur lors de la liaison Content-Entity: {e}")
    
    def mark_content_as_processed(self, chunk_id: str):
        """Marque un Content comme traité"""
        if not self.driver:
            return
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (c:Content {chunk_id: $chunk_id})
                    SET c.entities_extracted = true,
                        c.entities_extracted_at = datetime()
                """, chunk_id=chunk_id)
        except Exception as e:
            print(f"⚠️  Erreur lors du marquage: {e}")
    
    def process_content_chunks(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Traite les nœuds Content et extrait les entités"""
        if not self.driver:
            return {"processed": 0, "entities_created": 0, "relationships_created": 0, "errors": 0}
        
        stats = {
            "processed": 0,
            "entities_created": 0,
            "relationships_created": 0,
            "errors": 0,
            "skipped": 0
        }
        
        try:
            with self.driver.session() as session:
                # Construire la requête pour récupérer les Content
                query = """
                    MATCH (c:Content)
                    WHERE c.chunk_content IS NOT NULL 
                    AND c.chunk_content <> ""
                """
                
                if SKIP_ALREADY_PROCESSED:
                    query += " AND (c.entities_extracted IS NULL OR c.entities_extracted = false)"
                
                query += """
                    RETURN c.chunk_id as chunk_id,
                           c.chunk_content as chunk_content,
                           c.source_url as source_url
                    ORDER BY c.chunk_order
                """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                result = session.run(query)
                
                chunks = list(result)
                total_chunks = len(chunks)
                print(f"📊 {total_chunks} chunks à traiter")
                
                for i, record in enumerate(chunks, 1):
                    chunk_id = record["chunk_id"]
                    chunk_content = record["chunk_content"]
                    source_url = record["source_url"]
                    
                    print(f"\n[{i}/{total_chunks}] Traitement: {chunk_id[:60]}...")
                    
                    try:
                        # Extraire les entités et relations
                        extraction_result = self.extract_entities_from_text(chunk_content, source_url)
                        
                        if not extraction_result:
                            stats["skipped"] += 1
                            continue
                        
                        entity_ids = []
                        
                        # Créer les entités
                        for entity in extraction_result.entities:
                            if self.create_entity_node(entity, source_url):
                                entity_ids.append(entity.entity_id)
                                stats["entities_created"] += 1
                        
                        # Créer les relations
                        for relationship in extraction_result.relationships:
                            if self.create_relationship(relationship, source_url):
                                stats["relationships_created"] += 1
                        
                        # Lier le Content aux entités
                        if entity_ids:
                            self.link_content_to_entities(chunk_id, entity_ids)
                        
                        # Marquer comme traité
                        self.mark_content_as_processed(chunk_id)
                        
                        stats["processed"] += 1
                        
                        print(f"  ✓ {len(extraction_result.entities)} entités, {len(extraction_result.relationships)} relations")
                        
                    except Exception as e:
                        print(f"  ❌ Erreur: {e}")
                        stats["errors"] += 1
                        import traceback
                        traceback.print_exc()
                
        except Exception as e:
            print(f"❌ Erreur lors du traitement: {e}")
            stats["errors"] += 1
            import traceback
            traceback.print_exc()
        
        return stats
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques des entités et relations"""
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                # Statistiques des entités
                entity_stats = session.run("""
                    MATCH (e:Entity)
                    RETURN 
                        count(e) as total_entities,
                        count(DISTINCT e.entity_type) as entity_types_count,
                        collect(DISTINCT e.entity_type) as entity_types
                """).single()
                
                # Statistiques des relations
                rel_stats = session.run("""
                    MATCH ()-[r]->()
                    WHERE type(r) <> 'HAS_CONTENT' AND type(r) <> 'MENTIONS'
                    RETURN 
                        count(r) as total_relationships,
                        count(DISTINCT type(r)) as relationship_types_count,
                        collect(DISTINCT type(r)) as relationship_types
                """).single()
                
                # Statistiques Content
                content_stats = session.run("""
                    MATCH (c:Content)
                    RETURN 
                        count(c) as total_content,
                        count(CASE WHEN c.entities_extracted = true THEN 1 END) as processed_content
                """).single()
                
                return {
                    "total_entities": entity_stats["total_entities"],
                    "entity_types_count": entity_stats["entity_types_count"],
                    "entity_types": entity_stats["entity_types"],
                    "total_relationships": rel_stats["total_relationships"],
                    "relationship_types_count": rel_stats["relationship_types_count"],
                    "relationship_types": rel_stats["relationship_types"],
                    "total_content": content_stats["total_content"],
                    "processed_content": content_stats["processed_content"]
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
    print("FH-SWF Entity Extractor - Extraction d'entités avec OpenAI")
    print("=" * 70)
    print(f"Neo4j URI:           {NEO4J_URI}")
    print(f"Neo4j User:           {NEO4J_USER}")
    print(f"OpenAI Model:        {OPENAI_MODEL}")
    print(f"Temperature:         {OPENAI_TEMPERATURE}")
    print(f"Batch Size:          {BATCH_SIZE}")
    print(f"Max Chunks:          {MAX_CHUNKS_PER_RUN}")
    print(f"Skip Processed:      {SKIP_ALREADY_PROCESSED}")
    print("=" * 70)
    
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY n'est pas défini!")
        return 1
    
    try:
        # Initialiser l'extracteur
        extractor = EntityExtractor(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        
        # Afficher les statistiques initiales
        print("\n📊 Statistiques initiales...")
        initial_stats = extractor.get_stats()
        if initial_stats:
            print(f"✓ Entités existantes: {initial_stats.get('total_entities', 0)}")
            print(f"✓ Relations existantes: {initial_stats.get('total_relationships', 0)}")
            print(f"✓ Content total: {initial_stats.get('total_content', 0)}")
            print(f"✓ Content traité: {initial_stats.get('processed_content', 0)}")
        
        # Traiter les chunks
        print(f"\n🔍 Extraction d'entités et relations...")
        print(f"   Limite: {MAX_CHUNKS_PER_RUN} chunks")
        
        stats = extractor.process_content_chunks(limit=MAX_CHUNKS_PER_RUN)
        
        # Afficher les résultats
        print("\n" + "=" * 70)
        print("📊 RÉSULTATS DE L'EXTRACTION")
        print("=" * 70)
        print(f"Chunks traités:        {stats['processed']}")
        print(f"Entités créées:        {stats['entities_created']}")
        print(f"Relations créées:      {stats['relationships_created']}")
        print(f"Chunks ignorés:        {stats['skipped']}")
        print(f"Erreurs:               {stats['errors']}")
        
        # Afficher les statistiques finales
        print("\n" + "=" * 70)
        print("📊 STATISTIQUES FINALES")
        print("=" * 70)
        
        final_stats = extractor.get_stats()
        if final_stats:
            print(f"Total entités:         {final_stats.get('total_entities', 0)}")
            print(f"Types d'entités:       {final_stats.get('entity_types_count', 0)}")
            if final_stats.get('entity_types'):
                print(f"  Types: {', '.join(final_stats['entity_types'][:10])}")
            print(f"Total relations:       {final_stats.get('total_relationships', 0)}")
            print(f"Types de relations:    {final_stats.get('relationship_types_count', 0)}")
            if final_stats.get('relationship_types'):
                print(f"  Types: {', '.join(final_stats['relationship_types'][:10])}")
            print(f"Content traité:        {final_stats.get('processed_content', 0)} / {final_stats.get('total_content', 0)}")
        
        print("=" * 70)
        print("✅ Extraction terminée avec succès!")
        
        extractor.close()
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

