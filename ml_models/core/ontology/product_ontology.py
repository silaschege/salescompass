from .base import Ontology, Concept, Relationship, ConceptType, RelationshipType, OntologyRegistry

class ProductOntology(Ontology):
    """
    Ontology for Products and Recommendations.
    Models product bundles, features, and cross-sell relationships.
    """
    
    def __init__(self):
        super().__init__("product")
        self.initialize()
        
    def initialize(self) -> None:
        # Base concepts
        product = Concept(id="product", name="Product", concept_type=ConceptType.ENTITY)
        bundle = Concept(id="bundle", name="Product Bundle", concept_type=ConceptType.CATEGORY)
        solution = Concept(id="solution", name="Business Solution", concept_type=ConceptType.CATEGORY)
        benefit = Concept(id="benefit", name="Value Proposition", concept_type=ConceptType.ATTRIBUTE)
        
        self.add_concept(product)
        self.add_concept(bundle)
        self.add_concept(solution)
        self.add_concept(benefit)
        
        # Recommendation triggers
        # Concept(Lead/Opportunity) RECOMMENDS Product
        
    def add_product(self, prod_id: str, name: str, solution_area: str = None):
        prod = Concept(id=f"prod_{prod_id}", name=name, concept_type=ConceptType.ENTITY)
        self.add_concept(prod)
        
        base_prod = self.get_concept("product")
        if base_prod:
            self.add_relationship(Relationship(source=prod, target=base_prod, relationship_type=RelationshipType.IS_A))
            
        if solution_area:
            sol = self.get_concept(f"sol_{solution_area}")
            if not sol:
                sol = Concept(id=f"sol_{solution_area}", name=solution_area, concept_type=ConceptType.CATEGORY)
                self.add_concept(sol)
            self.add_relationship(Relationship(source=prod, target=sol, relationship_type=RelationshipType.BELONGS_TO))

# Register
OntologyRegistry.register(ProductOntology())
