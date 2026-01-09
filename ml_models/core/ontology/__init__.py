# Ontology package for ML Models
# This package contains ontological architecture for knowledge representation

from .base import Concept, Relationship, Ontology
from .sales_ontology import SalesOntology
from .customer_ontology import CustomerOntology
from .competitive_ontology import CompetitiveOntology
from .product_ontology import ProductOntology
from .event_ontology import EventOntology

__all__ = [
    'Concept',
    'Relationship', 
    'Ontology',
    'SalesOntology',
    'CustomerOntology',
    'CompetitiveOntology',
    'ProductOntology',
    'EventOntology',
]
