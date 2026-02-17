"""
A/B Testing Framework for ML Models.
Compares different model versions (Champion vs Challenger) in production.
"""

import random
import logging
from typing import Dict, Any, List, Optional
from ml_models.engine.models.foundation.base_model import BaseModel

class ABTestingFramework:
    """
    Manages traffic routing between different model versions.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("infrastructure.monitoring.ab_testing")
        self.experiments: Dict[str, Dict[str, Any]] = {}

    def start_experiment(self, experiment_id: str, champion: BaseModel, challenger: BaseModel, traffic_split: float = 0.5):
        """
        Initializes an A/B test between two models.
        """
        self.experiments[experiment_id] = {
            "champion": champion,
            "challenger": challenger,
            "traffic_split": traffic_split,
            "results": {"champion": [], "challenger": []}
        }
        self.logger.info(f"A/B Test '{experiment_id}' started. Traffic split: {traffic_split*100}% to Challenger.")

    def get_model(self, experiment_id: str) -> Optional[BaseModel]:
        """
        Decides which model to use based on traffic split.
        """
        exp = self.experiments.get(experiment_id)
        if not exp:
            return None
            
        if random.random() < exp["traffic_split"]:
            self.logger.debug(f"Routing to CHALLENGER in {experiment_id}")
            return exp["challenger"]
        else:
            self.logger.debug(f"Routing to CHAMPION in {experiment_id}")
            return exp["champion"]

    def log_result(self, experiment_id: str, model_role: str, outcome: float):
        """
        Logs the outcome for a specific model in the experiment.
        model_role should be 'champion' or 'challenger'.
        """
        exp = self.experiments.get(experiment_id)
        if exp and model_role in exp["results"]:
            exp["results"][model_role].append(outcome)

    def get_summary(self, experiment_id: str) -> Dict[str, Any]:
        """
        Summarizes experiment performance.
        """
        exp = self.experiments.get(experiment_id)
        if not exp: return {}
        
        summary = {}
        for role in ["champion", "challenger"]:
            results = exp["results"][role]
            summary[role] = {
                "count": len(results),
                "avg_outcome": sum(results) / len(results) if results else 0
            }
        return summary
