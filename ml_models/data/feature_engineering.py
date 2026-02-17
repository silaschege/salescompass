# Feature engineering module for ML Models
# Advanced feature creation and transformation techniques

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from sklearn.preprocessing import PolynomialFeatures
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import logging

from .data_adapter import salescompass_adapter
from .data_preparation import FeatureEngineering


class AdvancedFeatureEngineering:
    """
    Advanced feature engineering techniques for lead scoring.
    Includes polynomial features, clustering-based features, and domain-specific transformations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.feature_names = []
        self.poly_features = None
        self.pca = None
        self.kmeans = None
    
    def create_polynomial_features(self, df: pd.DataFrame, 
                                 degree: int = 2, 
                                 interaction_only: bool = False) -> pd.DataFrame:
        """
        Create polynomial and interaction features from numerical features.
        
        Args:
            df: Input dataframe
            degree: Degree of polynomial features
            interaction_only: If True, only interaction features are produced
            
        Returns:
            Dataframe with polynomial features added
        """
        # Identify numerical columns
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numerical_cols:
            self.logger.warning("No numerical columns found for polynomial feature creation")
            return df
        
        # Create polynomial features
        poly = PolynomialFeatures(degree=degree, interaction_only=interaction_only, include_bias=False)
        poly_features = poly.fit_transform(df[numerical_cols])
        
        # Get feature names
        feature_names = poly.get_feature_names_out(numerical_cols)
        
        # Create a dataframe with polynomial features
        poly_df = pd.DataFrame(poly_features, columns=feature_names, index=df.index)
        
        # Remove original numerical columns and add polynomial features
        result_df = df.drop(columns=numerical_cols)
        result_df = pd.concat([result_df, poly_df], axis=1)
        
        self.poly_features = poly
        
        return result_df
    
    def create_cluster_features(self, df: pd.DataFrame, 
                              n_clusters: int = 5,
                              feature_cols: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Create cluster-based features using KMeans clustering.
        
        Args:
            df: Input dataframe
            n_clusters: Number of clusters to create
            feature_cols: Columns to use for clustering (if None, uses all numerical)
            
        Returns:
            Dataframe with cluster features added
        """
        # Identify numerical columns for clustering
        if feature_cols is None:
            feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        else:
            # Ensure specified columns are numerical
            feature_cols = [col for col in feature_cols if col in df.select_dtypes(include=[np.number]).columns]
        
        if not feature_cols:
            self.logger.warning("No numerical columns found for clustering")
            return df
        
        # Fit KMeans
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(df[feature_cols])
        
        # Add cluster labels as a new feature
        result_df = df.copy()
        result_df['cluster_label'] = cluster_labels
        
        # Add distance to cluster centers as features
        distances = kmeans.transform(df[feature_cols])
        for i in range(n_clusters):
            result_df[f'distance_to_cluster_{i}'] = distances[:, i]
        
        self.kmeans = kmeans
        
        return result_df
    
    def create_pca_features(self, df: pd.DataFrame, 
                          n_components: Optional[int] = None,
                          variance_threshold: float = 0.95) -> pd.DataFrame:
        """
        Create PCA features from numerical features.
        
        Args:
            df: Input dataframe
            n_components: Number of components (if None, uses variance threshold)
            variance_threshold: Variance threshold for automatic component selection
            
        Returns:
            Dataframe with PCA features added
        """
        # Identify numerical columns
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numerical_cols:
            self.logger.warning("No numerical columns found for PCA")
            return df
        
        # Determine number of components
        if n_components is None:
            # Use variance threshold to determine components
            pca_full = PCA()
            pca_full.fit(df[numerical_cols])
            cumsum_var = np.cumsum(pca_full.explained_variance_ratio_)
            n_components = np.argmax(cumsum_var >= variance_threshold) + 1
        
        # Fit PCA
        pca = PCA(n_components=n_components)
        pca_features = pca.fit_transform(df[numerical_cols])
        
        # Create feature names
        pca_feature_names = [f'pca_component_{i}' for i in range(n_components)]
        
        # Create a dataframe with PCA features
        pca_df = pd.DataFrame(pca_features, columns=pca_feature_names, index=df.index)
        
        # Add PCA features to original dataframe
        result_df = pd.concat([df, pca_df], axis=1)
        
        self.pca = pca
        
        return result_df
    
    def create_domain_specific_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create domain-specific features for lead scoring based on business knowledge.
        
        Args:
            df: Input dataframe
            
        Returns:
            Dataframe with domain-specific features added
        """
        result_df = df.copy()
        
        # Create lead quality score based on multiple factors
        if all(col in df.columns for col in ['lead_score', 'profile_completeness_score']):
            result_df['lead_quality_score'] = (
                0.6 * df['lead_score'] + 
                0.4 * df['profile_completeness_score']
            )
        
        # Create business potential score
        if all(col in df.columns for col in ['company_size', 'annual_revenue']):
            # Normalize company size and revenue (0-100 scale)
            max_company_size = df['company_size'].max()
            max_revenue = df['annual_revenue'].max()
            
            if max_company_size > 0:
                normalized_company_size = (df['company_size'] / max_company_size) * 100
            else:
                normalized_company_size = 0
                
            if max_revenue > 0:
                normalized_revenue = (df['annual_revenue'] / max_revenue) * 100
            else:
                normalized_revenue = 0
            
            result_df['business_potential_score'] = (
                0.4 * normalized_company_size + 
                0.6 * normalized_revenue
            )
        
        # Create engagement velocity (how quickly engagement happened)
        if all(col in df.columns for col in ['days_since_creation', 'engagement_score']):
            # Engagement per day since creation
            result_df['engagement_velocity'] = np.where(
                df['days_since_creation'] > 0,
                df['engagement_score'] / df['days_since_creation'],
                0
            )
        
        # Create lead source effectiveness (relative to industry)
        if 'lead_source' in df.columns and 'industry' in df.columns:
            # This would typically use historical conversion data by source and industry
            # For now, create a simple combination feature
            result_df['source_industry_combo'] = df['lead_source'].astype(str) + '_' + df['industry'].astype(str)
        
        # Create urgency indicators
        if 'days_since_creation' in df.columns:
            # Leads that engage quickly might be more urgent
            result_df['early_engager'] = (
                (df['days_since_creation'] <= 7) & 
                (df.get('engagement_score', 0) > 0)
            ).astype(int)
        
        # Create consistency features
        if all(col in df.columns for col in ['lead_score', 'engagement_score']):
            # Consistency between lead score and engagement
            result_df['score_engagement_alignment'] = np.abs(
                df['lead_score'] - df['engagement_score']
            )
        
        return result_df
    
    def create_time_based_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create time-based features if date-related columns exist.
        
        Args:
            df: Input dataframe
            
        Returns:
            Dataframe with time-based features added
        """
        result_df = df.copy()
        
        # Look for date-related columns
        date_cols = [col for col in df.columns if 'date' in col.lower() or 'created' in col.lower()]
        
        for col in date_cols:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                # Extract date components
                result_df[f'{col}_year'] = df[col].dt.year
                result_df[f'{col}_month'] = df[col].dt.month
                result_df[f'{col}_day'] = df[col].dt.day
                result_df[f'{col}_dayofweek'] = df[col].dt.dayofweek
                result_df[f'{col}_quarter'] = df[col].dt.quarter
        
        return result_df


