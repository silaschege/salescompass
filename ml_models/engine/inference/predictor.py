# Inference system for ML Models
# Handles prediction requests and model serving

from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import json
import os

from ..models.base_model import BaseModel, model_registry
from ..data.data_preparation import DataPreparationPipeline
from ..config.settings import config


class ModelPredictor:
    """
    Inference system for making predictions with trained ML models.
    Handles input validation, preprocessing, prediction, and output formatting.
    """
    
    def __init__(self, model_id: Optional[str] = None, model: Optional[BaseModel] = None):
        """
        Initialize the predictor with a specific model.
        
        Args:
            model_id: ID of the model to use for predictions
            model: Model instance to use for predictions (alternative to model_id)
        """
        self.logger = logging.getLogger(__name__)
        
        if model:
            self.model = model
            self.model_id = model.model_spec.model_id
        elif model_id:
            self.model = model_registry.get_model(model_id)
            if not self.model:
                raise ValueError(f"Model with ID '{model_id}' not found in registry")
            self.model_id = model_id
        else:
            raise ValueError("Either model_id or model instance must be provided")
        
        if not self.model.is_trained:
            raise ValueError(f"Model '{self.model_id}' is not trained and cannot be used for predictions")
        
        # Initialize data preparation pipeline
        self.data_pipeline = DataPreparationPipeline()
    
    def predict_single(self, 
                      input_data: Dict[str, Any], 
                      include_probability: bool = True,
                      include_explanation: bool = False) -> Dict[str, Any]:
        """
        Make a prediction for a single input record.
        
        Args:
            input_data: Dictionary with feature names as keys and values as input
            include_probability: Whether to include prediction probability
            include_explanation: Whether to include feature importance explanation
            
        Returns:
            Dictionary with prediction results
        """
        # Convert single record to DataFrame
        df = pd.DataFrame([input_data])
        
        # Make batch prediction
        results = self.predict_batch(df, include_probability, include_explanation)
        
        # Return first result
        return results[0] if results else {}
    
    def predict_batch(self, 
                     input_data: Union[pd.DataFrame, List[Dict[str, Any]]], 
                     include_probability: bool = True,
                     include_explanation: bool = False) -> List[Dict[str, Any]]:
        """
        Make predictions for a batch of input records.
        
        Args:
            input_data: DataFrame or list of dictionaries with input features
            include_probability: Whether to include prediction probability
            include_explanation: Whether to include feature importance explanation
            
        Returns:
            List of dictionaries with prediction results
        """
        # Convert to DataFrame if necessary
        if isinstance(input_data, list):
            df = pd.DataFrame(input_data)
        else:
            df = input_data.copy()
        
        # Validate input features
        if not self._validate_input_features(df):
            raise ValueError("Input features do not match model requirements")
        
        # Preprocess the data
        try:
            df_processed = self.data_pipeline.transform_new_data(df)
        except Exception as e:
            self.logger.error(f"Error preprocessing input data: {str(e)}")
            raise ValueError(f"Error preprocessing input data: {str(e)}")
        
        # Make predictions
        try:
            predictions = self.model.predict(df_processed)
        except Exception as e:
            self.logger.error(f"Error making predictions: {str(e)}")
            raise ValueError(f"Error making predictions: {str(e)}")
        
        results = []
        
        for i in range(len(df)):
            result = {
                'prediction': int(predictions[i]),
                'model_id': self.model_id,
                'prediction_timestamp': datetime.now().isoformat(),
                'input_index': i
            }
            
            # Include probability if requested
            if include_probability:
                try:
                    probas = self.model.predict_proba(df_processed.iloc[[i]])
                    # Get probability of positive class (index 1 for binary classification)
                    if probas.shape[1] > 1:
                        result['probability'] = float(probas[0][1])
                        result['all_probabilities'] = [float(p) for p in probas[0]]
                    else:
                        result['probability'] = float(probas[0][0])
                except Exception as e:
                    self.logger.warning(f"Could not compute probabilities: {str(e)}")
                    result['probability'] = None
            
            # Include explanation if requested
            if include_explanation:
                explanation = self._generate_explanation(df_processed.iloc[i])
                result['explanation'] = explanation
            
            results.append(result)
        
        self.logger.info(f"Made predictions for {len(results)} records using model {self.model_id}")
        
        return results
    
    def _validate_input_features(self, df: pd.DataFrame) -> bool:
        """
        Validate that input features match the model's expected features.
        
        Args:
            df: Input DataFrame to validate
            
        Returns:
            True if features are valid, False otherwise
        """
        expected_features = set(self.model.feature_names)
        actual_features = set(df.columns)
        
        # Check if all expected features are present
        missing_features = expected_features - actual_features
        if missing_features:
            self.logger.error(f"Missing features: {missing_features}")
            return False
        
        # Log extra features (not necessarily an error)
        extra_features = actual_features - expected_features
        if extra_features:
            self.logger.info(f"Extra features in input (will be ignored): {extra_features}")
        
        return True
    
    def _generate_explanation(self, input_row: pd.Series) -> Dict[str, Any]:
        """
        Generate an explanation for the prediction based on feature importance.
        
        Args:
            input_row: Single row of processed input data
            
        Returns:
            Dictionary with explanation
        """
        explanation = {
            'method': 'feature_importance',
            'feature_contributions': {}
        }
        
        # Get feature importances from the model
        feature_importance = self.model.get_feature_importance()
        
        if feature_importance:
            # Calculate contribution of each feature based on its value and importance
            for feature_name, importance in feature_importance.items():
                if feature_name in input_row:
                    # For simplicity, we'll just return the importance score
                    # In a more advanced implementation, we could calculate SHAP values or LIME explanations
                    explanation['feature_contributions'][feature_name] = {
                        'importance': importance,
                        'value': input_row[feature_name],
                        'direction': 'positive' if input_row[feature_name] > 0 else 'negative'
                    }
        
        return explanation
    
    def predict_with_confidence(self, 
                               input_data: Union[pd.DataFrame, List[Dict[str, Any]]],
                               threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Make predictions with confidence assessment.
        
        Args:
            input_data: Input data for prediction
            threshold: Threshold for classification
            
        Returns:
            List of predictions with confidence assessment
        """
        # First get regular predictions with probabilities
        predictions = self.predict_batch(input_data, include_probability=True, include_explanation=False)
        
        for pred in predictions:
            # Assess confidence based on probability distance from threshold
            if 'probability' in pred and pred['probability'] is not None:
                prob = pred['probability']
                # Confidence is the distance from the threshold (0.5 by default)
                confidence = 2 * abs(prob - threshold)
                pred['confidence'] = min(confidence, 1.0)  # Cap at 1.0
                
                # Determine if prediction is high-confidence
                pred['is_high_confidence'] = confidence > 0.7
            else:
                pred['confidence'] = None
                pred['is_high_confidence'] = False
        
        return predictions


class LeadScoringPredictor(ModelPredictor):
    """
    Specialized predictor for lead scoring with business-specific functionality.
    """
    
    def __init__(self, model_id: Optional[str] = None, model: Optional[BaseModel] = None):
        """
        Initialize the lead scoring predictor.
        
        Args:
            model_id: ID of the lead scoring model to use
            model: Lead scoring model instance to use
        """
        super().__init__(model_id, model)
        
        # Validate that this is indeed a lead scoring model
        if self.model.model_spec.model_type.value != 'lead_scoring':
            raise ValueError("LeadScoringPredictor requires a lead scoring model")
    
    def predict_lead_score(self, 
                          lead_data: Dict[str, Any],
                          scoring_method: str = 'probability') -> Dict[str, Any]:
        """
        Predict a lead score with business context.
        
        Args:
            lead_data: Dictionary with lead information
            scoring_method: Method to convert prediction to score ('probability', 'classification')
            
        Returns:
            Dictionary with lead scoring results
        """
        # Make prediction
        prediction_result = self.predict_single(lead_data, include_probability=True, include_explanation=True)
        
        # Convert to business-friendly lead score
        if scoring_method == 'probability':
            # Use probability as the score (0-100 scale)
            if 'probability' in prediction_result and prediction_result['probability'] is not None:
                lead_score = int(prediction_result['probability'] * 100)
            else:
                lead_score = 0
        elif scoring_method == 'classification':
            # Use classification result (convert to 0-100 scale)
            lead_score = int(prediction_result['prediction'] * 100)
        else:
            raise ValueError(f"Unknown scoring method: {scoring_method}")
        
        # Add business context
        result = {
            'lead_score': lead_score,
            'converted_probability': prediction_result.get('probability'),
            'prediction': prediction_result['prediction'],
            'model_id': prediction_result['model_id'],
            'prediction_timestamp': prediction_result['prediction_timestamp'],
            'lead_qualification': self._get_lead_qualification(lead_score),
            'next_action_suggestion': self._get_next_action_suggestion(lead_score),
            'explanation': prediction_result.get('explanation', {})
        }
        
        return result
    
    def _get_lead_qualification(self, lead_score: int) -> str:
        """
        Get lead qualification based on score.
        
        Args:
            lead_score: Lead score (0-100)
            
        Returns:
            Lead qualification string
        """
        if lead_score >= 70:
            return 'Hot Lead'
        elif lead_score >= 40:
            return 'Warm Lead'
        elif lead_score >= 20:
            return 'Cold Lead'
        else:
            return 'Unqualified'
    
    def _get_next_action_suggestion(self, lead_score: int) -> str:
        """
        Get next action suggestion based on lead score.
        
        Args:
            lead_score: Lead score (0-100)
            
        Returns:
            Suggested next action
        """
        if lead_score >= 70:
            return 'Immediate follow-up required'
        elif lead_score >= 40:
            return 'Schedule contact within 24 hours'
        elif lead_score >= 20:
            return 'Nurture with content'
        else:
            return 'Consider removing from active list'


def create_predictor(model_id: str) -> ModelPredictor:
    """
    Factory function to create a predictor based on model type.
    
    Args:
        model_id: ID of the model to create predictor for
        
    Returns:
        Appropriate predictor instance
    """
    model = model_registry.get_model(model_id)
    if not model:
        raise ValueError(f"Model with ID '{model_id}' not found in registry")
    
    # Choose predictor type based on model type
    if model.model_spec.model_type.value == 'lead_scoring':
        return LeadScoringPredictor(model_id=model_id, model=model)
    else:
        return ModelPredictor(model_id=model_id, model=model)
