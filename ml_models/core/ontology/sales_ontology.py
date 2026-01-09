"""
Sales Domain Ontology for SalesCompass ML

This module defines the ontological structure for sales-related concepts
including leads, opportunities, pipelines, and sales activities.
"""

from .base import (
    Ontology, Concept, Relationship,
    ConceptType, RelationshipType, OntologyRegistry
)


class SalesOntology(Ontology):
    """
    Sales domain ontology covering:
    - Lead lifecycle
    - Opportunity stages
    - Sales activities
    - Win/loss factors
    - Revenue predictions
    """
    
    def __init__(self):
        super().__init__(name="sales_ontology", version="1.0.0")
        self.initialize()
        OntologyRegistry.register(self)
        
    def initialize(self) -> None:
        """Initialize sales domain concepts and relationships"""
        self._init_lead_concepts()
        self._init_opportunity_concepts()
        self._init_activity_concepts()
        self._init_outcome_concepts()
        self._init_relationships()
        
    def _init_lead_concepts(self) -> None:
        """Define lead-related concepts"""
        # Lead entity
        lead = Concept(
            id="lead",
            name="Lead",
            concept_type=ConceptType.ENTITY,
            attributes={
                "description": "A potential customer showing interest",
                "key_fields": ["score", "status", "source", "industry"]
            }
        )
        self.add_concept(lead)
        
        # Lead categories
        for category_data in [
            ("hot_lead", "Hot Lead", {"min_score": 80, "priority": "high"}),
            ("warm_lead", "Warm Lead", {"min_score": 50, "max_score": 79, "priority": "medium"}),
            ("cold_lead", "Cold Lead", {"max_score": 49, "priority": "low"}),
            ("mql", "Marketing Qualified Lead", {"qualified_by": "marketing"}),
            ("sql", "Sales Qualified Lead", {"qualified_by": "sales"}),
        ]:
            self.add_concept(Concept(
                id=category_data[0],
                name=category_data[1],
                concept_type=ConceptType.CATEGORY,
                attributes=category_data[2]
            ))
            
        # Lead attributes
        for attr_data in [
            ("lead_score", "Lead Score", {"range": [0, 100], "type": "numeric"}),
            ("lead_status", "Lead Status", {"values": ["new", "contacted", "qualified", "converted", "lost"]}),
            ("lead_source", "Lead Source", {"values": ["web", "referral", "campaign", "event", "cold"]}),
        ]:
            self.add_concept(Concept(
                id=attr_data[0],
                name=attr_data[1],
                concept_type=ConceptType.ATTRIBUTE,
                attributes=attr_data[2]
            ))
            
    def _init_opportunity_concepts(self) -> None:
        """Define opportunity-related concepts"""
        # Opportunity entity
        opportunity = Concept(
            id="opportunity",
            name="Opportunity",
            concept_type=ConceptType.ENTITY,
            attributes={
                "description": "A qualified sales opportunity",
                "key_fields": ["amount", "stage", "probability", "close_date"]
            }
        )
        self.add_concept(opportunity)
        
        # Opportunity stages
        stages = [
            ("stage_qualification", "Qualification", {"order": 1, "probability": 0.1}),
            ("stage_discovery", "Discovery", {"order": 2, "probability": 0.25}),
            ("stage_proposal", "Proposal", {"order": 3, "probability": 0.5}),
            ("stage_negotiation", "Negotiation", {"order": 4, "probability": 0.75}),
            ("stage_closed_won", "Closed Won", {"order": 5, "probability": 1.0, "is_won": True}),
            ("stage_closed_lost", "Closed Lost", {"order": 5, "probability": 0.0, "is_lost": True}),
        ]
        
        for stage_data in stages:
            self.add_concept(Concept(
                id=stage_data[0],
                name=stage_data[1],
                concept_type=ConceptType.CATEGORY,
                attributes=stage_data[2]
            ))
            
        # Opportunity metrics
        for metric_data in [
            ("win_probability", "Win Probability", {"range": [0, 1], "unit": "probability"}),
            ("deal_size", "Deal Size", {"unit": "currency"}),
            ("sales_velocity", "Sales Velocity", {"formula": "value * probability / days"}),
        ]:
            self.add_concept(Concept(
                id=metric_data[0],
                name=metric_data[1],
                concept_type=ConceptType.METRIC,
                attributes=metric_data[2]
            ))
            
    def _init_activity_concepts(self) -> None:
        """Define sales activity concepts"""
        # Activity events
        activities = [
            ("email_sent", "Email Sent", {"channel": "email", "direction": "outbound"}),
            ("email_opened", "Email Opened", {"channel": "email", "direction": "inbound"}),
            ("call_made", "Call Made", {"channel": "phone", "direction": "outbound"}),
            ("call_received", "Call Received", {"channel": "phone", "direction": "inbound"}),
            ("meeting_held", "Meeting Held", {"channel": "meeting"}),
            ("proposal_sent", "Proposal Sent", {"channel": "document"}),
            ("proposal_viewed", "Proposal Viewed", {"channel": "document", "direction": "inbound"}),
        ]
        
        for activity_data in activities:
            self.add_concept(Concept(
                id=activity_data[0],
                name=activity_data[1],
                concept_type=ConceptType.EVENT,
                attributes=activity_data[2]
            ))
            
        # Recommended actions
        actions = [
            ("action_call", "Make a Call", {"priority": "high", "timing": "immediate"}),
            ("action_email", "Send Email", {"priority": "medium", "timing": "same_day"}),
            ("action_meeting", "Schedule Meeting", {"priority": "high", "timing": "this_week"}),
            ("action_proposal", "Send Proposal", {"priority": "high", "timing": "after_discovery"}),
            ("action_followup", "Follow Up", {"priority": "medium", "timing": "3_days"}),
        ]
        
        for action_data in actions:
            self.add_concept(Concept(
                id=action_data[0],
                name=action_data[1],
                concept_type=ConceptType.ACTION,
                attributes=action_data[2]
            ))
            
    def _init_outcome_concepts(self) -> None:
        """Define outcome-related concepts"""
        # Win factors
        win_factors = [
            ("wf_strong_engagement", "Strong Engagement", {"impact": 0.3}),
            ("wf_champion_identified", "Champion Identified", {"impact": 0.25}),
            ("wf_budget_confirmed", "Budget Confirmed", {"impact": 0.2}),
            ("wf_timeline_defined", "Timeline Defined", {"impact": 0.15}),
            ("wf_decision_makers_engaged", "Decision Makers Engaged", {"impact": 0.2}),
        ]
        
        for factor_data in win_factors:
            self.add_concept(Concept(
                id=factor_data[0],
                name=factor_data[1],
                concept_type=ConceptType.CATEGORY,
                attributes={"factor_type": "win", **factor_data[2]}
            ))
            
        # Loss factors
        loss_factors = [
            ("lf_no_budget", "No Budget", {"impact": -0.3}),
            ("lf_competitor_won", "Competitor Won", {"impact": -0.25}),
            ("lf_no_decision", "No Decision Made", {"impact": -0.2}),
            ("lf_timing_not_right", "Timing Not Right", {"impact": -0.15}),
            ("lf_poor_engagement", "Poor Engagement", {"impact": -0.25}),
        ]
        
        for factor_data in loss_factors:
            self.add_concept(Concept(
                id=factor_data[0],
                name=factor_data[1],
                concept_type=ConceptType.CATEGORY,
                attributes={"factor_type": "loss", **factor_data[2]}
            ))
            
    def _init_relationships(self) -> None:
        """Define relationships between sales concepts"""
        # Lead category inheritance
        lead = self.get_concept("lead")
        for cat_id in ["hot_lead", "warm_lead", "cold_lead", "mql", "sql"]:
            cat = self.get_concept(cat_id)
            if cat:
                self.add_relationship(Relationship(
                    source=cat,
                    target=lead,
                    relationship_type=RelationshipType.IS_A
                ))
                
        # Lead to Opportunity conversion
        opportunity = self.get_concept("opportunity")
        sql = self.get_concept("sql")
        if sql and opportunity:
            self.add_relationship(Relationship(
                source=sql,
                target=opportunity,
                relationship_type=RelationshipType.PRECEDES,
                properties={"conversion_type": "qualification"}
            ))
            
        # Stage progression
        stage_order = ["stage_qualification", "stage_discovery", "stage_proposal", "stage_negotiation"]
        for i in range(len(stage_order) - 1):
            source_stage = self.get_concept(stage_order[i])
            target_stage = self.get_concept(stage_order[i + 1])
            if source_stage and target_stage:
                self.add_relationship(Relationship(
                    source=source_stage,
                    target=target_stage,
                    relationship_type=RelationshipType.PRECEDES
                ))
                
        # Activity influences win probability
        win_prob = self.get_concept("win_probability")
        for activity_id in ["email_opened", "call_received", "meeting_held", "proposal_viewed"]:
            activity = self.get_concept(activity_id)
            if activity and win_prob:
                self.add_relationship(Relationship(
                    source=activity,
                    target=win_prob,
                    relationship_type=RelationshipType.INFLUENCES,
                    weight=0.1
                ))
                
        # Score recommends action
        hot_lead = self.get_concept("hot_lead")
        action_call = self.get_concept("action_call")
        if hot_lead and action_call:
            self.add_relationship(Relationship(
                source=hot_lead,
                target=action_call,
                relationship_type=RelationshipType.RECOMMENDS,
                confidence=0.9
            ))
            
        # Win factors influence probability
        for wf_id in ["wf_strong_engagement", "wf_champion_identified", "wf_budget_confirmed"]:
            factor = self.get_concept(wf_id)
            if factor and win_prob:
                self.add_relationship(Relationship(
                    source=factor,
                    target=win_prob,
                    relationship_type=RelationshipType.INFLUENCES,
                    weight=factor.attributes.get("impact", 0.1)
                ))


# Singleton instance
_sales_ontology = None

def get_sales_ontology() -> SalesOntology:
    """Get the singleton sales ontology instance"""
    global _sales_ontology
    if _sales_ontology is None:
        _sales_ontology = SalesOntology()
    return _sales_ontology
