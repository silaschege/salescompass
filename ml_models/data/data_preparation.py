# Data preparation module for ML Models
# Handles data cleaning, preprocessing, and feature engineering

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
import logging

from .data_adapter import salescompass_adapter
from ..config.ontology_config import FeatureDefinition, DataType, ontology


class DataPreparationPipeline:
    """
    Data preparation pipeline for ML models.
    Handles cleaning, preprocessing, and feature engineering based on ontology specifications.
    """
    
    def __init__(self):
        self.scalers: Dict[str, StandardScaler] = {}
        self.encoders: Dict[str, Any] = {}
        self.feature_definitions: Dict[str, FeatureDefinition] = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize feature definitions from ontology
        self._init_feature_definitions()
    
    def _init_feature_definitions(self):
        """Initialize feature definitions from the ontology."""
        # Get the lead scoring model specification
        lead_scoring_model = None
        for model in ontology.models:
            if model.model_type.value == 'lead_scoring':
                lead_scoring_model = model
                break
        
        if lead_scoring_model:
            for feature in lead_scoring_model.features:
                self.feature_definitions[feature.name] = feature
    
    def prepare_features(self, df: pd.DataFrame, 
                        target_column: str = 'is_converted',
                        test_size: float = 0.2,
                        random_state: int = 42) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
        """
        Prepare features for model training.
        
        Args:
            df: Input dataframe with raw features
            target_column: Name of the target variable column
            test_size: Proportion of data to use for testing
            random_state: Random state for reproducibility
            
        Returns:
            X_train, y_train, X_test, y_test
        """
        # Make a copy to avoid modifying the original dataframe
        df_copy = df.copy()
        
        # Separate features and target
        if target_column not in df_copy.columns:
            raise ValueError(f"Target column '{target_column}' not found in dataframe")
        
        y = df_copy[target_column]
        X = df_copy.drop(columns=[target_column])
        
        # Clean and preprocess the data
        X = self._clean_data(X)
        X = self._encode_categorical_features(X)
        X = self._scale_numerical_features(X)
        
        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        return X_train, y_train, X_test, y_test
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean the data by handling missing values, outliers, etc.
        
        Args:
            df: Input dataframe
            
        Returns:
            Cleaned dataframe
        """
        df_clean = df.copy()
        
        for column in df_clean.columns:
            if column in self.feature_definitions:
                feature_def = self.feature_definitions[column]
                
                # Handle missing values based on feature type
                if feature_def.data_type == DataType.NUMERICAL:
                    # For numerical features, fill with median
                    df_clean[column] = df_clean[column].fillna(df_clean[column].median())
                    
                    # Handle outliers if min/max values are defined
                    if feature_def.min_value is not None:
                        df_clean[column] = df_clean[column].clip(lower=feature_def.min_value)
                    if feature_def.max_value is not None:
                        df_clean[column] = df_clean[column].clip(upper=feature_def.max_value)
                        
                elif feature_def.data_type in [DataType.CATEGORICAL, DataType.BOOLEAN]:
                    # For categorical features, fill with mode or 'unknown'
                    if df_clean[column].isnull().any():
                        mode_value = df_clean[column].mode()
                        fill_value = mode_value[0] if not mode_value.empty else 'unknown'
                        df_clean[column] = df_clean[column].fillna(fill_value)
        
        return df_clean
    
    def _encode_categorical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Encode categorical features using appropriate encoding methods.
        
        Args:
            df: Input dataframe
            
        Returns:
            Dataframe with encoded categorical features
        """
        df_encoded = df.copy()
        
        for column in df_encoded.columns:
            if column in self.feature_definitions:
                feature_def = self.feature_definitions[column]
                
                if feature_def.data_type in [DataType.CATEGORICAL, DataType.BOOLEAN]:
                    # For categorical features with limited unique values, use label encoding
                    if feature_def.allowed_values or df_encoded[column].nunique() <= 10:
                        if column not in self.encoders:
                            # Initialize and fit the encoder
                            le = LabelEncoder()
                            # Handle unseen labels by adding them to the training data
                            unique_values = df_encoded[column].unique()
                            # Fit on unique values to handle any unseen categories later
                            le.fit(unique_values)
                            self.encoders[column] = le
                        else:
                            # Handle unseen labels by adding them to the existing encoder
                            le = self.encoders[column]
                            current_classes = set(le.classes_)
                            new_classes = set(df_encoded[column].unique())
                            if not new_classes.issubset(current_classes):
                                # Rebuild encoder with all classes
                                all_classes = list(current_classes.union(new_classes))
                                le = LabelEncoder()
                                le.fit(all_classes)
                                self.encoders[column] = le
                        
                        # Transform the data
                        try:
                            df_encoded[column] = self.encoders[column].transform(df_encoded[column])
                        except ValueError as e:
                            # Handle unseen labels by transforming them to a default value
                            self.logger.warning(f"Unseen labels in column {column}, using default encoding: {e}")
                            # Map unseen labels to a default value (e.g., -1)
                            df_encoded[column] = df_encoded[column].apply(
                                lambda x: self.encoders[column].transform([x])[0] 
                                if x in self.encoders[column].classes_ else -1
                            )
        
        return df_encoded
    
    def _scale_numerical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Scale numerical features using StandardScaler.
        
        Args:
            df: Input dataframe
            
        Returns:
            Dataframe with scaled numerical features
        """
        df_scaled = df.copy()
        
        for column in df_scaled.columns:
            if column in self.feature_definitions:
                feature_def = self.feature_definitions[column]
                
                if feature_def.data_type == DataType.NUMERICAL:
                    if column not in self.scalers:
                        # Initialize and fit the scaler
                        scaler = StandardScaler()
                        df_scaled[column] = scaler.fit_transform(df_scaled[[column]]).flatten()
                        self.scalers[column] = scaler
                    else:
                        # Transform using existing scaler
                        df_scaled[column] = self.scalers[column].transform(df_scaled[[column]]).flatten()
        
        return df_scaled
    
    def transform_new_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform new data using the same preprocessing steps as training data.
        
        Args:
            df: New dataframe to transform
            
        Returns:
            Transformed dataframe
        """
        df_transformed = df.copy()
        
        # Clean the data
        df_transformed = self._clean_data(df_transformed)
        
        # Encode categorical features
        df_transformed = self._encode_categorical_features(df_transformed)
        
        # Scale numerical features
        df_transformed = self._scale_numerical_features(df_transformed)
        
        return df_transformed


