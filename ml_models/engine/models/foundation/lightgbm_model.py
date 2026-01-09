# LightGBM model implementation for ML Models
# Implements the LightGBM algorithm for optimized gradient boosting

from typing import Dict, Any
import pandas as pd
import numpy as np
from sklearn.exceptions import NotFittedError
import lightgbm as lgb

from ml_models.engine.models.foundation.base_model import BaseModel, ModelType
from ml_models.infrastructure.config.ontology_config import ModelSpecification


class LightGBMModel(BaseModel):
    """
    LightGBM model implementation for general use.
    This model uses tree-based gradient boosting with histogram-based algorithms.
    """
    
    def __init__(self, model_spec: ModelSpecification):
        """
        Initialize the LightGBM model.
        
        Args:
            model_spec: Model specification from the ontology
        """
        if model_spec.algorithm.lower() != "lightgbm":
            raise ValueError(f"LightGBMModel expects algorithm='LightGBM', got '{model_spec.algorithm}'")
        
        super().__init__(model_spec)
        
        # Initialize the LightGBM classifier with hyperparameters from spec
        hyperparams = model_spec.hyperparameters
        self.model = lgb.LGBMClassifier(
            n_estimators=hyperparams.get('n_estimators', 100),
            max_depth=hyperparams.get('max_depth', -1),
            learning_rate=hyperparams.get('learning_rate', 0.1),
            num_leaves=hyperparams.get('num_leaves', 31),
            subsample=hyperparams.get('subsample', 1.0),
            colsample_bytree=hyperparams.get('colsample_bytree', 1.0),
            reg_alpha=hyperparams.get('reg_alpha', 0.0),
            reg_lambda=hyperparams.get('reg_lambda', 0.0),
            random_state=hyperparams.get('random_state', 42),
            n_jobs=hyperparams.get('n_jobs', -1),
            objective=hyperparams.get('objective', 'binary'),
            metric=hyperparams.get('metric', 'binary_logloss')
        )
    
    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> Dict[str, Any]:
        """
        Train the LightGBM model on the provided data.
        
        Args:
            X: Training features
            y: Training targets
            **kwargs: Additional training parameters
            
        Returns:
            Dictionary with training results and metrics
        """
        # Validate features
        if not self.validate_features(X):
            # If validation fails but no feature names were set, we might be initializing
            if not self.feature_names:
                self.feature_names = list(X.columns)
            else:
                self.logger.warning("Feature validation warnings encountered, proceeding with training")
        
        # Store feature names if not present
        if not self.feature_names:
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
        # LightGBM provides feature importances directly
        importances = self.model.feature_importances_
        feature_importance_named = dict(zip(self.feature_names, importances))
        
        self.update_performance_metrics({'feature_importance': feature_importance_named})
        
        # Return training results
        results = {
            'status': 'success',
            'n_samples': X.shape[0],
            'n_features': X.shape[1],
            'model_type': 'LightGBM',
            'training_time': 'N/A'
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
            self.logger.warning("Feature validation warnings during inference")
        
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
            self.logger.warning("Feature validation warnings during inference")
        
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
        
        importances = self.model.feature_importances_
        # Normalize to 0-1 range for better comparison or leave as split/gain
        # Leaving as raw values for now
        return dict(zip(self.feature_names, float(x) for x in importances))
    
    def update_hyperparameters(self, **hyperparams):
        """
        Update the model's hyperparameters.
        
        Args:
            **hyperparams: Hyperparameters to update
        """
        self.model.set_params(**hyperparams)
        self.model_spec.hyperparameters.update(hyperparams)
