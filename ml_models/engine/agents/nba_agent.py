"""
Next Best Action (NBA) Agent.
Uses Reinforcement Learning (Contextual Bandit) to recommend optimal sales actions.
"""

import numpy as np
from typing import Dict, Any, List, Optional
import logging
from .action_agent import BaseActionAgent

class NBA_Agent(BaseActionAgent):
    """
    Agent that learns optimal sales actions through Reinforcement Learning.
    """
    
    def __init__(self, actions: List[str]):
        super().__init__("next_best_action")
        self.actions = actions
        self.n_actions = len(actions)
        # Simple policy storage (context_dim, n_actions)
        # Using a dictionary for context-to-policy mapping for simplicity in MVP
        self.policy_weights: Dict[str, np.ndarray] = {} 
        self.learning_rate = 0.1
        self.epsilon = 0.1  # Exploration rate

    def evaluate_and_act(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recommends an action based on context.
        """
        state_key = self._get_state_key(context)
        
        # Epsilon-greedy selection
        if np.random.random() < self.epsilon:
            action_idx = np.random.randint(self.n_actions)
        else:
            action_idx = self._get_best_action(state_key)
            
        action = self.actions[action_idx]
        
        return {
            "status": "recommended",
            "action": action,
            "action_id": action_idx,
            "state_key": state_key
        }

    def update_policy(self, state_key: str, action_idx: int, reward: float):
        """
        Updates the policy based on the reward received.
        """
        if state_key not in self.policy_weights:
            self.policy_weights[state_key] = np.zeros(self.n_actions)
            
        # Standard Q-update (Simplified for bandit)
        current_val = self.policy_weights[state_key][action_idx]
        self.policy_weights[state_key][action_idx] = current_val + self.learning_rate * (reward - current_val)
        
        self.logger.info(f"Updated policy for {state_key} action {action_idx}: Reward={reward}")

    def _get_state_key(self, context: Dict[str, Any]) -> str:
        # Create a simplified state representation from context
        # e.g., "industry_tech_score_high"
        industry = context.get('industry', 'unknown')
        score = context.get('lead_score', 0)
        score_bucket = "high" if score >= 80 else "med" if score >= 50 else "low"
        return f"{industry}_{score_bucket}"

    def _get_best_action(self, state_key: str) -> int:
        if state_key not in self.policy_weights:
            return np.random.randint(self.n_actions)
        return np.argmax(self.policy_weights[state_key])
