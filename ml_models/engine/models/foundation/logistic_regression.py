# Logistic Regression model implementation for ML Models
from typing import Dict, Any
import pandas as pd
import numpy as np
from sklearn.exceptions import NotFittedError
from sklearn.linear_model import LogisticRegression

from ml_models.engine.models.foundation.base_model import BaseModel, ModelType
from ml_models.infrastructure.config.ontology_config import ModelSpecification


class LogisticRegressionModel(BaseModel):
    """
    Logistic Regression model implementation.
    Standard classification algorithm for baseline models.
    """
    
    def __init__(self, model_spec: ModelSpecification):
        """
        Initialize the Logistic Regression model.
        
        Args:
            model_spec: Model specification from the ontology
        """
        super().__init__(model_spec)
        
        # Initialize the Logistic Regression classifier with hyperparameters from spec
        hyperparams = model_spec.hyperparameters
        self.model = LogisticRegression(
            C=hyperparams.get('C', 1.0),
            penalty=hyperparams.get('penalty', 'l2'),
            solver=hyperparams.get('solver', 'lbfgs'),
            max_iter=hyperparams.get('max_iter', 100),
            random_state=hyperparams.get('random_state', 42),
            n_jobs=hyperparams.get('n_jobs', -1),
            class_weight=hyperparams.get('class_weight', None)
        )
    
    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> Dict[str, Any]:
        """
        Train the Logistic Regression model.
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
        
        # Coefficients as feature importance
        if hasattr(self.model, 'coef_'):
            coefs = self.model.coef_[0]
            feature_importance = {name: float(val) for name, val in zip(self.feature_names, coefs)}
            self.update_performance_metrics({'feature_importance': feature_importance})
        
        return {
            'status': 'success',
            'n_samples': X.shape[0],
            'n_features': X.shape[1],
            'model_type': 'LogisticRegression'
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
        if not self.is_trained or not hasattr(self.model, 'coef_'):
            return {}
        coefs = self.model.coef_[0]
        return {name: float(val) for name, val in zip(self.feature_names, coefs)}
