# Neural Network model implementation (MLP) for ML Models
from typing import Dict, Any
import pandas as pd
import numpy as np
from sklearn.exceptions import NotFittedError
from sklearn.neural_network import MLPClassifier

from ml_models.engine.models.foundation.base_model import BaseModel, ModelType
from ml_models.infrastructure.config.ontology_config import ModelSpecification


class MultiLayerPerceptronModel(BaseModel):
    """
    MLP Neural Network model implementation.
    Good for complex nonlinear patterns.
    """
    
    def __init__(self, model_spec: ModelSpecification):
        """
        Initialize the MLP model.
        """
        super().__init__(model_spec)
        
        # Initialize the MLP classifier with hyperparameters from spec
        hyperparams = model_spec.hyperparameters
        self.model = MLPClassifier(
            hidden_layer_sizes=hyperparams.get('hidden_layer_sizes', (100,)),
            activation=hyperparams.get('activation', 'relu'),
            solver=hyperparams.get('solver', 'adam'),
            alpha=hyperparams.get('alpha', 0.0001),
            batch_size=hyperparams.get('batch_size', 'auto'),
            learning_rate=hyperparams.get('learning_rate', 'constant'),
            learning_rate_init=hyperparams.get('learning_rate_init', 0.001),
            max_iter=hyperparams.get('max_iter', 200),
            random_state=hyperparams.get('random_state', 42),
            early_stopping=hyperparams.get('early_stopping', False),
            validation_fraction=hyperparams.get('validation_fraction', 0.1)
        )
    
    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> Dict[str, Any]:
        """
        Train the MLP model.
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
            'hyperparameters': self.model.get_params(),
            'n_layers': self.model.n_layers_,
            'n_iter': self.model.n_iter_,
            'loss': self.model.loss_
        }
        self.training_history.append(training_record)
        
        return {
            'status': 'success',
            'n_samples': X.shape[0],
            'n_features': X.shape[1],
            'model_type': 'MLP',
            'loss': self.model.loss_
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
        # MLP doesn't have direct feature importance like tree-based models
        # One would need permutation importance or SHAP
        return {}
