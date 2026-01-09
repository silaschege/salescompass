# SVM model implementation for ML Models
from typing import Dict, Any
import pandas as pd
import numpy as np
from sklearn.exceptions import NotFittedError
from sklearn.svm import SVC

from ml_models.engine.models.foundation.base_model import BaseModel, ModelType
from ml_models.infrastructure.config.ontology_config import ModelSpecification


class SupportVectorMachineModel(BaseModel):
    """
    SVM model implementation.
    Effective high-dimensional mapping algorithm.
    """
    
    def __init__(self, model_spec: ModelSpecification):
        """
        Initialize the SVM model.
        """
        super().__init__(model_spec)
        
        # Initialize the SVM classifier with hyperparameters from spec
        hyperparams = model_spec.hyperparameters
        self.model = SVC(
            C=hyperparams.get('C', 1.0),
            kernel=hyperparams.get('kernel', 'rbf'),
            degree=hyperparams.get('degree', 3),
            gamma=hyperparams.get('gamma', 'scale'),
            probability=True,  # Mandatory for predict_proba
            random_state=hyperparams.get('random_state', 42),
            class_weight=hyperparams.get('class_weight', None)
        )
    
    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> Dict[str, Any]:
        """
        Train the SVM model.
        """
        if not self.validate_features(X):
            raise ValueError("Feature validation failed")
        
        self.feature_names = list(X.columns)
        self.model.fit(X, y)
        self.is_trained = True
        self.last_trained = pd.Timestamp.now()
        
        training_record = {
            'timestamp': self.last_trained,
            'n_samples': X.shape[0],
            'n_features': X.shape[1],
            'hyperparameters': self.model.get_params()
        }
        self.training_history.append(training_record)
        
        return {
            'status': 'success',
            'n_samples': X.shape[0],
            'n_features': X.shape[1],
            'model_type': 'SVM'
        }
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained:
            raise NotFittedError("Model must be trained before making predictions")
        if not self.validate_features(X):
            raise ValueError("Feature validation failed")
        return self.model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained:
            raise NotFittedError("Model must be trained before making predictions")
        if not self.validate_features(X):
            raise ValueError("Feature validation failed")
        return self.model.predict_proba(X)
    
    def get_feature_importance(self) -> Dict[str, float]:
        # SVM with RBF kernel doesn't have direct feature importance
        # If linear kernel is used, we could use coef_
        if self.model.kernel == 'linear' and hasattr(self.model, 'coef_'):
            coefs = self.model.coef_[0]
            if isinstance(coefs, (list, np.ndarray)):
                 return {name: float(val) for name, val in zip(self.feature_names, coefs)}
        return {}