class FeatureSelector:
    """
    Feature selection techniques for identifying the most important features.
    """
    
    def __init__(self):
        self.selected_features = None
        self.logger = logging.getLogger(__name__)
    
    def univariate_selection(self, X: pd.DataFrame, y: pd.Series, 
                           k: int = 10, score_func: str = 'f_classif') -> pd.DataFrame:
        """
        Select features using univariate statistical tests.
        
        Args:
            X: Feature dataframe
            y: Target series
            k: Number of top features to select
            score_func: Scoring function ('f_classif' or 'mutual_info_classif')
            
        Returns:
            Dataframe with selected features
        """
        # Determine scoring function
        if score_func == 'f_classif':
            selector = SelectKBest(score_func=f_classif, k=min(k, X.shape[1]))
        elif score_func == 'mutual_info_classif':
            selector = SelectKBest(score_func=mutual_info_classif, k=min(k, X.shape[1]))
        else:
            raise ValueError(f"Unknown score function: {score_func}")
        
        # Fit selector
        X_selected = selector.fit_transform(X, y)
        
        # Get selected feature names
        selected_features = X.columns[selector.get_support()].tolist()
        self.selected_features = selected_features
        
        return X[selected_selected_features]
    
    def correlation_filter(self, X: pd.DataFrame, 
                          threshold: float = 0.95) -> pd.DataFrame:
        """
        Remove highly correlated features.
        
        Args:
            X: Feature dataframe
            threshold: Correlation threshold for removal
            
        Returns:
            Dataframe with highly correlated features removed
        """
        # Calculate correlation matrix
        corr_matrix = X.corr().abs()
        
        # Find features with correlation greater than threshold
        upper_triangle = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )
        
        # Find features to drop
        features_to_drop = [
            column for column in upper_triangle.columns
            if any(upper_triangle[column] > threshold)
        ]
        
        self.logger.info(f"Dropping {len(features_to_drop)} highly correlated features: {features_to_drop}")
        
        # Return dataframe without highly correlated features
        return X.drop(columns=features_to_drop)
    
    def variance_threshold(self, X: pd.DataFrame, 
                          threshold: float = 0.01) -> pd.DataFrame:
        """
        Remove low-variance features.
        
        Args:
            X: Feature dataframe
            threshold: Minimum variance threshold
            
        Returns:
            Dataframe with low-variance features removed
        """
        from sklearn.feature_selection import VarianceThreshold
        
        selector = VarianceThreshold(threshold=threshold)
        X_selected = selector.fit_transform(X)
        
        # Get selected feature names
        selected_features = X.columns[selector.get_support()].tolist()
        
        return X[selected_features]


def create_comprehensive_feature_set(df: pd.DataFrame, 
                                   target_column: str = 'is_converted') -> pd.DataFrame:
    """
    Create a comprehensive feature set using all available feature engineering techniques.
    
    Args:
        df: Input dataframe
        target_column: Name of the target variable
        
    Returns:
        Dataframe with comprehensive feature set
    """
    # Separate features and target
    if target_column in df.columns:
        y = df[target_column]
        X = df.drop(columns=[target_column])
    else:
        X = df
        y = None
    
    # Apply advanced feature engineering
    advanced_fe = AdvancedFeatureEngineering()
    
    # Create domain-specific features
    X = advanced_fe.create_domain_specific_features(X)
    
    # Create time-based features if possible
    X = advanced_fe.create_time_based_features(X)
    
    # Create cluster features (using a subset of numerical features)
    numerical_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    if len(numerical_cols) >= 2:  # Need at least 2 features for clustering
        X = advanced_fe.create_cluster_features(X, feature_cols=numerical_cols[:5])  # Use max 5 features
    
    # Add target back if it existed
    if y is not None:
        X[target_column] = y
    
    return X


# Backward compatibility with the FeatureEngineering class in data_preparation.py
def create_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Backward compatible function that uses the original FeatureEngineering class
    and adds comprehensive features.
    """
    # Use the original feature engineering
    original_fe = FeatureEngineering()
    df = original_fe.create_derived_features(df)
    
    # Add comprehensive features
    df = create_comprehensive_feature_set(df)
    
    return df
