 # Deal Scoring Model for Opportunities
# Implements ML model to score deals based on various opportunity attributes

from typing import Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

from .base_opportunity import BaseOpportunityModel


class DealScoringModel(BaseOpportunityModel):
    """
    Model for scoring deals based on opportunity characteristics.
    Predicts a numerical score representing the quality/value of an opportunity.
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        Initialize the deal scoring model
        
        Args:
            model_config: Configuration containing model parameters
        """
        super().__init__(model_config)
        
        # Initialize model with config parameters or defaults
        self.model = RandomForestRegressor(
            n_estimators=model_config.get('n_estimators', 100),
            max_depth=model_config.get('max_depth', 10),
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
        Preprocess opportunity data for deal scoring
        
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
        Train the deal scoring model
        
        Args:
            X: Feature DataFrame
            y: Target Series (deal scores)
            
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
        mse = mean_squared_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)
        
        # Feature importance
        feature_importance = dict(zip(X_processed.columns, self.model.feature_importances_))
        
        return {
            'mse': mse,
            'r2_score': r2,
            'feature_importance': feature_importance,
            'samples_used': len(X_train)
        }
    
    def score_deal(self, opportunity_data: pd.DataFrame) -> np.ndarray:
        """
        Score a deal based on opportunity characteristics
        
        Args:
            opportunity_data: DataFrame with opportunity features
            
        Returns:
            Array of deal scores
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before scoring deals")
        
        X_processed = self.preprocess_data(opportunity_data)
        return self.model.predict(X_processed)