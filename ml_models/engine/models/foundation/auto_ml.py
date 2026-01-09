# AutoML Pipeline implementation for ML Models
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import logging
from datetime import datetime

from ml_models.engine.models.foundation.base_model import BaseModel, model_registry
from ml_models.infrastructure.config.ontology_config import ModelSpecification, ModelType as OntModelType
from ml_models.engine.models.foundation.model_factory import ModelFactory

class AutoMLPipeline:
    """
    Automated Machine Learning pipeline for model selection and optimization.
    Coordinates multiple foundational models to find the best performer for a given task.
    """
    
    def __init__(self, task_type: OntModelType, candidate_models: Optional[List[str]] = None):
        self.task_type = task_type
        # Dynamically fetch available algorithms from the factory if none provided
        self.candidate_models = candidate_models or ModelFactory.get_available_algorithms()
        self.results = []
        self.best_model: Optional[BaseModel] = None
        self.logger = logging.getLogger(__name__)

    def run(self, X: pd.DataFrame, y: pd.Series, validation_split: float = 0.2) -> Dict[str, Any]:
        """
        Executes the AutoML process:
        1. Split data
        2. Train all candidate models
        3. Evaluate and rank
        4. Select winner
        """
        from sklearn.model_selection import train_test_split
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=validation_split, random_state=42)
        
        self.logger.info(f"Starting AutoML for {self.task_type.value} with {len(self.candidate_models)} candidates")
        
        for model_name in self.candidate_models:
            try:
                model_instance = self._instantiate_candidate(model_name)
                if not model_instance:
                    continue
                
                # Train
                start_time = datetime.now()
                model_instance.train(X_train, y_train)
                end_time = datetime.now()
                
                # Evaluate
                metrics = model_instance.evaluate(X_val, y_val)
                duration = (end_time - start_time).total_seconds()
                
                result = {
                    'model_name': model_name,
                    'instance': model_instance,
                    'metrics': metrics,
                    'training_duration': duration,
                    'timestamp': datetime.now()
                }
                self.results.append(result)
                self.logger.info(f"Model {model_name} finished: Accuracy={metrics.get('accuracy', 0):.4f}")
                
            except Exception as e:
                self.logger.error(f"AutoML failed for model {model_name}: {str(e)}")

        # Ranking and Selection
        if self.results:
            self.results.sort(key=lambda x: x['metrics'].get('f1_score', 0) if self.task_type == OntModelType.LEAD_SCORING else x['metrics'].get('accuracy', 0), reverse=True)
            self.best_model = self.results[0]['instance']
            self.logger.info(f"AutoML Winner: {self.results[0]['model_name']}")
            
        return self._get_summary()

    def _instantiate_candidate(self, name: str) -> Optional[BaseModel]:
        """
        Uses ModelFactory to dynamically create a model instance.
        """
        # Create a generic spec for the candidate
        spec = ModelSpecification(
            model_id=f"automl_{name}_{datetime.now().strftime('%Y%m%d')}",
            model_type=self.task_type,
            name=f"AutoML-{name}",
            description="Auto-generated candidate",
            version="1.0.0",
            features=[], # To be populated by crawler
            target_variable="",
            algorithm=name,
            hyperparameters={},
            performance_metrics=["accuracy", "f1_score"],
            dependencies=[]
        )
        return ModelFactory.create_model(spec)

    def _get_summary(self) -> Dict[str, Any]:
        return {
            'task': self.task_type.value,
            'winner': self.results[0]['model_name'] if self.results else None,
            'all_results': [{k: v for k, v in r.items() if k != 'instance'} for r in self.results]
        }
