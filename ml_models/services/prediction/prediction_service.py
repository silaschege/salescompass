"""
Prediction Service - Ontology-Based ML Predictions

This module provides prediction services that leverage the knowledge graph
and ontological concepts for win probability, churn risk, and deal size predictions.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

from ml_models.core.ontology.base import Concept, ConceptType, RelationshipType
from ml_models.core.knowledge_graph import KnowledgeGraph, get_knowledge_graph

logger = logging.getLogger(__name__)


@dataclass
class Prediction:
    """Represents an ML prediction with confidence and explanation"""
    value: float
    confidence: float
    explanation: List[str]
    contributing_factors: Dict[str, float]
    timestamp: datetime = None
    model_version: str = "1.0.0"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
            
    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "contributing_factors": self.contributing_factors,
            "timestamp": self.timestamp.isoformat(),
            "model_version": self.model_version
        }


class PredictionService(ABC):
    """
    Abstract base class for ontology-based prediction services.
    """
    
    def __init__(self, knowledge_graph: KnowledgeGraph = None):
        self.kg = knowledge_graph or get_knowledge_graph()
        self.model_name = "base_predictor"
        self.model_version = "1.0.0"
        
    @abstractmethod
    def predict(self, entity_type: str, entity_id: str, **kwargs) -> Prediction:
        """Make a prediction for an entity"""
        pass
    
    def get_entity_features(self, entity_type: str, entity_id: str) -> Dict[str, float]:
        """Extract features from knowledge graph for prediction"""
        return self.kg.extract_ontology_features(entity_type, entity_id)
    
    def explain_prediction(
        self,
        entity_type: str,
        entity_id: str,
        prediction: Prediction
    ) -> List[str]:
        """Generate human-readable explanation for a prediction"""
        explanations = []
        
        binding = self.kg.get_entity_binding(entity_type, entity_id)
        if not binding:
            return ["No ontology binding found for entity"]
            
        for concept_id in binding.concepts:
            concept = self.kg.get_concept(concept_id)
            if concept and concept.concept_type == ConceptType.CATEGORY:
                explanations.append(f"Entity classified as: {concept.name}")
                
        for factor, weight in prediction.contributing_factors.items():
            if weight > 0.1:
                explanations.append(f"{factor} contributes +{weight:.0%} to prediction")
            elif weight < -0.1:
                explanations.append(f"{factor} contributes {weight:.0%} to prediction")
                
        return explanations


class WinProbabilityPredictor(PredictionService):
    """
    Predicts the probability of winning an opportunity.
    Uses ontology concepts like stage, engagement, and win factors.
    """
    
    def __init__(self, knowledge_graph: KnowledgeGraph = None):
        super().__init__(knowledge_graph)
        self.model_name = "win_probability_predictor"
        
    def predict(
        self,
        entity_type: str,
        entity_id: str,
        opportunity_data: Dict[str, Any] = None
    ) -> Prediction:
        """
        Predict win probability for an opportunity.
        
        Args:
            entity_type: Should be "opportunity"
            entity_id: Opportunity ID
            opportunity_data: Additional opportunity attributes
        """
        features = self.get_entity_features(entity_type, entity_id)
        binding = self.kg.get_entity_binding(entity_type, entity_id)
        
        # Base probability from stage
        base_probability = 0.25
        contributing_factors = {}
        
        if binding:
            for concept_id in binding.concepts:
                concept = self.kg.get_concept(concept_id)
                if not concept:
                    continue
                    
                # Stage-based probability
                if concept_id.startswith("stage_"):
                    stage_prob = concept.attributes.get("probability", 0.25)
                    base_probability = stage_prob
                    contributing_factors["stage"] = stage_prob
                    
                # Win factors
                if concept.attributes.get("factor_type") == "win":
                    impact = concept.attributes.get("impact", 0.1)
                    base_probability += impact
                    contributing_factors[concept.name] = impact
                    
                # Loss factors
                if concept.attributes.get("factor_type") == "loss":
                    impact = concept.attributes.get("impact", -0.1)
                    base_probability += impact
                    contributing_factors[concept.name] = impact
                    
        # Engagement influence
        engagement_influence = self.kg.compute_influence_score(
            entity_type, entity_id, "win_probability"
        )
        if engagement_influence > 0:
            base_probability += engagement_influence * 0.2
            contributing_factors["engagement"] = engagement_influence * 0.2
            
        # Clamp probability
        final_probability = max(0.0, min(1.0, base_probability))
        
        # Calculate confidence based on data completeness
        confidence = min(0.5 + len(binding.concepts) * 0.1 if binding else 0.3, 0.95)
        
        prediction = Prediction(
            value=final_probability,
            confidence=confidence,
            explanation=[],
            contributing_factors=contributing_factors,
            model_version=self.model_version
        )
        
        prediction.explanation = self.explain_prediction(entity_type, entity_id, prediction)
        
        return prediction


class ChurnRiskPredictor(PredictionService):
    """
    Predicts the risk of customer churn.
    Uses customer ontology concepts for health and engagement signals.
    """
    
    def __init__(self, knowledge_graph: KnowledgeGraph = None):
        super().__init__(knowledge_graph)
        self.model_name = "churn_risk_predictor"
        
    def predict(
        self,
        entity_type: str,
        entity_id: str,
        account_data: Dict[str, Any] = None
    ) -> Prediction:
        """
        Predict churn risk for an account.
        
        Args:
            entity_type: Should be "account"
            entity_id: Account ID
            account_data: Additional account attributes
        """
        features = self.get_entity_features(entity_type, entity_id)
        binding = self.kg.get_entity_binding(entity_type, entity_id)
        
        # Base risk
        base_risk = 0.1
        contributing_factors = {}
        
        if binding:
            for concept_id in binding.concepts:
                concept = self.kg.get_concept(concept_id)
                if not concept:
                    continue
                    
                # Health state
                if concept_id.startswith("health_"):
                    churn_risk_map = {"low": 0.1, "medium": 0.4, "high": 0.7}
                    risk_level = concept.attributes.get("churn_risk", "medium")
                    base_risk = churn_risk_map.get(risk_level, 0.3)
                    contributing_factors["health_state"] = base_risk
                    
                # Churn signals
                if concept.attributes.get("signal_type") == "churn":
                    severity = concept.attributes.get("severity", 0.3)
                    base_risk += severity * 0.3
                    contributing_factors[concept.name] = severity * 0.3
                    
                # Engagement patterns
                if concept_id.startswith("pattern_"):
                    if "dormant" in concept_id or "disengaged" in concept_id:
                        base_risk += 0.2
                        contributing_factors["engagement_pattern"] = 0.2
                    elif "active" in concept_id:
                        base_risk -= 0.1
                        contributing_factors["engagement_pattern"] = -0.1
                        
        # Influence from metrics
        churn_influence = self.kg.compute_influence_score(
            entity_type, entity_id, "churn_risk"
        )
        if churn_influence > 0:
            base_risk += churn_influence
            contributing_factors["signal_influence"] = churn_influence
            
        final_risk = max(0.0, min(1.0, base_risk))
        confidence = min(0.5 + len(binding.concepts) * 0.1 if binding else 0.3, 0.95)
        
        prediction = Prediction(
            value=final_risk,
            confidence=confidence,
            explanation=[],
            contributing_factors=contributing_factors,
            model_version=self.model_version
        )
        
        prediction.explanation = self.explain_prediction(entity_type, entity_id, prediction)
        
        return prediction


class DealSizePredictor(PredictionService):
    """
    Predicts expected deal size based on account segment and opportunity characteristics.
    """
    
    def __init__(self, knowledge_graph: KnowledgeGraph = None):
        super().__init__(knowledge_graph)
        self.model_name = "deal_size_predictor"
        
    def predict(
        self,
        entity_type: str,
        entity_id: str,
        opportunity_data: Dict[str, Any] = None
    ) -> Prediction:
        """
        Predict expected deal size.
        
        Args:
            entity_type: "opportunity" or "account"
            entity_id: Entity ID
            opportunity_data: Current deal information
        """
        binding = self.kg.get_entity_binding(entity_type, entity_id)
        
        # Segment-based base
        segment_values = {
            "segment_enterprise": 150000,
            "segment_mid_market": 50000,
            "segment_smb": 15000,
            "segment_startup": 25000
        }
        
        base_value = 30000
        contributing_factors = {}
        
        if binding:
            for concept_id in binding.concepts:
                if concept_id in segment_values:
                    base_value = segment_values[concept_id]
                    contributing_factors["segment"] = base_value
                    break
                    
            # Adjust for expansion potential
            for concept_id in binding.concepts:
                concept = self.kg.get_concept(concept_id)
                if concept and concept.id == "expansion_potential":
                    if binding.features.get("expansion_potential", 0) > 0.5:
                        multiplier = 1.3
                        base_value *= multiplier
                        contributing_factors["expansion_potential"] = multiplier
                        
        # Apply provided data if available
        if opportunity_data and "amount" in opportunity_data:
            stated_amount = opportunity_data["amount"]
            # Blend stated with predicted
            base_value = (base_value * 0.3) + (stated_amount * 0.7)
            contributing_factors["stated_amount"] = stated_amount
            
        confidence = 0.6 if binding and len(binding.concepts) > 2 else 0.4
        
        prediction = Prediction(
            value=base_value,
            confidence=confidence,
            explanation=[f"Predicted deal size: ${base_value:,.0f}"],
            contributing_factors=contributing_factors,
            model_version=self.model_version
        )
        
        return prediction