class FeatureEngineering:
    """
    Advanced feature engineering for lead scoring.
    Creates new features from existing data to improve model performance.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create derived features from the existing dataframe.
        
        Args:
            df: Input dataframe
            
        Returns:
            Dataframe with additional derived features
        """
        df_enhanced = df.copy()
        
        # Create interaction features if the base features exist
        if 'company_size' in df_enhanced.columns and 'lead_score' in df_enhanced.columns:
            df_enhanced['company_size_score_interaction'] = (
                df_enhanced['company_size'] * df_enhanced['lead_score'] / 100
            )
        
        if 'annual_revenue' in df_enhanced.columns and 'lead_score' in df_enhanced.columns:
            df_enhanced['revenue_score_interaction'] = (
                df_enhanced['annual_revenue'] * df_enhanced['lead_score'] / 100
            )
        
        # Create categorical feature combinations if they exist
        if 'industry' in df_enhanced.columns and 'lead_source' in df_enhanced.columns:
            df_enhanced['industry_source_combo'] = (
                df_enhanced['industry'].astype(str) + '_' + df_enhanced['lead_source'].astype(str)
            )
        
        # Create binned features for numerical variables
        if 'lead_score' in df_enhanced.columns:
            df_enhanced['lead_score_binned'] = pd.cut(
                df_enhanced['lead_score'], 
                bins=[0, 25, 50, 75, 100], 
                labels=['very_low', 'low', 'medium', 'high']
            ).astype(str)
        
        if 'company_size' in df_enhanced.columns:
            df_enhanced['company_size_binned'] = pd.cut(
                df_enhanced['company_size'], 
                bins=[0, 10, 50, 250, float('inf')], 
                labels=['small', 'small_medium', 'medium_large', 'large']
            ).astype(str)
        
        # Create engagement score if engagement features exist
        engagement_features = [
            'email_opened', 'link_clicked', 'website_visited', 
            'demo_requested', 'proposal_downloaded'
        ]
        existing_engagement = [f for f in engagement_features if f in df_enhanced.columns]
        if existing_engagement:
            df_enhanced['engagement_score'] = df_enhanced[existing_engagement].sum(axis=1)
        
        # Create recency features if days since creation exists
        if 'days_since_creation' in df_enhanced.columns:
            df_enhanced['is_recent_lead'] = (df_enhanced['days_since_creation'] <= 30).astype(int)
            df_enhanced['lead_age_category'] = pd.cut(
                df_enhanced['days_since_creation'],
                bins=[0, 7, 30, 90, float('inf')],
                labels=['new', 'week_old', 'month_old', 'old']
            ).astype(str)
        
        # Create profile completeness categories
        if 'profile_completeness_score' in df_enhanced.columns:
            df_enhanced['profile_completeness_category'] = pd.cut(
                df_enhanced['profile_completeness_score'],
                bins=[0, 25, 50, 75, 100],
                labels=['incomplete', 'basic', 'good', 'complete']
            ).astype(str)
        
        return df_enhanced
    
    def select_important_features(self, df: pd.DataFrame, 
                                target_column: str = 'is_converted',
                                n_features: int = 15) -> pd.DataFrame:
        """
        Select the most important features using statistical methods.
        
        Args:
            df: Input dataframe
            target_column: Name of the target variable
            n_features: Number of top features to select
            
        Returns:
            Dataframe with only the selected features
        """
        from sklearn.feature_selection import SelectKBest, f_classif
        
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found in dataframe")
        
        # Separate features and target
        y = df[target_column]
        X = df.drop(columns=[target_column])
        
        # Select top features
        selector = SelectKBest(score_func=f_classif, k=min(n_features, X.shape[1]))
        X_selected = selector.fit_transform(X, y)
        
        # Get selected feature names
        selected_features = X.columns[selector.get_support()].tolist()
        selected_features.append(target_column)  # Add target back
        
        return df[selected_features]


# Example usage
def prepare_lead_scoring_data(tenant_id: Optional[str] = None,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            limit: Optional[int] = None) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """
    Convenience function to prepare lead scoring data end-to-end.
    
    Args:
        tenant_id: Specific tenant to extract data for
        start_date: Start date for data extraction
        end_date: End date for data extraction
        limit: Maximum number of records to extract
        
    Returns:
        X_train, y_train, X_test, y_test
    """
    from datetime import datetime
    
    # Extract data using the adapter
    df = salescompass_adapter.extract_lead_data(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    # Validate the data
    validation_results = salescompass_adapter.validate_data(df)
    if not validation_results['valid']:
        raise ValueError(f"Data validation failed: {validation_results['missing_features']}")
    
    # Create derived features
    feature_engineer = FeatureEngineering()
    df = feature_engineer.create_derived_features(df)
    
    # Select important features
    df = feature_engineer.select_important_features(df)
    
    # Prepare features for training
    pipeline = DataPreparationPipeline()
    return pipeline.prepare_features(df)
