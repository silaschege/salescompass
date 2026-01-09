from typing import Dict, Any, List, Optional
from datetime import datetime
from .base import Ontology, Concept, Relationship, ConceptType, RelationshipType

class EventOntology(Ontology):
    """
    Ontology for representing and reasoning about business events and activities.
    Covers Meetings, Calls, Emails, and Tasks.
    """
    
    def __init__(self):
        super().__init__(name="EventOntology", version="1.0.0")
        
    def initialize(self) -> None:
        """Initialize core event concepts and relationships"""
        
        # Base Event Concept
        event = Concept(
            id="event",
            name="Event",
            concept_type=ConceptType.EVENT,
            attributes={"description": "A discrete occurrence in time"}
        )
        self.add_concept(event)
        
        # Specific Event Types
        meeting = Concept(
            id="meeting",
            name="Meeting",
            concept_type=ConceptType.EVENT,
            attributes={"modality": "synchronous", "channel": "video/in-person"}
        )
        self.add_concept(meeting)
        
        call = Concept(
            id="call",
            name="Phone Call",
            concept_type=ConceptType.EVENT,
            attributes={"modality": "synchronous", "channel": "voice"}
        )
        self.add_concept(call)
        
        email = Concept(
            id="email",
            name="Email",
            concept_type=ConceptType.EVENT,
            attributes={"modality": "asynchronous", "channel": "text"}
        )
        self.add_concept(email)
        
        task = Concept(
            id="task",
            name="Task",
            concept_type=ConceptType.ACTION,
            attributes={"status": "pending"}
        )
        self.add_concept(task)
        
        # Establish Hierarchy (Meeting IS_A Event)
        self.add_relationship(Relationship(meeting, event, RelationshipType.IS_A))
        self.add_relationship(Relationship(call, event, RelationshipType.IS_A))
        self.add_relationship(Relationship(email, event, RelationshipType.IS_A))
        
        # Participant Concept (Generic)
        participant = Concept(
            id="participant",
            name="Participant",
            concept_type=ConceptType.ENTITY,
            attributes={"role": "attendee"}
        )
        self.add_concept(participant)
        
        # Event has Participants
        self.add_relationship(Relationship(event, participant, RelationshipType.HAS_A))

    def create_meeting_event(self, meeting_id: str, title: str, duration_min: int, participants: List[str]) -> Concept:
        """Factory method to create a concrete meeting instance in the ontology"""
        meeting_concept = Concept(
            id=f"meeting_{meeting_id}",
            name=title,
            concept_type=ConceptType.EVENT,
            attributes={
                "duration_minutes": duration_min, 
                "timestamp": datetime.now().isoformat(),
                "type": "meeting"
            }
        )
        self.add_concept(meeting_concept)
        
        # Link to Base Meeting Class
        base_meeting = self.get_concept("meeting")
        if base_meeting:
            self.add_relationship(Relationship(meeting_concept, base_meeting, RelationshipType.IS_A))
            
        return meeting_concept

    def add_event_outcome(self, event_id: str, outcome: str, sentiment: float) -> None:
        """Enrich an event with outcome and sentiment data"""
        event = self.get_concept(event_id)
        if event:
            event.attributes["outcome"] = outcome
            event.attributes["sentiment_score"] = sentiment
            
            # Check for triggers based on sentiment
            if sentiment < -0.5:
                # Negative sentiment triggers 'Risk' concept if available
                # Logic to be expanded when integrating with Risk/Churn ontology
                pass

