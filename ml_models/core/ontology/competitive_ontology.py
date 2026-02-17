from .base import Ontology, Concept, Relationship, ConceptType, RelationshipType, OntologyRegistry

class CompetitiveOntology(Ontology):
    """
    Ontology for Competitive Intelligence.
    Models competitors, their features, pricing, and market positioning.
    """
    
    def __init__(self):
        super().__init__("competitive")
        self.initialize()
        
    def initialize(self) -> None:
        # Define base concepts
        competitor = Concept(id="competitor", name="Competitor", concept_type=ConceptType.ENTITY)
        feature = Concept(id="feature", name="Feature", concept_type=ConceptType.ATTRIBUTE)
        pricing_model = Concept(id="pricing_model", name="Pricing Model", concept_type=ConceptType.CATEGORY)
        market_segment = Concept(id="market_segment", name="Market Segment", concept_type=ConceptType.CATEGORY)
        
        self.add_concept(competitor)
        self.add_concept(feature)
        self.add_concept(pricing_model)
        self.add_concept(market_segment)
        
        # Relationships
        # Competitor HAS_A Feature
        # Competitor BELONGS_TO Market Segment
        # Feature INFLUENCES Win Rate (via KG links)
        
    def add_competitor(self, comp_id: str, name: str, segment: str = None):
        comp = Concept(id=f"comp_{comp_id}", name=name, concept_type=ConceptType.ENTITY)
        self.add_concept(comp)
        
        # Link to base competitor concept
        base_comp = self.get_concept("competitor")
        if base_comp:
            self.add_relationship(Relationship(source=comp, target=base_comp, relationship_type=RelationshipType.IS_A))
            
        if segment:
            seg_concept = self.get_concept(f"segment_{segment}")
            if not seg_concept:
                seg_concept = Concept(id=f"segment_{segment}", name=segment, concept_type=ConceptType.CATEGORY)
                self.add_concept(seg_concept)
            self.add_relationship(Relationship(source=comp, target=seg_concept, relationship_type=RelationshipType.BELONGS_TO))

# Register
OntologyRegistry.register(CompetitiveOntology())
