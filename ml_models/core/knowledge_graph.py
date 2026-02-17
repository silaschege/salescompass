"""
Knowledge Graph for SalesCompass ML

This module provides a unified knowledge graph that integrates
multiple domain ontologies and enables cross-domain reasoning.
"""

from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

from .ontology.base import (
    Concept, Relationship, Ontology,
    ConceptType, RelationshipType, OntologyRegistry
)

logger = logging.getLogger(__name__)


@dataclass
class EntityBinding:
    """
    Binds a real-world entity to ontology concepts.
    
    Attributes:
        entity_type: Type of entity (lead, opportunity, account, etc.)
        entity_id: Unique identifier in the source system
        concepts: List of concept IDs this entity is bound to
        features: Computed features for ML
        last_updated: Timestamp of last update
    """
    entity_type: str
    entity_id: str
    concepts: List[str] = field(default_factory=list)
    features: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "concepts": self.concepts,
            "features": self.features,
            "metadata": self.metadata,
            "last_updated": self.last_updated.isoformat()
        }


class KnowledgeGraph:
    """
    Unified knowledge graph integrating multiple ontologies.
    
    Provides:
    - Cross-ontology concept linking
    - Entity-to-concept binding
    - Inference and reasoning
    - Feature extraction for ML
    """
    
    def __init__(self, name: str = "salescompass_kg"):
        self.name = name
        self._ontologies: Dict[str, Ontology] = {}
        self._entity_bindings: Dict[Tuple[str, str], EntityBinding] = {}
        self._cross_ontology_links: List[Relationship] = []
        self._inference_rules: List[callable] = []
        
    def register_ontology(self, ontology: Ontology) -> None:
        """Register an ontology with the knowledge graph"""
        self._ontologies[ontology.name] = ontology
        logger.info(f"Registered ontology: {ontology.name}")
        
    def get_ontology(self, name: str) -> Optional[Ontology]:
        """Get a registered ontology by name"""
        return self._ontologies.get(name)
    
    def list_ontologies(self) -> List[str]:
        """List all registered ontology names"""
        return list(self._ontologies.keys())
    
    def get_concept(self, concept_id: str) -> Optional[Concept]:
        """Get a concept from any registered ontology"""
        for ontology in self._ontologies.values():
            concept = ontology.get_concept(concept_id)
            if concept:
                return concept
        return None
    
    def link_concepts(
        self,
        source_ontology: str,
        source_concept_id: str,
        target_ontology: str,
        target_concept_id: str,
        relationship_type: RelationshipType,
        weight: float = 1.0,
        properties: Dict[str, Any] = None
    ) -> bool:
        """Create a cross-ontology link between concepts"""
        source_ont = self.get_ontology(source_ontology)
        target_ont = self.get_ontology(target_ontology)
        
        if not source_ont or not target_ont:
            return False
            
        source = source_ont.get_concept(source_concept_id)
        target = target_ont.get_concept(target_concept_id)
        
        if not source or not target:
            return False
            
        link = Relationship(
            source=source,
            target=target,
            relationship_type=relationship_type,
            weight=weight,
            properties=properties or {}
        )
        self._cross_ontology_links.append(link)
        return True
    
    # === Entity Binding ===
    
    def bind_entity(
        self,
        entity_type: str,
        entity_id: str,
        concept_ids: List[str],
        features: Dict[str, float] = None,
        metadata: Dict[str, Any] = None
    ) -> EntityBinding:
        """Bind a real-world entity to ontology concepts"""
        key = (entity_type, entity_id)
        
        binding = EntityBinding(
            entity_type=entity_type,
            entity_id=entity_id,
            concepts=concept_ids,
            features=features or {},
            metadata=metadata or {},
            last_updated=datetime.now()
        )
        
        self._entity_bindings[key] = binding
        return binding
    
    def get_entity_binding(self, entity_type: str, entity_id: str) -> Optional[EntityBinding]:
        """Get the binding for an entity"""
        return self._entity_bindings.get((entity_type, entity_id))
    
    def get_entities_by_concept(self, concept_id: str) -> List[EntityBinding]:
        """Get all entities bound to a specific concept"""
        return [
            binding for binding in self._entity_bindings.values()
            if concept_id in binding.concepts
        ]
    
    def update_entity_features(
        self,
        entity_type: str,
        entity_id: str,
        features: Dict[str, float]
    ) -> bool:
        """Update features for an entity binding"""
        binding = self.get_entity_binding(entity_type, entity_id)
        if binding:
            binding.features.update(features)
            binding.last_updated = datetime.now()
            return True
        return False
    
    # === Inference & Reasoning ===
    
    def add_inference_rule(self, rule: callable) -> None:
        """Add an inference rule function"""
        self._inference_rules.append(rule)
    
    def infer_concepts(self, entity_type: str, entity_id: str) -> List[str]:
        """
        Infer additional concepts for an entity based on its current bindings.
        Uses registered inference rules and ontology relationships.
        """
        binding = self.get_entity_binding(entity_type, entity_id)
        if not binding:
            return []
            
        inferred = set()
        
        # Apply inference rules
        for rule in self._inference_rules:
            try:
                new_concepts = rule(binding, self)
                inferred.update(new_concepts)
            except Exception as e:
                logger.error(f"Inference rule failed: {e}")
                
        # Follow ontology relationships
        for concept_id in binding.concepts:
            concept = self.get_concept(concept_id)
            if not concept:
                continue
                
            # Find related concepts through IS_A and BELONGS_TO
            for ontology in self._ontologies.values():
                for rel in ontology.get_relationships(concept_id):
                    if rel.relationship_type in [RelationshipType.IS_A, RelationshipType.BELONGS_TO]:
                        inferred.add(rel.target.id)
                        
        # Remove already bound concepts
        inferred -= set(binding.concepts)
        
        return list(inferred)
    
    def get_recommended_actions(
        self,
        entity_type: str,
        entity_id: str
    ) -> List[Tuple[Concept, float]]:
        """
        Get recommended actions for an entity based on its concepts.
        Returns list of (action_concept, confidence) tuples.
        """
        binding = self.get_entity_binding(entity_type, entity_id)
        if not binding:
            return []
            
        recommendations = {}
        
        for concept_id in binding.concepts:
            for ontology in self._ontologies.values():
                for rel in ontology.get_relationships(concept_id):
                    if rel.relationship_type == RelationshipType.RECOMMENDS:
                        if rel.target.concept_type == ConceptType.ACTION:
                            action_id = rel.target.id
                            if action_id not in recommendations:
                                recommendations[action_id] = (rel.target, rel.confidence)
                            else:
                                # Combine confidences
                                existing_conf = recommendations[action_id][1]
                                new_conf = 1 - (1 - existing_conf) * (1 - rel.confidence)
                                recommendations[action_id] = (rel.target, new_conf)
                                
        # Sort by confidence
        sorted_recommendations = sorted(
            recommendations.values(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_recommendations
    
    def compute_influence_score(
        self,
        entity_type: str,
        entity_id: str,
        target_metric_id: str
    ) -> float:
        """
        Compute the influence score of an entity's concepts on a target metric.
        """
        binding = self.get_entity_binding(entity_type, entity_id)
        if not binding:
            return 0.0
            
        total_influence = 0.0
        
        for concept_id in binding.concepts:
            for ontology in self._ontologies.values():
                for rel in ontology.get_relationships(concept_id):
                    if rel.relationship_type == RelationshipType.INFLUENCES:
                        if rel.target.id == target_metric_id:
                            total_influence += rel.weight * rel.confidence
                            
        # Also check cross-ontology links
        for link in self._cross_ontology_links:
            if link.source.id in binding.concepts and link.target.id == target_metric_id:
                if link.relationship_type == RelationshipType.INFLUENCES:
                    total_influence += link.weight
                    
        return min(max(total_influence, 0.0), 1.0)  # Clamp to [0, 1]
    
    # === Feature Extraction ===
    
    def extract_ontology_features(
        self,
        entity_type: str,
        entity_id: str
    ) -> Dict[str, float]:
        """
        Extract features for an entity based on its ontology bindings.
        Returns a feature dictionary suitable for ML models.
        """
        binding = self.get_entity_binding(entity_type, entity_id)
        if not binding:
            return {}
            
        features = {}
        
        # One-hot encode concept types
        for concept_type in ConceptType:
            features[f"concept_type_{concept_type.value}"] = 0.0
            
        # Count concepts by type
        for concept_id in binding.concepts:
            concept = self.get_concept(concept_id)
            if concept:
                features[f"concept_type_{concept.concept_type.value}"] += 1.0
                features[f"has_{concept_id}"] = 1.0
                
        # Relationship-based features
        relationship_counts = {rt.value: 0 for rt in RelationshipType}
        
        for concept_id in binding.concepts:
            for ontology in self._ontologies.values():
                for rel in ontology.get_relationships(concept_id):
                    relationship_counts[rel.relationship_type.value] += 1
                    
        for rt, count in relationship_counts.items():
            features[f"rel_count_{rt}"] = float(count)
            
        # Merge with stored features
        features.update(binding.features)
        
        return features
    
    # === Serialization ===
    
    def to_json(self) -> str:
        """Serialize the knowledge graph to JSON"""
        return json.dumps({
            "name": self.name,
            "ontologies": self.list_ontologies(),
            "entity_bindings": [b.to_dict() for b in self._entity_bindings.values()],
            "cross_ontology_links": [r.to_dict() for r in self._cross_ontology_links]
        }, indent=2)

    def to_rdf_turtle(self) -> str:
        """
        Export the knowledge graph in RDF Turtle format for OWL interoperability.
        """
        lines = [
            "@prefix sc: <http://salescompass.io/ontology/> .",
            "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
            "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
            ""
        ]
        
        # Concepts
        for ont in self._ontologies.values():
            for concept in ont._concepts.values():
                lines.append(f"sc:{concept.id} rdf:type owl:Class ;")
                lines.append(f"    rdfs:label \"{concept.name}\" ;")
                lines.append(f"    sc:conceptType \"{concept.concept_type.value}\" .")
                
        # Relationships
        for ont in self._ontologies.values():
            for rel in ont._relationships:
                lines.append(f"sc:{rel.source.id} sc:{rel.relationship_type.value} sc:{rel.target.id} .")
                
        # Entity Bindings
        for key, binding in self._entity_bindings.items():
            subject = f"sc:{binding.entity_type}_{binding.entity_id}"
            lines.append(f"{subject} rdf:type sc:Entity ;")
            for concept_id in binding.concepts:
                lines.append(f"    sc:classifiedAs sc:{concept_id} ;")
            lines.append(f"    sc:lastUpdated \"{binding.last_updated.isoformat()}\" .")
            
        return "\n".join(lines)
    
    def stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        total_concepts = sum(
            len(ont._concepts) for ont in self._ontologies.values()
        )
        total_relationships = sum(
            len(ont._relationships) for ont in self._ontologies.values()
        )
        
        return {
            "ontologies": len(self._ontologies),
            "total_concepts": total_concepts,
            "total_relationships": total_relationships + len(self._cross_ontology_links),
            "entity_bindings": len(self._entity_bindings),
            "cross_ontology_links": len(self._cross_ontology_links),
            "inference_rules": len(self._inference_rules)
        }


# Singleton instance
_knowledge_graph = None

def get_knowledge_graph() -> KnowledgeGraph:
    """Get the singleton knowledge graph instance"""
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = KnowledgeGraph()
        
        # Auto-register ontologies from registry
        for ont_name in OntologyRegistry.list_ontologies():
            ont = OntologyRegistry.get(ont_name)
            if ont:
                _knowledge_graph.register_ontology(ont)
                
    return _knowledge_graph
