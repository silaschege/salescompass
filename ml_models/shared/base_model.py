# Base model class for ML Models
# Defines the common interface and functionality for all ML models

import os
import pickle
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime
import logging
try:
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
except ImportError:
    # Allow running without sklearn for heuristic models/testing
    accuracy_score = precision_score = recall_score = f1_score = roc_auc_score = None

from ..config.ontology_config import ModelSpecification, ModelType
from ..config.settings import config


class BaseModel(ABC):
    """
    Abstract base class for all ML models in the SalesCompass system.
    Defines the common interface and functionality that all models must implement.
    """
    
    def __init__(self, model_spec: ModelSpecification):
        """
        Initialize the base model with a model specification.
        
        Args:
            model_spec: Model specification from the ontology
        """
        self.model_spec = model_spec
        self.model = None
        self.is_trained = False
        self.training_history = []
        self.performance_metrics = {}
        self.feature_names = []
        self.logger = logging.getLogger(__name__)
        
        # Model metadata
        self.created_at = datetime.now()
        self.last_trained = None
        self.version = model_spec.version
        
    @abstractmethod
    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> Dict[str, Any]:
        """
        Train the model on the provided data.
        
        Args:
            X: Training features
            y: Training targets
            **kwargs: Additional training parameters
            
        Returns:
            Dictionary with training results and metrics
        """
        pass
    
    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions on the provided data.
        
        Args:
            X: Features to predict on
            
        Returns:
            Array of predictions
        """
        pass
    
    @abstractmethod
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get prediction probabilities for the provided data.
        
        Args:
            X: Features to predict on
            
        Returns:
            Array of prediction probabilities
        """
        pass
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """
        Evaluate the model on the provided data.
        
        Args:
            X: Features to evaluate on
            y: True targets
            
        Returns:
            Dictionary with evaluation metrics
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        # Make predictions
        y_pred = self.predict(X)
        
        # Calculate metrics based on the model type
        metrics = {}
        
        if self.model_spec.model_type in [ModelType.LEAD_SCORING, ModelType.CONVERSION_PREDICTION]:
            # Binary classification metrics
            metrics['accuracy'] = accuracy_score(y, y_pred)
            metrics['precision'] = precision_score(y, y_pred, zero_division=0)
            metrics['recall'] = recall_score(y, y_pred, zero_division=0)
            metrics['f1_score'] = f1_score(y, y_pred, zero_division=0)
            
            # If the model supports probabilities, calculate AUC
            try:
                y_proba = self.predict_proba(X)[:, 1]  # Get probability of positive class
                metrics['auc_roc'] = roc_auc_score(y, y_proba)
            except:
                self.logger.warning("Could not calculate AUC-ROC - model may not support probabilities")
        
        # Store metrics
        self.performance_metrics = metrics
        
        return metrics
    
    def save_model(self, filepath: Optional[str] = None) -> str:
        """
        Save the trained model to disk.
        
        Args:
            filepath: Path to save the model. If None, uses default path based on model ID.
            
        Returns:
            Path where the model was saved
        """
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        # Generate filepath if not provided
        if filepath is None:
            model_dir = os.path.join(config.model_storage_path, self.model_spec.model_id)
            os.makedirs(model_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(model_dir, f"model_{timestamp}.pkl")
        
        # Create model package with model and metadata
        model_package = {
            'model': self.model,
            'model_spec': self.model_spec,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained,
            'last_trained': self.last_trained,
            'performance_metrics': self.performance_metrics,
            'training_history': self.training_history,
            'version': self.version,
            'created_at': self.created_at
        }
        
        # Save the model package
        with open(filepath, 'wb') as f:
            pickle.dump(model_package, f)
        
        self.logger.info(f"Model saved to {filepath}")
        return filepath
    
    def load_model(self, filepath: str):
        """
        Load a trained model from disk.
        
        Args:
            filepath: Path to the saved model file
        """
        with open(filepath, 'rb') as f:
            model_package = pickle.load(f)
        
        # Restore model attributes
        self.model = model_package['model']
        self.model_spec = model_package['model_spec']
        self.feature_names = model_package['feature_names']
        self.is_trained = model_package['is_trained']
        self.last_trained = model_package['last_trained']
        self.performance_metrics = model_package['performance_metrics']
        self.training_history = model_package['training_history']
        self.version = model_package['version']
        self.created_at = model_package['created_at']
        
        self.logger.info(f"Model loaded from {filepath}")
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Get feature importance scores if available.
        
        Returns:
            Dictionary mapping feature names to importance scores, or None if not available
        """
        if not self.is_trained:
            return None
        
        # Default implementation returns None
        # Subclasses should override this method if they support feature importance
        return None
    
    def validate_features(self, X: pd.DataFrame) -> bool:
        """
        Validate that the input features match the expected features.
        
        Args:
            X: Features to validate
            
        Returns:
            True if features are valid, False otherwise
        """
        if not self.feature_names:
            # If no feature names stored, we can't validate
            return True
        
        # Check if all expected features are present
        missing_features = set(self.feature_names) - set(X.columns)
        if missing_features:
            self.logger.error(f"Missing features: {missing_features}")
            return False
        
        # Check if extra features are present (not necessarily an error, but log it)
        extra_features = set(X.columns) - set(self.feature_names)
        if extra_features:
            self.logger.warning(f"Extra features found: {extra_features}")
        
        return True
    
    def update_performance_metrics(self, metrics: Dict[str, float]):
        """
        Update the model's performance metrics.
        
        Args:
            metrics: Dictionary of performance metrics
        """
        self.performance_metrics.update(metrics)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_id': self.model_spec.model_id,
            'model_type': self.model_spec.model_type.value,
            'name': self.model_spec.name,
            'description': self.model_spec.description,
            'version': self.version,
            'is_trained': self.is_trained,
            'created_at': self.created_at.isoformat(),
            'last_trained': self.last_trained.isoformat() if self.last_trained else None,
            'performance_metrics': self.performance_metrics,
            'feature_names': self.feature_names,
            'algorithm': self.model_spec.algorithm
        }


class ModelRegistry:
    """
    Registry for managing different model instances.
    """
    
    def __init__(self):
        self.models: Dict[str, BaseModel] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_model(self, model: BaseModel):
        """
        Register a model instance.
        
        Args:
            model: Model instance to register
        """
        model_id = model.model_spec.model_id
        self.models[model_id] = model
        self.logger.info(f"Model {model_id} registered")
    
    def get_model(self, model_id: str) -> Optional[BaseModel]:
        """
        Get a registered model instance.
        
        Args:
            model_id: ID of the model to retrieve
            
        Returns:
            Model instance or None if not found
        """
        return self.models.get(model_id)
    
    def list_models(self) -> List[str]:
        """
        List all registered model IDs.
        
        Returns:
            List of model IDs
        """
        return list(self.models.keys())
    
    def remove_model(self, model_id: str):
        """
        Remove a model from the registry.
        
        Args:
            model_id: ID of the model to remove
        """
        if model_id in self.models:
            del self.models[model_id]
            self.logger.info(f"Model {model_id} removed from registry")


# Global model registry instance
model_registry = ModelRegistry()
