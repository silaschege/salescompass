# Win Probability Model for Opportunities
# Implements ML model to predict the probability of winning an opportunity

from typing import Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score

from .base_opportunity import BaseOpportunityModel


class WinProbabilityModel(BaseOpportunityModel):
    """
    Model for predicting the probability of winning an opportunity.
    Predicts the likelihood that an opportunity will be won.
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        Initialize the win probability model
        
        Args:
            model_config: Configuration containing model parameters
        """
        super().__init__(model_config)
        
        # Initialize model with config parameters or defaults
        self.model = GradientBoostingClassifier(
            n_estimators=model_config.get('n_estimators', 100),
            max_depth=model_config.get('max_depth', 3),
            learning_rate=model_config.get('learning_rate', 0.1),
            min_samples_split=model_config.get('min_samples_split', 2),
            min_samples_leaf=model_config.get('min_samples_leaf', 1),
            random_state=model_config.get('random_state', 42)
        )
        
        self.scaler = StandardScaler()
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.categorical_features: List[str] = model_config.get('categorical_features', [])
        self.numerical_features: List[str] = model_config.get('numerical_features', [])
        
    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess opportunity data for win probability prediction
        
        Args:
            data: DataFrame with opportunity features
            
        Returns:
            Processed DataFrame ready for model
        """
        processed_data = data.copy()
        
        # Handle categorical features
        for feature in self.categorical_features:
            if feature in processed_data.columns:
                if feature not in self.label_encoders:
                    self.label_encoders[feature] = LabelEncoder()
                    processed_data[feature] = self.label_encoders[feature].fit_transform(
                        processed_data[feature].astype(str)
                    )
                else:
                    # Transform using existing encoder, handling unseen labels
                    le = self.label_encoders[feature]
                    processed_data[feature] = processed_data[feature].astype(str)
                    # Map unseen labels to a default value (using the last known label)
                    processed_data[feature] = processed_data[feature].apply(
                        lambda x: x if x in le.classes_ else le.classes_[0]
                    )
                    processed_data[feature] = le.transform(processed_data[feature])
        
        # Handle numerical features
        numerical_data = processed_data[self.numerical_features]
        scaled_numerical = self.scaler.fit_transform(numerical_data)
        processed_data[self.numerical_features] = scaled_numerical
        
        return processed_data
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Train the win probability model
        
        Args:
            X: Feature DataFrame
            y: Target Series (win/loss labels)
            
        Returns:
            Dictionary with training results and metrics
        """
        # Preprocess the data
        X_processed = self.preprocess_data(X)
        
        # Split data for validation
        X_train, X_val, y_train, y_val = train_test_split(
            X_processed, y, 
            test_size=self.model_config.get('validation_split', 0.2),
            random_state=self.model_config.get('random_state', 42)
        )
        
        # Train the model
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Validate and calculate metrics
        y_pred = self.model.predict(X_val)
        y_pred_proba = self.model.predict_proba(X_val)[:, 1]  # Probability of positive class
        
        accuracy = accuracy_score(y_val, y_pred)
        precision = precision_score(y_val, y_pred, average='weighted')
        recall = recall_score(y_val, y_pred, average='weighted')
        auc_roc = roc_auc_score(y_val, y_pred_proba)
        
        # Feature importance
        feature_importance = dict(zip(X_processed.columns, self.model.feature_importances_))
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'auc_roc': auc_roc,
            'feature_importance': feature_importance,
            'samples_used': len(X_train)
        }
    
    def predict_win_probability(self, opportunity_data: pd.DataFrame) -> np.ndarray:
        """
        Predict the win probability for opportunities
        
        Args:
            opportunity_data: DataFrame with opportunity features
            
        Returns:
            Array of win probabilities
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before predicting win probability")
        
        X_processed = self.preprocess_data(opportunity_data)
        return self.model.predict_proba(X_processed)[:, 1]  # Return probability of winning