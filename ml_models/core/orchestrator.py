"""
ML & Agent Orchestrator.
Coordinates the flow from CRM events to Knowledge Graph updates, ML inference, and autonomous agent actions.
"""

from typing import Dict, Any, List, Optional
import logging
from core.knowledge_graph import get_knowledge_graph
from engine.agents.dispatcher import dispatcher
from services.prediction_service import LeadScoringService, OpportunityWinProbabilityService
from infrastructure.compliance.audit_logger import audit_logger

class SystemOrchestrator:
    """
    The 'Brain' of the ML module. Orchestrates cross-component workflows.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ml.orchestrator")
        self.kg = get_knowledge_graph()
        self.lead_service = LeadScoringService()
        self.opp_service = OpportunityWinProbabilityService()

    def handle_lead_update(self, lead_id: str, lead_instance: Any):
        """
        Orchestrates response to a lead being created or updated.
        """
        self.logger.info(f"Orchestrating workflow for Lead: {lead_id}")
        
        # 1. Run ML Scoring
        score_result = self.lead_service.score_lead(lead_instance)
        
        # Log Audit
        audit_logger.log_inference(
            model_id="lead_scoring_v1",
            inputs={"lead_id": lead_id, "industry": getattr(lead_instance, 'industry', 'unknown')},
            outputs=score_result,
            latency_ms=15.0 # Placeholder or measure actual time
        )
        
        # 2. Build Context for Agents
        context = {
            "entity_type": "lead",
            "entity_id": lead_id,
            "score": score_result.get('score', 0),
            "inference_method": score_result.get('method', 'unknown'),
            "industry": getattr(lead_instance, 'industry', 'unknown'),
            "source": getattr(lead_instance, 'lead_source', 'unknown')
        }
        
        # 3. Dispatch to Agents (LeadNurtureAgent is active for leads)
        # Broadcast allows multiple agents to react if registered
        agent_outcomes = dispatcher.broadcast(context)
        
        self.logger.info(f"Lead {lead_id} processed. Score: {context['score']}. Agent actions: {list(agent_outcomes.keys())}")
        return {
            "score": score_result,
            "agent_outcomes": agent_outcomes
        }

    def handle_opportunity_update(self, opp_id: str, opp_instance: Any):
        """
        Orchestrates response to an opportunity update.
        """
        self.logger.info(f"Orchestrating workflow for Opportunity: {opp_id}")
        
        # 1. Run Win Probability Inference
        prob_result = self.opp_service.predict_win_probability(opp_instance)
        
        # Log Audit
        audit_logger.log_inference(
            model_id="win_prob_v1",
            inputs={"opp_id": opp_id, "amount": getattr(opp_instance, 'amount', 0)},
            outputs=prob_result,
            latency_ms=20.0
        )
        
        # 2. Build Context for NBA (Next Best Action) Agent
        context = {
            "entity_type": "opportunity",
            "entity_id": opp_id,
            "win_probability": prob_result.get('probability', 0.0),
            "inference_method": prob_result.get('method', 'unknown'),
            "amount": float(getattr(opp_instance, 'amount', 0)),
            "stage": getattr(opp_instance, 'stage', None).name if getattr(opp_instance, 'stage', None) else 'unknown'
        }
        
        # 3. Activate NBA Agent to recommend next step
        # NBA_Agent specifically handles opportunities in its evaluation logic
        agent_outcomes = dispatcher.dispatch("next_best_action", context)
        
        self.logger.info(f"Opportunity {opp_id} processed. Prob: {context['win_probability']}. NBA Outcome: {agent_outcomes}")
        return {
            "probability": prob_result,
            "agent_outcomes": agent_outcomes
        }

# Singleton Orchestrator
orchestrator = SystemOrchestrator()
