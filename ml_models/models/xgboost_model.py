# XGBoost model implementation for ML Models
# Implements the XGBoost algorithm for lead scoring

from typing import Dict, Any
import pandas as pd
import numpy as np
from sklearn.exceptions import NotFittedError
import xgboost as xgb

from .base_model import BaseModel, ModelType
from ..config.ontology_config import ModelSpecification


class XGBoostModel(BaseModel):
    """
    XGBoost model implementation for lead scoring.
    This model uses gradient boosting to make predictions.
    """
    
    def __init__(self, model_spec: ModelSpecification):
        """
        Initialize the XGBoost model.
        
        Args:
            model_spec: Model specification from the ontology
        """
        if model_spec.algorithm.lower() != "xgboost":
            raise ValueError(f"XGBoostModel expects algorithm='XGBoost', got '{model_spec.algorithm}'")
        
        super().__init__(model_spec)
        
        # Initialize the XGBoost classifier with hyperparameters from spec
        hyperparams = model_spec.hyperparameters
        self.model = xgb.XGBClassifier(
            n_estimators=hyperparams.get('n_estimators', 10),
            max_depth=hyperparams.get('max_depth', 6),
            learning_rate=hyperparams.get('learning_rate', 0.3),
            subsample=hyperparams.get('subsample', 1),
            colsample_bytree=hyperparams.get('colsample_bytree', 1),
            reg_alpha=hyperparams.get('reg_alpha', 0),
            reg_lambda=hyperparams.get('reg_lambda', 1),
            random_state=hyperparams.get('random_state', 42),
            n_jobs=hyperparams.get('n_jobs', -1),
            objective=hyperparams.get('objective', 'binary:logistic'),
            eval_metric=hyperparams.get('eval_metric', 'logloss')
        )
    
    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> Dict[str, Any]:
        """
        Train the XGBoost model on the provided data.
        
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
        feature_importance = self.model.get_booster().get_score(importance_type='weight')
        # Convert to our format (map feature indices to names)
        feature_importance_named = {}
        for idx, importance in feature_importance.items():
            # XGBoost internally names features as f0, f1, etc.
            feature_idx = int(idx[1:])  # Remove 'f' prefix
            if feature_idx < len(self.feature_names):
                feature_importance_named[self.feature_names[feature_idx]] = importance
        
        self.update_performance_metrics({'feature_importance': feature_importance_named})
        
        # Return training results
        results = {
            'status': 'success',
            'n_samples': X.shape[0],
            'n_features': X.shape[1],
            'model_type': 'XGBoost',
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
        
        # Get feature importance from XGBoost
        importance_scores = self.model.get_booster().get_score(importance_type='weight')
        
        # Map feature indices back to feature names
        feature_importance = {}
        for idx, importance in importance_scores.items():
            # XGBoost internally names features as f0, f1, etc.
            feature_idx = int(idx[1:])  # Remove 'f' prefix
            if feature_idx < len(self.feature_names):
                feature_importance[self.feature_names[feature_idx]] = importance
        
        return feature_importance
    
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
