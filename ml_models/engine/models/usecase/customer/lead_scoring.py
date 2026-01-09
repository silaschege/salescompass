# Lead Scoring model implementation based on XGBoost
from typing import Dict, Any
import pandas as pd
import numpy as np
from sklearn.exceptions import NotFittedError

from ml_models.engine.models.foundation.xgboost import XGBoostModel
from ml_models.infrastructure.config.ontology_config import ModelSpecification, ModelType

class LeadScoringXGBoostModel(XGBoostModel):
    """
    Specialized XGBoost model for lead scoring with domain-specific features.
    """
    
    def __init__(self, model_spec: ModelSpecification):
        """
        Initialize the Lead Scoring XGBoost model.
        
        Args:
            model_spec: Model specification from the ontology
        """
        # Ensure the model spec is for lead scoring
        if model_spec.model_type != ModelType.LEAD_SCORING:
            raise ValueError(f"LeadScoringXGBoostModel expects model_type=ModelType.LEAD_SCORING, got '{model_spec.model_type}'")
        
        super().__init__(model_spec)
        
        # Additional configuration specific to lead scoring
        self.probability_threshold = 0.5  # Default threshold for classification
    
    def set_probability_threshold(self, threshold: float):
        """
        Set the probability threshold for classification.
        
        Args:
            threshold: Probability threshold (0-1)
        """
        if not 0 <= threshold <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        
        self.probability_threshold = threshold
    
    def predict_with_confidence(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """
        Make predictions with confidence scores.
        
        Args:
            X: Features to predict on
            
        Returns:
            Dictionary with predictions, probabilities, and confidence scores
        """
        if not self.is_trained:
            raise NotFittedError("Model must be trained before making predictions")
        
        # Validate features
        if not self.validate_features(X):
            raise ValueError("Feature validation failed")
        
        # Get prediction probabilities
        probas = self.model.predict_proba(X)
        
        # Calculate predictions based on threshold
        predictions = (probas[:, 1] >= self.probability_threshold).astype(int)
        
        # Calculate confidence as the max probability (distance from 0.5)
        confidence = np.abs(probas[:, 1] - 0.5) * 2  # Scale to 0-1 range
        
        return {
            'predictions': predictions,
            'probabilities': probas[:, 1],  # Probability of positive class
            'confidence': confidence,
            'probability_threshold': self.probability_threshold
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model including lead scoring specific details.
        
        Returns:
            Dictionary with model information
        """
        base_info = super().get_model_info()
        base_info['probability_threshold'] = self.probability_threshold
        base_info['model_purpose'] = 'Lead Scoring'
        
        return base_info
    
    def enable_early_stopping(self, X_val: pd.DataFrame, y_val: pd.Series, 
                            patience: int = 10, metric: str = 'logloss'):
        """
        Enable early stopping during training with validation data.
        
        Args:
            X_val: Validation features
            y_val: Validation targets
            patience: Number of rounds with no improvement to wait
            metric: Evaluation metric to monitor
        """
        if not self.is_trained:
            # Store validation data for when training occurs
            self.validation_data = (X_val, y_val)
            self.early_stopping_params = {
                'patience': patience,
                'metric': metric
            }
        else:
            # If model is already trained, we can't apply early stopping
            raise ValueError("Early stopping can only be set before training")
