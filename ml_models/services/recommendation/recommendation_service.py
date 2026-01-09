"""
Recommendation Service - Ontology-Based Recommendations

This module provides recommendation services for Next Best Actions,
content suggestions, and intelligent guidance.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from ml_models.core.ontology.base import Concept, ConceptType, RelationshipType
from ml_models.core.knowledge_graph import KnowledgeGraph, get_knowledge_graph

logger = logging.getLogger(__name__)


class RecommendationPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Recommendation:
    """Represents a recommendation with context"""
    id: str
    title: str
    description: str
    action_type: str
    priority: RecommendationPriority
    confidence: float
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "action_type": self.action_type,
            "priority": self.priority.value,
            "confidence": self.confidence,
            "reason": self.reason,
            "metadata": self.metadata,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


class RecommendationService(ABC):
    """Abstract base class for recommendation services"""
    
    def __init__(self, knowledge_graph: KnowledgeGraph = None):
        self.kg = knowledge_graph or get_knowledge_graph()
        
    @abstractmethod
    def get_recommendations(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 5
    ) -> List[Recommendation]:
        """Get recommendations for an entity"""
        pass


class NextBestActionService(RecommendationService):
    """
    Provides Next Best Action recommendations based on
    entity state and ontological relationships.
    """
    
    ACTION_TEMPLATES = {
        "action_call": {
            "title": "Schedule a Call",
            "description": "This lead/contact would benefit from a direct phone call",
            "timing": "within 24 hours"
        },
        "action_email": {
            "title": "Send Personalized Email",
            "description": "Follow up with a tailored email based on their interests",
            "timing": "same day"
        },
        "action_meeting": {
            "title": "Schedule Discovery Meeting",
            "description": "Set up a meeting to understand their requirements",
            "timing": "this week"
        },
        "action_proposal": {
            "title": "Send Proposal",
            "description": "Prepare and send a customized proposal",
            "timing": "after qualification"
        },
        "action_followup": {
            "title": "Follow Up",
            "description": "Check in on pending items or decisions",
            "timing": "3 days"
        },
        "action_exec_outreach": {
            "title": "Executive Outreach",
            "description": "Engage an executive sponsor for strategic alignment",
            "timing": "urgent"
        },
        "action_success_review": {
            "title": "Success Review Meeting",
            "description": "Conduct a formal success review to address concerns",
            "timing": "this week"
        },
        "action_training_offer": {
            "title": "Offer Training Session",
            "description": "Provide additional training to increase adoption",
            "timing": "within 2 weeks"
        },
        "action_discount_offer": {
            "title": "Retention Offer",
            "description": "Present a retention offer or discount",
            "timing": "before renewal"
        },
        "action_feature_preview": {
            "title": "Feature Preview Access",
            "description": "Provide early access to upcoming features",
            "timing": "when available"
        }
    }
    
    def get_recommendations(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 5
    ) -> List[Recommendation]:
        """
        Get Next Best Actions for an entity.
        
        Uses ontology RECOMMENDS and TRIGGERS relationships to identify actions.
        """
        recommendations = []
        
        # Get ontology-based recommendations
        ontology_actions = self.kg.get_recommended_actions(entity_type, entity_id)
        
        for action_concept, confidence in ontology_actions:
            template = self.ACTION_TEMPLATES.get(action_concept.id, {})
            
            priority = self._determine_priority(action_concept, confidence)
            
            rec = Recommendation(
                id=f"nba_{entity_type}_{entity_id}_{action_concept.id}",
                title=template.get("title", action_concept.name),
                description=template.get("description", ""),
                action_type=action_concept.id,
                priority=priority,
                confidence=confidence,
                reason=self._generate_reason(entity_type, entity_id, action_concept),
                metadata={
                    "timing": template.get("timing", "soon"),
                    "concept_id": action_concept.id,
                    "urgency": action_concept.attributes.get("urgency", "medium")
                }
            )
            recommendations.append(rec)
            
        # Sort by priority and confidence
        priority_order = {
            RecommendationPriority.CRITICAL: 0,
            RecommendationPriority.HIGH: 1,
            RecommendationPriority.MEDIUM: 2,
            RecommendationPriority.LOW: 3
        }
        
        recommendations.sort(
            key=lambda r: (priority_order[r.priority], -r.confidence)
        )
        
        return recommendations[:limit]
    
    def _determine_priority(self, action_concept: Concept, confidence: float) -> RecommendationPriority:
        """Determine priority based on concept attributes and confidence"""
        urgency = action_concept.attributes.get("urgency", "medium")
        
        if urgency == "urgent" or confidence > 0.9:
            return RecommendationPriority.CRITICAL
        elif urgency == "high" or confidence > 0.7:
            return RecommendationPriority.HIGH
        elif urgency == "medium" or confidence > 0.5:
            return RecommendationPriority.MEDIUM
        else:
            return RecommendationPriority.LOW
    
    def _generate_reason(
        self,
        entity_type: str,
        entity_id: str,
        action_concept: Concept
    ) -> str:
        """Generate a human-readable reason for the recommendation"""
        binding = self.kg.get_entity_binding(entity_type, entity_id)
        
        if not binding:
            return f"Recommended action: {action_concept.name}"
            
        triggering_concepts = []
        for concept_id in binding.concepts:
            concept = self.kg.get_concept(concept_id)
            if concept and concept.concept_type == ConceptType.CATEGORY:
                triggering_concepts.append(concept.name)
                
        if triggering_concepts:
            return f"Based on: {', '.join(triggering_concepts[:3])}"
        
        return f"Recommended to improve engagement"


class ContentRecommendationService(RecommendationService):
    """
    Recommends relevant content based on entity interests and stage.
    """
    
    CONTENT_MAPPING = {
        "stage_qualification": [
            {"type": "case_study", "title": "Customer Success Stories"},
            {"type": "overview", "title": "Product Overview"},
            {"type": "roi_calculator", "title": "ROI Calculator"}
        ],
        "stage_discovery": [
            {"type": "demo_video", "title": "Product Demo Video"},
            {"type": "whitepaper", "title": "Industry Whitepaper"},
            {"type": "comparison", "title": "Competitive Comparison"}
        ],
        "stage_proposal": [
            {"type": "pricing", "title": "Pricing Guide"},
            {"type": "implementation", "title": "Implementation Guide"},
            {"type": "security", "title": "Security Documentation"}
        ],
        "stage_negotiation": [
            {"type": "contract", "title": "Contract Templates"},
            {"type": "sla", "title": "SLA Documentation"},
            {"type": "onboarding", "title": "Onboarding Plan"}
        ],
        "health_at_risk": [
            {"type": "best_practices", "title": "Best Practices Guide"},
            {"type": "training", "title": "Training Resources"},
            {"type": "support", "title": "Support Portal Access"}
        ],
        "health_critical": [
            {"type": "exec_summary", "title": "Executive Summary"},
            {"type": "rescue_plan", "title": "Success Recovery Plan"},
            {"type": "escalation", "title": "Dedicated Support Options"}
        ]
    }
    
    def get_recommendations(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 5
    ) -> List[Recommendation]:
        """Get content recommendations based on entity stage and state"""
        recommendations = []
        binding = self.kg.get_entity_binding(entity_type, entity_id)
        
        if not binding:
            return []
            
        seen_types = set()
        
        for concept_id in binding.concepts:
            if concept_id in self.CONTENT_MAPPING:
                for content in self.CONTENT_MAPPING[concept_id]:
                    if content["type"] not in seen_types:
                        seen_types.add(content["type"])
                        
                        rec = Recommendation(
                            id=f"content_{entity_id}_{content['type']}",
                            title=content["title"],
                            description=f"Recommended {content['type']} for current stage",
                            action_type="share_content",
                            priority=RecommendationPriority.MEDIUM,
                            confidence=0.7,
                            reason=f"Relevant for {concept_id} stage",
                            metadata={
                                "content_type": content["type"],
                                "triggering_concept": concept_id
                            }
                        )
                        recommendations.append(rec)
                        
        return recommendations[:limit]
