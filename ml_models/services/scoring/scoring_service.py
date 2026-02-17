"""
Scoring Service - Ontology-Based Entity Scoring

This module provides scoring services for leads and accounts
based on ontological classifications and relationships.
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
class Score:
    """Represents a computed score with breakdown"""
    value: float
    max_value: float
    breakdown: Dict[str, float]
    grade: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
            
    @property
    def percentage(self) -> float:
        return (self.value / self.max_value * 100) if self.max_value > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "max_value": self.max_value,
            "percentage": self.percentage,
            "breakdown": self.breakdown,
            "grade": self.grade,
            "timestamp": self.timestamp.isoformat()
        }


class ScoringService(ABC):
    """Abstract base class for ontology-based scoring services"""
    
    def __init__(self, knowledge_graph: KnowledgeGraph = None):
        self.kg = knowledge_graph or get_knowledge_graph()
        self.max_score = 100
        self.grade_thresholds = {
            "A": 80,
            "B": 60,
            "C": 40,
            "D": 20,
            "F": 0
        }
        
    @abstractmethod
    def score(self, entity_type: str, entity_id: str, **kwargs) -> Score:
        """Calculate score for an entity"""
        pass
    
    def calculate_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        for grade, threshold in sorted(
            self.grade_thresholds.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if score >= threshold:
                return grade
        return "F"


class LeadScoringService(ScoringService):
    """
    Scores leads based on demographic and behavioral factors
    using ontological classifications.
    """
    
    def __init__(self, knowledge_graph: KnowledgeGraph = None):
        super().__init__(knowledge_graph)
        self.demographic_weight = 0.4
        self.behavioral_weight = 0.6
        
    def score(
        self,
        entity_type: str,
        entity_id: str,
        demographic_data: Dict[str, Any] = None,
        behavioral_data: Dict[str, Any] = None
    ) -> Score:
        """
        Calculate lead score based on demographics and behavior.
        
        Args:
            entity_type: Should be "lead"
            entity_id: Lead ID
            demographic_data: Industry, company size, title, etc.
            behavioral_data: Engagement events, page views, etc.
        """
        binding = self.kg.get_entity_binding(entity_type, entity_id)
        breakdown = {}
        
        # Demographic scoring (40%)
        demo_score = self._score_demographics(binding, demographic_data or {})
        breakdown["demographic"] = demo_score * self.demographic_weight
        
        # Behavioral scoring (60%)
        behavior_score = self._score_behavior(binding, behavioral_data or {})
        breakdown["behavioral"] = behavior_score * self.behavioral_weight
        
        # Concept-based adjustments
        concept_bonus = self._get_concept_bonus(binding)
        breakdown["concept_bonus"] = concept_bonus
        
        total_score = sum(breakdown.values())
        total_score = max(0, min(self.max_score, total_score))
        
        # Update entity binding with computed score
        if binding:
            self.kg.update_entity_features(entity_type, entity_id, {"lead_score": total_score})
            
            # Bind to appropriate category concept
            if total_score >= 80:
                if "hot_lead" not in binding.concepts:
                    binding.concepts.append("hot_lead")
            elif total_score >= 50:
                if "warm_lead" not in binding.concepts:
                    binding.concepts.append("warm_lead")
            else:
                if "cold_lead" not in binding.concepts:
                    binding.concepts.append("cold_lead")
        
        return Score(
            value=total_score,
            max_value=self.max_score,
            breakdown=breakdown,
            grade=self.calculate_grade(total_score)
        )
    
    def _score_demographics(
        self,
        binding,
        demographic_data: Dict[str, Any]
    ) -> float:
        """Score based on demographic fit"""
        score = 50  # Base score
        
        # Industry match
        ideal_industries = {"technology", "finance", "healthcare", "manufacturing"}
        industry = demographic_data.get("industry", "").lower()
        if industry in ideal_industries:
            score += 20
            
        # Company size
        employee_count = demographic_data.get("employee_count", 0)
        if employee_count >= 1000:
            score += 15
        elif employee_count >= 100:
            score += 10
        elif employee_count >= 20:
            score += 5
            
        # Title/Seniority
        title = demographic_data.get("title", "").lower()
        if any(x in title for x in ["ceo", "cto", "cfo", "vp", "director"]):
            score += 15
        elif any(x in title for x in ["manager", "head", "lead"]):
            score += 10
            
        return min(100, score)
    
    def _score_behavior(
        self,
        binding,
        behavioral_data: Dict[str, Any]
    ) -> float:
        """Score based on behavioral engagement"""
        score = 0
        
        # Check for engagement events in binding
        if binding:
            for concept_id in binding.concepts:
                concept = self.kg.get_concept(concept_id)
                if concept and concept.concept_type == ConceptType.EVENT:
                    weight = concept.attributes.get("weight", 0.5)
                    score += weight * 20
                    
        # Additional behavioral data
        page_views = behavioral_data.get("page_views", 0)
        score += min(page_views * 2, 20)
        
        email_opens = behavioral_data.get("email_opens", 0)
        score += min(email_opens * 5, 25)
        
        form_submissions = behavioral_data.get("form_submissions", 0)
        score += min(form_submissions * 10, 30)
        
        demo_requested = behavioral_data.get("demo_requested", False)
        if demo_requested:
            score += 25
            
        return min(100, score)
    
    def _get_concept_bonus(self, binding) -> float:
        """Get bonus points from specific concepts"""
        bonus = 0
        
        if not binding:
            return bonus
            
        for concept_id in binding.concepts:
            # MQL/SQL status
            if concept_id == "mql":
                bonus += 5
            elif concept_id == "sql":
                bonus += 10
                
        return bonus


class AccountHealthScoringService(ScoringService):
    """
    Scores account health based on engagement, support, and usage patterns.
    """
    
    def __init__(self, knowledge_graph: KnowledgeGraph = None):
        super().__init__(knowledge_graph)
        self.engagement_weight = 0.35
        self.support_weight = 0.25
        self.usage_weight = 0.25
        self.relationship_weight = 0.15
        
    def score(
        self,
        entity_type: str,
        entity_id: str,
        engagement_data: Dict[str, Any] = None,
        support_data: Dict[str, Any] = None,
        usage_data: Dict[str, Any] = None
    ) -> Score:
        """
        Calculate account health score.
        
        Args:
            entity_type: Should be "account"
            entity_id: Account ID
            engagement_data: Engagement metrics
            support_data: Support ticket data
            usage_data: Product usage metrics
        """
        binding = self.kg.get_entity_binding(entity_type, entity_id)
        breakdown = {}
        
        # Engagement score
        engagement = self._score_engagement(binding, engagement_data or {})
        breakdown["engagement"] = engagement * self.engagement_weight
        
        # Support health
        support = self._score_support(binding, support_data or {})
        breakdown["support"] = support * self.support_weight
        
        # Usage score
        usage = self._score_usage(binding, usage_data or {})
        breakdown["usage"] = usage * self.usage_weight
        
        # Relationship score
        relationship = self._score_relationship(binding)
        breakdown["relationship"] = relationship * self.relationship_weight
        
        total_score = sum(breakdown.values())
        total_score = max(0, min(self.max_score, total_score))
        
        # Update binding
        if binding:
            self.kg.update_entity_features(entity_type, entity_id, {"health_score": total_score})
            
            # Bind to health state
            if total_score >= 80:
                if "health_healthy" not in binding.concepts:
                    binding.concepts.append("health_healthy")
            elif total_score >= 50:
                if "health_at_risk" not in binding.concepts:
                    binding.concepts.append("health_at_risk")
            else:
                if "health_critical" not in binding.concepts:
                    binding.concepts.append("health_critical")
        
        return Score(
            value=total_score,
            max_value=self.max_score,
            breakdown=breakdown,
            grade=self.calculate_grade(total_score)
        )
    
    def _score_engagement(self, binding, data: Dict[str, Any]) -> float:
        """Score based on engagement patterns"""
        score = 50
        
        # NPS score
        nps = data.get("nps_score", 0)
        if nps >= 50:
            score += 30
        elif nps >= 0:
            score += 15
        else:
            score -= 20
            
        # Recent engagement
        days_since_engagement = data.get("days_since_last_engagement", 30)
        if days_since_engagement <= 7:
            score += 20
        elif days_since_engagement <= 14:
            score += 10
        elif days_since_engagement > 30:
            score -= 20
            
        return max(0, min(100, score))
    
    def _score_support(self, binding, data: Dict[str, Any]) -> float:
        """Score based on support metrics"""
        score = 80  # Start optimistic
        
        open_tickets = data.get("open_tickets", 0)
        score -= open_tickets * 5
        
        escalations = data.get("escalations", 0)
        score -= escalations * 15
        
        avg_resolution_time = data.get("avg_resolution_hours", 24)
        if avg_resolution_time > 72:
            score -= 15
        elif avg_resolution_time < 4:
            score += 10
            
        return max(0, min(100, score))
    
    def _score_usage(self, binding, data: Dict[str, Any]) -> float:
        """Score based on product usage"""
        score = 50
        
        adoption_rate = data.get("feature_adoption_rate", 0.5)
        score += adoption_rate * 40
        
        active_users_ratio = data.get("active_users_ratio", 0.5)
        score += active_users_ratio * 30
        
        login_frequency = data.get("weekly_logins", 5)
        score += min(login_frequency * 2, 20)
        
        return max(0, min(100, score))
    
    def _score_relationship(self, binding) -> float:
        """Score based on relationship strength"""
        score = 50
        
        if not binding:
            return score
            
        # Check for champion
        if "role_champion" in binding.concepts:
            score += 30
        elif "role_decision_maker" in binding.concepts:
            score += 20
            
        # Check for blockers
        if "role_blocker" in binding.concepts:
            score -= 20
            
        return max(0, min(100, score))
