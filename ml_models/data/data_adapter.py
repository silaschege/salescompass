# Data adapter for SalesCompass integration
# This module provides the interface between SalesCompass and the ML models

import pandas as pd
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import os

from ..config.ontology_config import DataAdapterSpecification, ontology
from ..config.settings import config


class SalesCompassDataAdapter:
    """
    Data adapter for extracting and transforming data from SalesCompass for ML models.
    This adapter follows the ontology specification for SalesCompass data integration.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize the data adapter with a connection to SalesCompass database.
        
        Args:
            connection_string: Database connection string. If None, uses config value.
        """
        self.connection_string = connection_string or config.database_url
        self.engine = create_engine(self.connection_string)
        self.adapter_spec = self._get_adapter_spec()
        
    def _get_adapter_spec(self) -> DataAdapterSpecification:
        """Get the SalesCompass adapter specification from ontology."""
        for adapter in ontology.data_adapters:
            if adapter.adapter_id == "salescompass_adapter_v1":
                return adapter
        raise ValueError("SalesCompass adapter specification not found in ontology")
    
    def extract_lead_data(self, 
                         tenant_id: Optional[str] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         limit: Optional[int] = None) -> pd.DataFrame:
        """
        Extract lead data from SalesCompass for ML model training/prediction.
        
        Args:
            tenant_id: Specific tenant to extract data for (for multi-tenant systems)
            start_date: Start date for data extraction
            end_date: End date for data extraction
            limit: Maximum number of records to extract
            
        Returns:
            DataFrame with lead data matching the ontology feature definitions
        """
        # Build the query based on the adapter specification
        query = self._build_lead_query(tenant_id, start_date, end_date, limit)
        
        # Execute the query and return the result
        df = pd.read_sql_query(text(query), self.engine)
        
        # Transform the data to match the ML model feature requirements
        df = self._transform_lead_data(df)
        
        return df
    
    def _build_lead_query(self, 
                         tenant_id: Optional[str] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         limit: Optional[int] = None) -> str:
        """
        Build SQL query for extracting lead data based on adapter specification.
        """
        # Base query to get all necessary lead data
        query = """
        SELECT 
            l.id as lead_id,
            l.lead_score,
            l.company_size,
            l.annual_revenue,
            l.industry,
            l.lead_source,
            l.marketing_channel,
            l.status,
            l.created_at,
            l.updated_at,
            l.lead_acquisition_date,
            l.cac_cost,
            l.business_type,
            l.funding_stage,
            l.job_title,
            l.country,
            ls.label as source_label,
            lsr.label as status_label,
            i.label as industry_label,
            mc.label as marketing_channel_label,
            -- Calculate derived features
            CASE 
                WHEN l.status = 'converted' THEN 1 
                ELSE 0 
            END as is_converted,
            julianday('now') - julianday(l.created_at) as days_since_creation,
            -- Placeholder for interaction count (would need to join with interaction logs)
            0 as interaction_count,
            CASE 
                WHEN l.email IS NOT NULL AND l.email != '' THEN 1 
                ELSE 0 
            END as has_email,
            CASE 
                WHEN l.phone IS NOT NULL AND l.phone != '' THEN 1 
                ELSE 0 
            END as has_phone,
            CASE 
                WHEN l.job_title IS NOT NULL AND l.job_title != '' THEN 1 
                ELSE 0 
            END as has_job_title
        FROM leads_lead l
        LEFT JOIN leads_leadsource ls ON l.source_ref_id = ls.id
        LEFT JOIN leads_leadstatus lsr ON l.status_ref_id = lsr.id
        LEFT JOIN leads_industry i ON l.industry_ref_id = i.id
        LEFT JOIN leads_marketingchannel mc ON l.marketing_channel_ref_id = mc.id
        """
        
        # Add tenant filter if specified
        if tenant_id:
            query += f" WHERE l.tenant_id = '{tenant_id}'"
        else:
            # Filter out records with null tenant_id if not specified (for multi-tenant systems)
            query += " WHERE l.tenant_id IS NOT NULL"
        
        # Add date filters if specified
        if start_date:
            query += f" AND l.created_at >= '{start_date.strftime('%Y-%m-%d')}'"
        if end_date:
            query += f" AND l.created_at <= '{end_date.strftime('%Y-%m-%d')}'"
        
        # Add limit if specified
        if limit:
            query += f" LIMIT {limit}"
        
        return query
    
    def _transform_lead_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the raw lead data to match the ML model feature requirements.
        """
        # Create a copy of the dataframe to avoid modifying the original
        transformed_df = df.copy()
        
        # Calculate profile completeness score
        transformed_df['profile_completeness_score'] = (
            (transformed_df['has_email'] * 20) +
            (transformed_df['has_phone'] * 20) +
            (transformed_df['has_job_title'] * 15) +
            (transformed_df['company_size'].notna().astype(int) * 15) +
            (transformed_df['annual_revenue'].notna().astype(int) * 15) +
            (transformed_df['industry'].notna().astype(int) * 10) +
            (transformed_df['country'].notna().astype(int) * 5)
        ).clip(upper=100)
        
        # Map industry to standardized values
        industry_mapping = {
            'tech': 'technology',
            'manufacturing': 'manufacturing',
            'finance': 'financial_services',
            'healthcare': 'healthcare',
            'retail': 'retail',
            'energy': 'energy',
            'education': 'education',
            'other': 'other'
        }
        transformed_df['industry'] = transformed_df['industry'].map(industry_mapping).fillna('other')
        
        # Map lead source to standardized values
        source_mapping = {
            'web': 'web_form',
            'event': 'event',
            'referral': 'referral',
            'ads': 'paid_ads',
            'manual': 'manual_entry'
        }
        transformed_df['lead_source'] = transformed_df['lead_source'].map(source_mapping).fillna('other')
        
        # Map marketing channel to standardized values
        channel_mapping = {
            'email': 'email_marketing',
            'social': 'social_media',
            'paid_ads': 'paid_advertising',
            'content': 'content_marketing',
            'seo': 'seo',
            'referral': 'referral',
            'event': 'events',
            'direct': 'direct_traffic',
            'other': 'other'
        }
        transformed_df['marketing_channel'] = transformed_df['marketing_channel'].map(channel_mapping).fillna('other')
        
        # Fill missing values for numerical features
        numerical_features = [
            'lead_score', 'company_size', 'annual_revenue', 
            'days_since_creation', 'profile_completeness_score'
        ]
        for feature in numerical_features:
            if feature in transformed_df.columns:
                transformed_df[feature] = transformed_df[feature].fillna(transformed_df[feature].median())
        
        # Fill missing values for categorical features
        categorical_features = [
            'industry', 'lead_source', 'marketing_channel', 'business_type'
        ]
        for feature in categorical_features:
            if feature in transformed_df.columns:
                transformed_df[feature] = transformed_df[feature].fillna('unknown')
        
        # Create boolean features for engagement indicators
        # These would be populated from actual interaction data in a real implementation
        engagement_features = [
            'email_opened', 'link_clicked', 'website_visited', 
            'demo_requested', 'proposal_downloaded'
        ]
        for feature in engagement_features:
            if feature not in transformed_df.columns:
                transformed_df[feature] = 0 # Default to 0 if no interaction data available
        
        # Calculate days since last interaction (placeholder - would use actual interaction data)
        transformed_df['last_interaction_days'] = transformed_df['days_since_creation']
        
        # Select only the features defined in the ontology
        required_features = [f.name for f in self.adapter_spec.required_features]
        optional_features = [f.name for f in self.adapter_spec.optional_features]
        all_defined_features = required_features + optional_features
        
        # Keep only features that are defined in the ontology
        available_features = [col for col in all_defined_features if col in transformed_df.columns]
        transformed_df = transformed_df[available_features]
        
        return transformed_df
    
    def get_feature_mappings(self) -> Dict[str, str]:
        """
        Get the feature mappings as defined in the adapter specification.
        
        Returns:
            Dictionary mapping ML model feature names to source field names
        """
        return self.adapter_spec.feature_mappings
    
    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate the extracted data against the ontology requirements.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': True,
            'missing_features': [],
            'data_quality_issues': [],
            'row_count': len(df)
        }
        
        # Check for required features
        for feature in self.adapter_spec.required_features:
            if feature not in df.columns:
                results['valid'] = False
                results['missing_features'].append(feature)
        
        # Check for data quality issues
        for col in df.columns:
            if df[col].isnull().all():
                results['data_quality_issues'].append(f"All values are null for feature: {col}")
            elif df[col].dtype in ['int64', 'float64']:
                if (df[col] < 0).any() and col in ['company_size', 'annual_revenue', 'lead_score']:
                    results['data_quality_issues'].append(f"Negative values found for non-negative feature: {col}")
        
        return results


# Singleton instance for easy access
salescompass_adapter = SalesCompassDataAdapter()
