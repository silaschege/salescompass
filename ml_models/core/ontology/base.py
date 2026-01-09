"""
Base Ontology Classes for SalesCompass ML

This module provides the foundational classes for building domain-specific
ontologies using a graph-based knowledge representation approach.

Architecture:
- Concept: Represents entities/categories in the domain
- Relationship: Semantic connections between concepts
- Ontology: Container for concepts and relationships
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Callable
from enum import Enum
import json
from datetime import datetime


class ConceptType(Enum):
    """Types of concepts in the ontology"""
    ENTITY = "entity"           # Concrete instance (Lead, Account, Opportunity)
    CATEGORY = "category"       # Classification (Hot Lead, Enterprise Account)
    ATTRIBUTE = "attribute"     # Property (Score, Status, Stage)
    EVENT = "event"             # Temporal occurrence (Engagement, Conversion)
    METRIC = "metric"           # Measurable value (Win Rate, CLV)
    ACTION = "action"           # Recommended action (Call, Email, Meeting)


class RelationshipType(Enum):
    """Types of relationships between concepts"""
    IS_A = "is_a"                       # Inheritance (Hot Lead IS_A Lead)
    HAS_A = "has_a"                     # Composition (Account HAS_A Contact)
    BELONGS_TO = "belongs_to"           # Membership (Lead BELONGS_TO Campaign)
    INFLUENCES = "influences"           # Causal (Engagement INFLUENCES Win Rate)
    TRIGGERS = "triggers"               # Event causation (Low Score TRIGGERS Alert)
    CORRELATES_WITH = "correlates_with" # Statistical (Revenue CORRELATES_WITH Engagement)
    PRECEDES = "precedes"               # Temporal (Qualification PRECEDES Proposal)
    RECOMMENDS = "recommends"           # Suggestive (High Score RECOMMENDS Call)


@dataclass
class Concept:
    """
    Represents a node in the knowledge graph.
    
    Attributes:
        id: Unique identifier
        name: Human-readable name
        concept_type: Type classification
        attributes: Key-value properties
        embeddings: Vector representation for ML
        metadata: Additional context
    """
    id: str
    name: str
    concept_type: ConceptType
    attributes: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, Concept):
            return self.id == other.id
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "concept_type": self.concept_type.value,
            "attributes": self.attributes,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Concept':
        return cls(
            id=data["id"],
            name=data["name"],
            concept_type=ConceptType(data["concept_type"]),
            attributes=data.get("attributes", {}),
            embeddings=data.get("embeddings"),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        )


@dataclass
class Relationship:
    """
    Represents an edge in the knowledge graph.
    
    Attributes:
        source: Source concept
        target: Target concept
        relationship_type: Type of relationship
        weight: Strength of relationship (0.0 to 1.0)
        confidence: Confidence in the relationship
        properties: Additional relationship properties
    """
    source: Concept
    target: Concept
    relationship_type: RelationshipType
    weight: float = 1.0
    confidence: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash((self.source.id, self.target.id, self.relationship_type))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source.id,
            "target_id": self.target.id,
            "relationship_type": self.relationship_type.value,
            "weight": self.weight,
            "confidence": self.confidence,
            "properties": self.properties
        }


class Ontology(ABC):
    """
    Abstract base class for domain-specific ontologies.
    
    Provides methods for:
    - Managing concepts and relationships
    - Querying the knowledge graph
    - Inferring new knowledge
    """
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self._concepts: Dict[str, Concept] = {}
        self._relationships: List[Relationship] = []
        self._concept_index: Dict[ConceptType, Set[str]] = {t: set() for t in ConceptType}
        self._relationship_index: Dict[str, List[Relationship]] = {}
        
    @abstractmethod
    def initialize(self) -> None:
        """Initialize domain-specific concepts and relationships"""
        pass
    
    def add_concept(self, concept: Concept) -> None:
        """Add a concept to the ontology"""
        self._concepts[concept.id] = concept
        self._concept_index[concept.concept_type].add(concept.id)
        self._relationship_index[concept.id] = []
        
    def get_concept(self, concept_id: str) -> Optional[Concept]:
        """Retrieve a concept by ID"""
        return self._concepts.get(concept_id)
    
    def get_concepts_by_type(self, concept_type: ConceptType) -> List[Concept]:
        """Get all concepts of a specific type"""
        return [self._concepts[cid] for cid in self._concept_index[concept_type]]
    
    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship to the ontology"""
        self._relationships.append(relationship)
        self._relationship_index[relationship.source.id].append(relationship)
        
    def get_relationships(self, concept_id: str) -> List[Relationship]:
        """Get all relationships from a concept"""
        return self._relationship_index.get(concept_id, [])
    
    def get_related_concepts(
        self, 
        concept_id: str, 
        relationship_type: Optional[RelationshipType] = None
    ) -> List[Concept]:
        """Get concepts related to a given concept"""
        relationships = self.get_relationships(concept_id)
        if relationship_type:
            relationships = [r for r in relationships if r.relationship_type == relationship_type]
        return [r.target for r in relationships]
    
    def infer_path(
        self, 
        source_id: str, 
        target_id: str, 
        max_depth: int = 5
    ) -> Optional[List[Relationship]]:
        """Find a path of relationships between two concepts"""
        visited = set()
        queue = [(source_id, [])]
        
        while queue:
            current_id, path = queue.pop(0)
            if current_id == target_id:
                return path
            
            if current_id in visited or len(path) >= max_depth:
                continue
                
            visited.add(current_id)
            
            for rel in self.get_relationships(current_id):
                if rel.target.id not in visited:
                    queue.append((rel.target.id, path + [rel]))
        
        return None
    
    def compute_similarity(self, concept1_id: str, concept2_id: str) -> float:
        """Compute similarity between two concepts based on their relationships"""
        c1_rels = set(r.target.id for r in self.get_relationships(concept1_id))
        c2_rels = set(r.target.id for r in self.get_relationships(concept2_id))
        
        if not c1_rels and not c2_rels:
            return 0.0
            
        intersection = len(c1_rels & c2_rels)
        union = len(c1_rels | c2_rels)
        
        return intersection / union if union > 0 else 0.0
    
    def to_json(self) -> str:
        """Serialize ontology to JSON"""
        return json.dumps({
            "name": self.name,
            "version": self.version,
            "concepts": [c.to_dict() for c in self._concepts.values()],
            "relationships": [r.to_dict() for r in self._relationships]
        }, indent=2)
    
    def query(
        self,
        concept_type: Optional[ConceptType] = None,
        attributes: Optional[Dict[str, Any]] = None,
        related_to: Optional[str] = None,
        relationship_type: Optional[RelationshipType] = None
    ) -> List[Concept]:
        """
        Query concepts based on various criteria.
        
        Args:
            concept_type: Filter by concept type
            attributes: Filter by attribute values
            related_to: Filter by relationship to another concept
            relationship_type: Type of relationship for related_to filter
        """
        results = list(self._concepts.values())
        
        if concept_type:
            results = [c for c in results if c.concept_type == concept_type]
            
        if attributes:
            results = [
                c for c in results 
                if all(c.attributes.get(k) == v for k, v in attributes.items())
            ]
            
        if related_to:
            related = self.get_related_concepts(related_to, relationship_type)
            related_ids = {c.id for c in related}
            results = [c for c in results if c.id in related_ids]
            
        return results


class OntologyRegistry:
    """
    Singleton registry for managing multiple ontologies.
    """
    _instance = None
    _ontologies: Dict[str, Ontology] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, ontology: Ontology) -> None:
        """Register an ontology"""
        cls._ontologies[ontology.name] = ontology
        
    @classmethod
    def get(cls, name: str) -> Optional[Ontology]:
        """Get an ontology by name"""
        return cls._ontologies.get(name)
    
    @classmethod
    def list_ontologies(cls) -> List[str]:
        """List all registered ontology names"""
        return list(cls._ontologies.keys())
