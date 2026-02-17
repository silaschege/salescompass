"""
Ontology-Based ML Services for SalesCompass

This module provides ML services that leverage the ontological architecture
for predictions, scoring, and recommendations.
"""

from .prediction_service import (
    PredictionService,
    WinProbabilityPredictor,
    ChurnRiskPredictor,
    DealSizePredictor
)
from .scoring_service import (
    ScoringService,
    LeadScoringService,
    AccountHealthScoringService
)
from .recommendation_service import (
    RecommendationService,
    NextBestActionService,
    ContentRecommendationService
)
from .nlp_service import (
    NLPService,
    SentimentAnalyzer,
    EntityExtractor,
    TextClassifier
)
from .anomaly_service import (
    AnomalyService,
    PatternDetector,
    SecurityAnomalyDetector
)

__all__ = [
    # Prediction
    'PredictionService',
    'WinProbabilityPredictor',
    'ChurnRiskPredictor',
    'DealSizePredictor',
    # Scoring
    'ScoringService',
    'LeadScoringService',
    'AccountHealthScoringService',
    # Recommendation
    'RecommendationService',
    'NextBestActionService',
    'ContentRecommendationService',
    # NLP
    'NLPService',
    'SentimentAnalyzer',
    'EntityExtractor',
    'TextClassifier',
    # Anomaly
    'AnomalyService',
    'PatternDetector',
    'SecurityAnomalyDetector',
]
