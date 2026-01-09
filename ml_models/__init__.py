# ML Models package for SalesCompass
# Built with an ontological architecture for standalone deployment

from .core.ontology.base import (
    Concept,
    Relationship,
    Ontology,
)
from .core.ontology.sales_ontology import SalesOntology, get_sales_ontology
from .core.ontology.customer_ontology import CustomerOntology, get_customer_ontology
from .core.knowledge_graph import KnowledgeGraph, get_knowledge_graph

from .services.prediction import (
    PredictionService,
    WinProbabilityPredictor,
    ChurnRiskPredictor,
    DealSizePredictor,
)
from .services.scoring import (
    ScoringService,
    LeadScoringService,
    AccountHealthScoringService,
)
from .services.recommendation import (
    RecommendationService,
    NextBestActionService,
    ContentRecommendationService,
)
from .services.intelligence import (
    NLPService,
    SentimentAnalyzer,
    EntityExtractor,
    TextClassifier,
    AnomalyService,
    PatternDetector,
    SecurityAnomalyDetector,
)

__all__ = [
    # Core Ontology
    'Concept',
    'Relationship',
    'Ontology',
    'SalesOntology',
    'CustomerOntology',
    'get_sales_ontology',
    'get_customer_ontology',
    'KnowledgeGraph',
    'get_knowledge_graph',
    
    # Services
    'PredictionService',
    'WinProbabilityPredictor',
    'ChurnRiskPredictor',
    'DealSizePredictor',
    'ScoringService',
    'LeadScoringService',
    'AccountHealthScoringService',
    'RecommendationService',
    'NextBestActionService',
    'ContentRecommendationService',
    'NLPService',
    'SentimentAnalyzer',
    'EntityExtractor',
    'TextClassifier',
    'AnomalyService',
    'PatternDetector',
    'SecurityAnomalyDetector',
]

__version__ = '1.1.0'
