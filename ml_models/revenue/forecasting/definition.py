from dataclasses import dataclass
from typing import List, Optional
from ml_models.shared.base_model import BaseModel
from ml_models.config.ontology_config import ModelSpecification, ModelType

class RevenueForecastingModel(BaseModel):
    """
    Model for forecasting revenue based on open opportunities.
    Currently maps to the 'heuristic' approach but designed to wrap XGBoost/Regression later.
    """
    
    def __init__(self, model_spec: Optional[ModelSpecification] = None):
        if model_spec is None:
            # Default spec if not provided
            model_spec = ModelSpecification(
                model_id="revenue_forecast_v1",
                name="Revenue Forecast Model",
                model_type=ModelType.REVENUE_FORECAST,
                description="Forecasts revenue from open opportunities",
                version="1.0.0",
                algorithm="heuristic_weighted",
                features=[],
                target_variable="revenue",
                hyperparameters={},
                performance_metrics=["error"],
                dependencies=[]
            )
        super().__init__(model_spec)
        
    def train(self, X, y, **kwargs):
        # Heuristic model doesn't need training, but we implement interface
        self.is_trained = True
        return {"status": "skipped", "reason": "heuristic_model"}
        
    def predict(self, X):
        """
        Predict revenue potential.
        X should contain: 'amount', 'probability'
        """
        # Simple heuristic: amount * probability
        if 'amount' not in X.columns or 'probability' not in X.columns:
            raise ValueError("Input must contain 'amount' and 'probability' columns")
            
        return X['amount'] * X['probability']

    def predict_proba(self, X):
        # Not applicable for regression
        return None
