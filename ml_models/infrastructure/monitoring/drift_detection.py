"""
Model Monitoring & Drift Detection Service.
Tracks model performance and data distribution shifts.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List
import logging
from ml_models.infrastructure.config.settings import config
from ml_models.engine.training.ct_pipeline import CT_TrainingPipeline

class MonitoringService:
    """
    Monitors live data for drift and maintains performance logs.
    """
    
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.logger = logging.getLogger(f"monitor.{model_id}")
        self.threshold = config.drift_detection_threshold
        self.performance_history = []

    def check_drift(self, reference_data: pd.DataFrame, current_data: pd.DataFrame) -> bool:
        """
        Calculates simple Population Stability Index (PSI) or similar to detect drift.
        For now, uses a basic mean-shift detection as a placeholder.
        """
        # Simple drift logic: Compare means of numerical features
        num_ref = reference_data.select_dtypes(include=[np.number])
        num_curr = current_data.select_dtypes(include=[np.number])
        
        drift_detected = False
        for col in num_ref.columns:
            if col in num_curr.columns:
                ref_mean = num_ref[col].mean()
                curr_mean = num_curr[col].mean()
                
                # Check absolute percentage change
                if ref_mean != 0:
                    change = abs(curr_mean - ref_mean) / abs(ref_mean)
                    if change > self.threshold:
                        self.logger.warning(f"Drift detected in feature '{col}': {change:.4f} > {self.threshold}")
                        drift_detected = True
                        
        return drift_detected

    def log_performance(self, metrics: Dict[str, float]):
        """Logs current inference performance."""
        entry = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "metrics": metrics
        }
        self.performance_history.append(entry)
        
        # Check if accuracy dropped significantly (simplified)
        if metrics.get('accuracy', 1.0) < config.min_precision_threshold:
            self.logger.error(f"Performance ALERT: Accuracy dropped to {metrics.get('accuracy')}")
            # In a production system, this could trigger a CT_TrainingPipeline run
