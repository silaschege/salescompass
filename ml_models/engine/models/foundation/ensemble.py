# Ensemble model implementation for ML Models
# Combines multiple models for improved lead scoring

from typing import Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.ensemble import VotingClassifier
from sklearn.exceptions import NotFittedError

from ml_models.engine.models.foundation.base_model import BaseModel, ModelType
from ml_models.infrastructure.config.ontology_config import ModelSpecification


class EnsembleModel(BaseModel):
    """
    Ensemble model that combines multiple base models for improved predictions.
    Uses voting classifier to combine predictions from different algorithms.
    """
    
    def __init__(self, model_spec: ModelSpecification, base_models: List[BaseModel]):
        """
        Initialize the Ensemble model.
        
        Args:
            model_spec: Model specification from the ontology
            base_models: List of base models to include in the ensemble
        """
        if model_spec.algorithm.lower() != "ensemble":
            raise ValueError(f"EnsembleModel expects algorithm='Ensemble', got '{model_spec.algorithm}'")
        
        super().__init__(model_spec)
        
        # Store base models
        self.base_models = base_models
        
        # Create sklearn estimators list for voting classifier
        estimators = []
        for i, model in enumerate(self.base_models):
            if not model.is_trained:
                raise ValueError(f"Base model {i} must be trained before creating ensemble")
            # Get the sklearn model from the base model
            estimators.append((f"model_{i}_{model.model_spec.algorithm}", model.model))
        
        # Initialize the voting classifier
        voting_type = model_spec.hyperparameters.get('voting', 'soft')  # 'soft' or 'hard'
        self.model = VotingClassifier(estimators=estimators, voting=voting_type)
        
        # Store feature names from the first model (assuming all models have same features)
        if self.base_models:
            self.feature_names = self.base_models[0].feature_names
    
    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> Dict[str, Any]:
        """
        Train the ensemble model on the provided data.
        Note: Base models should already be trained.
        
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
        
        # Train the ensemble (this just sets up the voting mechanism)
        # Base models are already trained
        self.model.fit(X, y)
        
        # Mark as trained
        self.is_trained = True
        self.last_trained = pd.Timestamp.now()
        
        # Record training in history
        training_record = {
            'timestamp': self.last_trained,
            'n_samples': X.shape[0],
            'n_features': X.shape[1],
            'n_base_models': len(self.base_models),
            'voting_type': self.model.voting,
            'base_models': [model.model_spec.name for model in self.base_models]
        }
        self.training_history.append(training_record)
        
        # Return training results
        results = {
            'status': 'success',
            'n_samples': X.shape[0],
            'n_features': X.shape[1],
            'n_base_models': len(self.base_models),
            'model_type': 'Ensemble',
            'voting_type': self.model.voting
        }
        
        return results
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions on the provided data using ensemble voting.
        
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
    
    def get_base_model_predictions(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """
        Get predictions from each base model in the ensemble.
        
        Args:
            X: Features to predict on
            
        Returns:
            Dictionary mapping model names to their predictions
        """
        if not self.is_trained:
            raise NotFittedError("Model must be trained before making predictions")
        
        # Validate features
        if not self.validate_features(X):
            raise ValueError("Feature validation failed")
        
        predictions = {}
        for i, model in enumerate(self.base_models):
            predictions[f"model_{i}_{model.model_spec.algorithm}"] = model.predict(X)
        
        return predictions
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get average feature importance across all base models.
        
        Returns:
            Dictionary mapping feature names to average importance scores
        """
        if not self.is_trained or not self.base_models:
            return {}
        
        # Collect feature importances from all base models
        all_importances = []
        for model in self.base_models:
            importance = model.get_feature_importance()
            if importance:
                all_importances.append(importance)
        
        if not all_importances:
            return {}
        
        # Calculate average importance for each feature
        avg_importance = {}
        for feature in self.feature_names:
            feature_importances = [imp.get(feature, 0) for imp in all_importances]
            avg_importance[feature] = np.mean(feature_importances)
        
        return avg_importance


class LeadScoringEnsembleModel(EnsembleModel):
    """
    Specialized Ensemble model for lead scoring with domain-specific features.
    """
    
    def __init__(self, model_spec: ModelSpecification, base_models: List[BaseModel]):
        """
        Initialize the Lead Scoring Ensemble model.
        
        Args:
            model_spec: Model specification from the ontology
            base_models: List of base models to include in the ensemble
        """
        # Ensure the model spec is for lead scoring
        if model_spec.model_type != ModelType.LEAD_SCORING:
            raise ValueError(f"LeadScoringEnsembleModel expects model_type=ModelType.LEAD_SCORING, got '{model_spec.model_type}'")
        
        super().__init__(model_spec, base_models)
        
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
        base_info['base_models_info'] = [model.get_model_info() for model in self.base_models]
        
        return base_info
    
    def get_disagreement_score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Calculate disagreement score between base models.
        Higher disagreement may indicate less confident predictions.
        
        Args:
            X: Features to predict on
            
        Returns:
            Array of disagreement scores (0-1 scale, higher means more disagreement)
        """
        if not self.is_trained:
            raise NotFittedError("Model must be trained before making predictions")
        
        # Get predictions from each base model
        base_predictions = self.get_base_model_predictions(X)
        
        # Calculate disagreement as variance across model predictions
        prediction_matrix = np.array(list(base_predictions.values()))  # Shape: (n_models, n_samples)
        disagreement = np.var(prediction_matrix, axis=0)  # Variance across models for each sample
        
        # Normalize disagreement to 0-1 scale
        max_possible_disagreement = 0.25  # Max variance for binary predictions is 0.25
        normalized_disagreement = disagreement / max_possible_disagreement
        
        return normalized_disagreement


def create_lead_scoring_ensemble(base_models: List[BaseModel]) -> LeadScoringEnsembleModel:
    """
    Convenience function to create a lead scoring ensemble model.
    
    Args:
        base_models: List of trained base models to include in ensemble
        
    Returns:
        LeadScoringEnsembleModel instance
    """
    from ..config.ontology_config import LEAD_SCORING_MODEL
    
    # Create a model spec for the ensemble based on the lead scoring model spec
    ensemble_spec = ModelSpecification(
        model_id="lead_scoring_ensemble_v1",
        model_type=LEAD_SCORING_MODEL.model_type,
        name="Lead Scoring Ensemble Model",
        description="Ensemble model combining multiple algorithms for lead scoring",
        version="1.0.0",
        features=LEAD_SCORING_MODEL.features,
        target_variable=LEAD_SCORING_MODEL.target_variable,
        algorithm="Ensemble",
        hyperparameters={
            'voting': 'soft',  # Use probability voting
            'weights': None  # Equal weights for all models
        },
        performance_metrics=LEAD_SCORING_MODEL.performance_metrics,
        dependencies=LEAD_SCORING_MODEL.dependencies + ["xgboost"]  # Add any additional dependencies
    )
    
    return LeadScoringEnsembleModel(ensemble_spec, base_models)
