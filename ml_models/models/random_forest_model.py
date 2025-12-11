# Random Forest model implementation for ML Models
# Implements the Random Forest algorithm for lead scoring

from typing import Dict, Any
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import NotFittedError

from .base_model import BaseModel, ModelType
from ..config.ontology_config import ModelSpecification


class RandomForestModel(BaseModel):
    """
    Random Forest model implementation for lead scoring.
    This model uses ensemble learning with multiple decision trees to make predictions.
    """
    
    def __init__(self, model_spec: ModelSpecification):
        """
        Initialize the Random Forest model.
        
        Args:
            model_spec: Model specification from the ontology
        """
        if model_spec.algorithm.lower() != "randomforest":
            raise ValueError(f"RandomForestModel expects algorithm='RandomForest', got '{model_spec.algorithm}'")
        
        super().__init__(model_spec)
        
        # Initialize the Random Forest classifier with hyperparameters from spec
        hyperparams = model_spec.hyperparameters
        self.model = RandomForestClassifier(
            n_estimators=hyperparams.get('n_estimators', 100),
            max_depth=hyperparams.get('max_depth', 10),
            min_samples_split=hyperparams.get('min_samples_split', 2),
            min_samples_leaf=hyperparams.get('min_samples_leaf', 1),
            max_features=hyperparams.get('max_features', 'sqrt'),
            random_state=hyperparams.get('random_state', 42),
            n_jobs=hyperparams.get('n_jobs', -1),
            class_weight=hyperparams.get('class_weight', 'balanced')
        )
    
    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> Dict[str, Any]:
        """
        Train the Random Forest model on the provided data.
        
        Args:
            X: Training features
            y: Training targets
            **kwargs: Additional training parameters
            
        Returns:
            Dictionary with training results and metrics
        """
        # Validate features
        if not self.validate_features(X):
            raise ValueError("Feature validation failed")
        
        # Store feature names
        self.feature_names = list(X.columns)
        
        # Train the model
        self.model.fit(X, y)
        
        # Mark as trained
        self.is_trained = True
        self.last_trained = pd.Timestamp.now()
        
        # Record training in history
        training_record = {
            'timestamp': self.last_trained,
            'n_samples': X.shape[0],
            'n_features': X.shape[1],
            'hyperparameters': self.model.get_params()
        }
        self.training_history.append(training_record)
        
        # Calculate and store feature importances
        feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
        self.update_performance_metrics({'feature_importance': feature_importance})
        
        # Return training results
        results = {
            'status': 'success',
            'n_samples': X.shape[0],
            'n_features': X.shape[1],
            'model_type': 'RandomForest',
            'training_time': 'N/A'  # Actual training time would require timing the fit method
        }
        
        return results
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions on the provided data.
        
        Args:
            X: Features to predict on
            
        Returns:
            Array of predictions
        """
        if not self.is_trained:
            raise NotFittedError("Model must be trained before making predictions")
        
        # Validate features
        if not self.validate_features(X):
            raise ValueError("Feature validation failed")
        
        # Make predictions
        return self.model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get prediction probabilities for the provided data.
        
        Args:
            X: Features to predict on
            
        Returns:
            Array of prediction probabilities
        """
        if not self.is_trained:
            raise NotFittedError("Model must be trained before making predictions")
        
        # Validate features
        if not self.validate_features(X):
            raise ValueError("Feature validation failed")
        
        # Get prediction probabilities
        return self.model.predict_proba(X)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance scores from the trained model.
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        if not self.is_trained:
            return {}
        
        return dict(zip(self.feature_names, self.model.feature_importances_))
    
    def update_hyperparameters(self, **hyperparams):
        """
        Update the model's hyperparameters.
        
        Args:
            **hyperparams: Hyperparameters to update
        """
        # Update the model's hyperparameters
        self.model.set_params(**hyperparams)
        
        # Update the model spec as well
        self.model_spec.hyperparameters.update(hyperparams)


class LeadScoringRandomForestModel(RandomForestModel):
    """
    Specialized Random Forest model for lead scoring with domain-specific features.
    """
    
    def __init__(self, model_spec: ModelSpecification):
        """
        Initialize the Lead Scoring Random Forest model.
        
        Args:
            model_spec: Model specification from the ontology
        """
        # Ensure the model spec is for lead scoring
        if model_spec.model_type != ModelType.LEAD_SCORING:
            raise ValueError(f"LeadScoringRandomForestModel expects model_type=ModelType.LEAD_SCORING, got '{model_spec.model_type}'")
        
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
