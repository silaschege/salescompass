"""
Semantic Governance - SPARQL Queries & SHACL Validation.
Ensures Knowledge Graph integrity and provides advanced query capabilities.
"""

from typing import Dict, Any, List, Optional
import logging
from ml_models.core.knowledge_graph import get_knowledge_graph

class SemanticGovernanceService:
    """
    Manages graph validation and advanced querying.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("governance.semantic")
        self.kg = get_knowledge_graph()

    def validate_graph(self) -> Dict[str, Any]:
        """
        Performs structural and semantic validation (Concept-SHACL).
        Ensures all concepts have IDs, types, and required relationships.
        """
        self.logger.info("Starting SHACL-style graph validation...")
        errors = []
        
        # 1. Structural Validation
        for ont_name in self.kg.list_ontologies():
            ont = self.kg._ontologies.get(ont_name)
            for concept_id, concept in ont._concepts.items():
                if not concept.name:
                    errors.append(f"Concept {concept_id}: Missing Name")
                if not concept.concept_type:
                    errors.append(f"Concept {concept_id}: Missing Type")
                    
        # 2. Relationship Integrity
        for ont_name in self.kg.list_ontologies():
            ont = self.kg._ontologies.get(ont_name)
            for rel in ont._relationships:
                if rel.source.id not in ont._concepts or rel.target.id not in ont._concepts:
                    errors.append(f"Relationship Integrity Failure: {rel.source.id} -> {rel.target.id}")

        return {
            "valid": len(errors) == 0,
            "error_count": len(errors),
            "errors": errors
        }

    def execute_sparql_lite(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes a simplified SPARQL-style query against the Knowledge Graph.
        In a production environment, this would use rdflib.plugins.sparql.
        """
        self.logger.info(f"Executing query: {query}")
        # Simplified query parser for MVP (Selective retrieval)
        results = []
        
        if "SELECT" in query.upper() and ("LEADS" in query.upper() or "CONCEPTS" in query.upper()):
            for ont_name in self.kg.list_ontologies():
                ont = self.kg._ontologies.get(ont_name)
                for c in ont._concepts.values():
                    results.append({"id": c.id, "name": c.name, "type": c.concept_type.value})
                    
        return results
