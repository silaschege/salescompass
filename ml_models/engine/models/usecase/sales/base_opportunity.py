# Opportunities ML Models Package
# Contains implementations for deal scoring and win probability prediction

from typing import Dict, Any
import pandas as pd
import numpy as np
from ml_models.engine.models.foundation.base_model import BaseModel


class BaseOpportunityModel(BaseModel):
    """
    Base class for all opportunity-related ML models
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        Initialize the base opportunity model
        
        Args:
            model_config: Configuration dictionary for the model
        """
        # Call BaseModel init with a dummy spec if config is a dict, 
        # or handle it appropriately. For now, assuming model_config 
        # might be a dict or a spec depending on how it's called.
        # This is a bridge between the old and new system.
        super().__init__(model_config) 
        self.model_config = model_config
        self.model = None
        self.is_trained = False
    
    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the opportunity data for model training/inference
        
        Args:
            data: Raw opportunity data
            
        Returns:
            Processed data ready for model consumption
        """
        # Implementation will be in subclasses
        raise NotImplementedError
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Train the model with the provided data
        
        Args:
            X: Feature data
            y: Target values
            
        Returns:
            Dictionary with training metrics
        """
        raise NotImplementedError
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions using the trained model
        
        Args:
            X: Feature data
            
        Returns:
            Predictions
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        return self.model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make probability predictions using the trained model
        
        Args:
            X: Feature data
            
        Returns:
            Prediction probabilities
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
            
        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X)
        else:
            raise NotImplementedError("Model does not support probability predictions")