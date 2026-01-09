import logging
from typing import List, Any
from .knowledge_graph import get_knowledge_graph
from .ontology.base import Concept, ConceptType

logger = logging.getLogger(__name__)

class KnowledgeGraphSynchronizer:
    """
    Orchestrates dynamic updates of the Knowledge Graph from CRM data.
    """
    
    def __init__(self):
        self.kg = get_knowledge_graph()
        
    def sync_leads(self, leads_queryset: List[Any]):
        """Syncs Lead data into KG entities"""
        for lead in leads_queryset:
            # Create a concept or binding for this lead
            concept_ids = ["lead_generic"]
            if lead.status == 'hot':
                concept_ids.append("hot_lead")
            
            # Map industry and company size
            if lead.industry:
                concept_ids.append(f"industry_{lead.industry.lower()}")
            
            self.kg.bind_entity(
                entity_type="lead",
                entity_id=str(lead.id),
                concept_ids=concept_ids,
                metadata={
                    "company": lead.company,
                    "score": getattr(lead, 'lead_score', 0)
                }
            )
            
    def sync_opportunities(self, opps_queryset: List[Any]):
        """Syncs Opportunity data into KG entities"""
        for opp in opps_queryset:
            concept_ids = ["opportunity_generic"]
            if opp.amount > 100000:
                concept_ids.append("enterprise_deal")
            
            self.kg.bind_entity(
                entity_type="opportunity",
                entity_id=str(opp.id),
                concept_ids=concept_ids,
                metadata={
                    "amount": float(opp.amount),
                    "stage": opp.stage.opportunity_stage_name
                }
            )
            
    def trigger_full_refresh(self):
        """
        Placeholder for background job that sweeps all core models.
        """
        logger.info("Triggering full KG refresh from CRM data...")
        # In actual implementation, this would import Django models
        # and iterate over querysets.
