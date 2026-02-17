"""
Customer Domain Ontology for SalesCompass ML

This module defines the ontological structure for customer-related concepts
including accounts, contacts, engagement, and customer health.
"""

from .base import (
    Ontology, Concept, Relationship,
    ConceptType, RelationshipType, OntologyRegistry
)


class CustomerOntology(Ontology):
    """
    Customer domain ontology covering:
    - Account types and segments
    - Contact roles and relationships
    - Engagement patterns
    - Customer health and churn risk
    - Lifetime value prediction
    """
    
    def __init__(self):
        super().__init__(name="customer_ontology", version="1.0.0")
        self.initialize()
        OntologyRegistry.register(self)
        
    def initialize(self) -> None:
        """Initialize customer domain concepts and relationships"""
        self._init_account_concepts()
        self._init_contact_concepts()
        self._init_engagement_concepts()
        self._init_health_concepts()
        self._init_relationships()
        
    def _init_account_concepts(self) -> None:
        """Define account-related concepts"""
        # Account entity
        account = Concept(
            id="account",
            name="Account",
            concept_type=ConceptType.ENTITY,
            attributes={
                "description": "A customer organization",
                "key_fields": ["name", "industry", "segment", "arr"]
            }
        )
        self.add_concept(account)
        
        # Account segments
        segments = [
            ("segment_enterprise", "Enterprise", {"min_arr": 100000, "priority": "strategic"}),
            ("segment_mid_market", "Mid-Market", {"min_arr": 25000, "max_arr": 99999, "priority": "high"}),
            ("segment_smb", "SMB", {"max_arr": 24999, "priority": "medium"}),
            ("segment_startup", "Startup", {"characteristics": ["high_growth", "funding"]}),
        ]
        
        for segment_data in segments:
            self.add_concept(Concept(
                id=segment_data[0],
                name=segment_data[1],
                concept_type=ConceptType.CATEGORY,
                attributes=segment_data[2]
            ))
            
        # Account health states
        health_states = [
            ("health_healthy", "Healthy", {"score_range": [80, 100], "churn_risk": "low"}),
            ("health_at_risk", "At Risk", {"score_range": [50, 79], "churn_risk": "medium"}),
            ("health_critical", "Critical", {"score_range": [0, 49], "churn_risk": "high"}),
        ]
        
        for state_data in health_states:
            self.add_concept(Concept(
                id=state_data[0],
                name=state_data[1],
                concept_type=ConceptType.CATEGORY,
                attributes=state_data[2]
            ))
            
    def _init_contact_concepts(self) -> None:
        """Define contact-related concepts"""
        # Contact entity
        contact = Concept(
            id="contact",
            name="Contact",
            concept_type=ConceptType.ENTITY,
            attributes={
                "description": "A person associated with an account",
                "key_fields": ["name", "email", "title", "role"]
            }
        )
        self.add_concept(contact)
        
        # Contact roles
        roles = [
            ("role_champion", "Champion", {"influence": "high", "support": "strong"}),
            ("role_decision_maker", "Decision Maker", {"influence": "high", "authority": "final"}),
            ("role_influencer", "Influencer", {"influence": "medium", "authority": "advisory"}),
            ("role_user", "End User", {"influence": "low", "feedback": "operational"}),
            ("role_blocker", "Blocker", {"influence": "high", "support": "negative"}),
        ]
        
        for role_data in roles:
            self.add_concept(Concept(
                id=role_data[0],
                name=role_data[1],
                concept_type=ConceptType.CATEGORY,
                attributes=role_data[2]
            ))
            
    def _init_engagement_concepts(self) -> None:
        """Define engagement-related concepts"""
        # Engagement patterns
        patterns = [
            ("pattern_active", "Actively Engaged", {"frequency": "high", "recency": "recent"}),
            ("pattern_passive", "Passively Engaged", {"frequency": "medium", "recency": "moderate"}),
            ("pattern_dormant", "Dormant", {"frequency": "low", "recency": "stale"}),
            ("pattern_disengaged", "Disengaged", {"frequency": "none", "recency": "expired"}),
        ]
        
        for pattern_data in patterns:
            self.add_concept(Concept(
                id=pattern_data[0],
                name=pattern_data[1],
                concept_type=ConceptType.CATEGORY,
                attributes=pattern_data[2]
            ))
            
        # Engagement events
        events = [
            ("event_login", "Product Login", {"channel": "product", "weight": 0.5}),
            ("event_feature_use", "Feature Usage", {"channel": "product", "weight": 0.8}),
            ("event_support_request", "Support Request", {"channel": "support", "weight": 0.3}),
            ("event_nps_response", "NPS Response", {"channel": "survey", "weight": 0.6}),
            ("event_renewal", "Contract Renewal", {"channel": "sales", "weight": 1.0}),
            ("event_expansion", "Account Expansion", {"channel": "sales", "weight": 1.0}),
        ]
        
        for event_data in events:
            self.add_concept(Concept(
                id=event_data[0],
                name=event_data[1],
                concept_type=ConceptType.EVENT,
                attributes=event_data[2]
            ))
            
        # Engagement metrics
        metrics = [
            ("engagement_score", "Engagement Score", {"range": [0, 100], "unit": "score"}),
            ("nps_score", "NPS Score", {"range": [-100, 100], "unit": "nps"}),
            ("product_adoption", "Product Adoption Rate", {"range": [0, 1], "unit": "percentage"}),
        ]
        
        for metric_data in metrics:
            self.add_concept(Concept(
                id=metric_data[0],
                name=metric_data[1],
                concept_type=ConceptType.METRIC,
                attributes=metric_data[2]
            ))
            
    def _init_health_concepts(self) -> None:
        """Define customer health and churn concepts"""
        # Health metrics
        health_metrics = [
            ("health_score", "Health Score", {"range": [0, 100], "composite": True}),
            ("churn_risk", "Churn Risk", {"range": [0, 1], "unit": "probability"}),
            ("clv", "Customer Lifetime Value", {"unit": "currency"}),
            ("expansion_potential", "Expansion Potential", {"range": [0, 1], "unit": "probability"}),
        ]
        
        for metric_data in health_metrics:
            self.add_concept(Concept(
                id=metric_data[0],
                name=metric_data[1],
                concept_type=ConceptType.METRIC,
                attributes=metric_data[2]
            ))
            
        # Churn signals
        churn_signals = [
            ("signal_usage_decline", "Usage Decline", {"severity": 0.7}),
            ("signal_support_escalation", "Support Escalation", {"severity": 0.5}),
            ("signal_low_nps", "Low NPS Score", {"severity": 0.6}),
            ("signal_missed_renewal", "Missed Renewal Date", {"severity": 0.9}),
            ("signal_champion_left", "Champion Left Company", {"severity": 0.8}),
        ]
        
        for signal_data in churn_signals:
            self.add_concept(Concept(
                id=signal_data[0],
                name=signal_data[1],
                concept_type=ConceptType.EVENT,
                attributes={"signal_type": "churn", **signal_data[2]}
            ))
            
        # Retention actions
        retention_actions = [
            ("action_exec_outreach", "Executive Outreach", {"urgency": "high"}),
            ("action_success_review", "Success Review Meeting", {"urgency": "medium"}),
            ("action_training_offer", "Training Offer", {"urgency": "medium"}),
            ("action_discount_offer", "Discount Offer", {"urgency": "high"}),
            ("action_feature_preview", "Feature Preview Access", {"urgency": "low"}),
        ]
        
        for action_data in retention_actions:
            self.add_concept(Concept(
                id=action_data[0],
                name=action_data[1],
                concept_type=ConceptType.ACTION,
                attributes=action_data[2]
            ))
            
    def _init_relationships(self) -> None:
        """Define relationships between customer concepts"""
        account = self.get_concept("account")
        contact = self.get_concept("contact")
        
        # Account has contacts
        if account and contact:
            self.add_relationship(Relationship(
                source=account,
                target=contact,
                relationship_type=RelationshipType.HAS_A
            ))
            
        # Segment inheritance
        for segment_id in ["segment_enterprise", "segment_mid_market", "segment_smb", "segment_startup"]:
            segment = self.get_concept(segment_id)
            if segment and account:
                self.add_relationship(Relationship(
                    source=segment,
                    target=account,
                    relationship_type=RelationshipType.IS_A
                ))
                
        # Contact role inheritance
        for role_id in ["role_champion", "role_decision_maker", "role_influencer", "role_user", "role_blocker"]:
            role = self.get_concept(role_id)
            if role and contact:
                self.add_relationship(Relationship(
                    source=role,
                    target=contact,
                    relationship_type=RelationshipType.IS_A
                ))
                
        # Engagement influences health
        engagement_score = self.get_concept("engagement_score")
        health_score = self.get_concept("health_score")
        churn_risk = self.get_concept("churn_risk")
        
        if engagement_score and health_score:
            self.add_relationship(Relationship(
                source=engagement_score,
                target=health_score,
                relationship_type=RelationshipType.INFLUENCES,
                weight=0.4
            ))
            
        if engagement_score and churn_risk:
            self.add_relationship(Relationship(
                source=engagement_score,
                target=churn_risk,
                relationship_type=RelationshipType.CORRELATES_WITH,
                weight=-0.6  # Negative correlation
            ))
            
        # Churn signals trigger actions
        signal_action_map = [
            ("signal_usage_decline", "action_success_review"),
            ("signal_low_nps", "action_exec_outreach"),
            ("signal_champion_left", "action_exec_outreach"),
            ("signal_missed_renewal", "action_discount_offer"),
        ]
        
        for signal_id, action_id in signal_action_map:
            signal = self.get_concept(signal_id)
            action = self.get_concept(action_id)
            if signal and action:
                self.add_relationship(Relationship(
                    source=signal,
                    target=action,
                    relationship_type=RelationshipType.TRIGGERS,
                    confidence=0.8
                ))
                
        # Churn signals influence churn risk
        for signal_id in ["signal_usage_decline", "signal_support_escalation", "signal_low_nps", 
                          "signal_missed_renewal", "signal_champion_left"]:
            signal = self.get_concept(signal_id)
            if signal and churn_risk:
                self.add_relationship(Relationship(
                    source=signal,
                    target=churn_risk,
                    relationship_type=RelationshipType.INFLUENCES,
                    weight=signal.attributes.get("severity", 0.5)
                ))


# Singleton instance
_customer_ontology = None

def get_customer_ontology() -> CustomerOntology:
    """Get the singleton customer ontology instance"""
    global _customer_ontology
    if _customer_ontology is None:
        _customer_ontology = CustomerOntology()
    return _customer_ontology
