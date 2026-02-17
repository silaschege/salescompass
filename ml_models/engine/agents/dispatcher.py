"""
Action Agent Dispatcher.
Orchestrates autonomous agents and routes ML outcomes to appropriate handlers.
"""

from typing import Dict, Any, List, Optional, Type
import logging
from .action_agent import BaseActionAgent, LeadNurtureAgent
from .nba_agent import NBA_Agent

class AgentDispatcher:
    """
    Dispatcher that manages multiple agents and routes evaluation requests.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("agent.dispatcher")
        self._agents: Dict[str, BaseActionAgent] = {}
        self._register_default_agents()

    def _register_default_agents(self):
        """Registers the built-in agents."""
        self.register_agent(LeadNurtureAgent())
        self.register_agent(NBA_Agent(actions=["send_email", "call", "schedule_demo", "discount_offer"]))

    def register_agent(self, agent: BaseActionAgent):
        """Registers a new agent instance."""
        self._agents[agent.name] = agent
        self.logger.info(f"Agent '{agent.name}' registered with dispatcher.")

    def dispatch(self, agent_name: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Dispatches a context to a specific agent.
        """
        agent = self._agents.get(agent_name)
        if not agent:
            self.logger.error(f"No agent found with name: {agent_name}")
            return None
            
        try:
            return agent.evaluate_and_act(context)
        except Exception as e:
            self.logger.error(f"Error executing agent {agent_name}: {str(e)}")
            return {"status": "error", "message": str(e)}

    def broadcast(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends context to all registered agents for evaluation.
        Relevant for broad triggers like 'High Performance Opportunity'.
        """
        results = {}
        for name, agent in self._agents.items():
            try:
                result = agent.evaluate_and_act(context)
                results[name] = result
            except Exception as e:
                results[name] = {"status": "error", "message": str(e)}
        return results

# Singleton instance for global access
dispatcher = AgentDispatcher()
