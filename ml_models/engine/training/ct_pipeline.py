"""
Continuous Training (CT) Pipeline.
Automates the process of data ingestion, model training, and performance evaluation.
"""

import pandas as pd
from typing import Dict, Any, Optional
import logging
from datetime import datetime
from ml_models.engine.models.foundation.auto_ml import AutoMLPipeline
from ml_models.infrastructure.config.ontology_config import ModelType
from ml_models.infrastructure.monitoring.versioning import ModelVersioningService

class CT_TrainingPipeline:
    """
    Orchestrates the automated training workflow.
    """
    
    def __init__(self, model_id: str, model_type: ModelType):
        self.model_id = model_id
        self.model_type = model_type
        self.logger = logging.getLogger(f"ct.pipeline.{model_id}")
        self.versioning = ModelVersioningService()

    def run_cycle(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Executes a full training cycle:
        1. Ingest Data (provided as args)
        2. Run AutoML to find best model
        3. Save and Register the new version
        4. (Optional) Auto-promote if accuracy exceeds threshold
        """
        self.logger.info(f"Starting CT cycle for {self.model_id}")
        
        # 1. Train via AutoML
        pipeline = AutoMLPipeline(self.model_type)
        summary = pipeline.run(X, y)
        
        best_instance = pipeline.best_model
        if not best_instance:
            self.logger.error("CT training failed: No best model found.")
            return {"status": "failed", "error": "no_model_trained"}
            
        # 2. Save artifact
        artifact_path = best_instance.save_model()
        
        # 3. Register version
        version_id = self.versioning.register_version(
            model_id=self.model_id,
            artifact_path=artifact_path,
            metrics=best_instance.performance_metrics
        )
        
        self.logger.info(f"CT cycle complete. New version registered: {version_id}")
        
        return {
            "status": "success",
            "version_id": version_id,
            "metrics": best_instance.performance_metrics,
            "artifact_path": artifact_path
        }

    def check_and_retrain(self, current_accuracy: float, threshold: float, data: tuple):
        """
        Triggers retraining if current performance is below threshold.
        """
        if current_accuracy < threshold:
            self.logger.warning(f"Accuracy {current_accuracy} below threshold {threshold}. Triggering retraining.")
            X, y = data
            return self.run_cycle(X, y)
        return {"status": "skipped", "reason": "performance_ok"}
