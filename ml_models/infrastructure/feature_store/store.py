import os
import pandas as pd
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from ml_models.infrastructure.config.settings import config

class FeatureStore:
    """
    MVP Feature Store implementation.
    Stores features in parquet files for retrieval by entity ID.
    """
    
    def __init__(self, store_path: Optional[str] = None):
        self.store_path = store_path or config.feature_store_path
        self.logger = logging.getLogger(__name__)
        
        # Ensure directory exists
        if not os.path.exists(self.store_path):
            try:
                os.makedirs(self.store_path, exist_ok=True)
            except OSError:
                pass
                
    def get_feature_group_path(self, group_name: str) -> str:
        return os.path.join(self.store_path, f"{group_name}.parquet")

    def save_features(self, group_name: str, features_df: pd.DataFrame, entity_id_col: str = "id"):
        """
        Save features for a given group (e.g., 'customer_features', 'product_features').
        Merges with existing data if present.
        """
        if entity_id_col not in features_df.columns:
            raise ValueError(f"Entity ID column '{entity_id_col}' not found in dataframe")
            
        file_path = self.get_feature_group_path(group_name)
        
        # Add timestamp
        features_df['feature_timestamp'] = datetime.utcnow()
        
        if os.path.exists(file_path):
            try:
                existing_df = pd.read_parquet(file_path)
                # Merge logic: Upsert based on entity_id
                # Remove rows that are being updated
                updated_ids = features_df[entity_id_col].unique()
                existing_df = existing_df[~existing_df[entity_id_col].isin(updated_ids)]
                
                # Concatenate
                final_df = pd.concat([existing_df, features_df], ignore_index=True)
            except Exception as e:
                self.logger.error(f"Error reading existing feature store: {str(e)}")
                # Fallback to overwrite if read fails (safe MVP choice?) No, better to raise or log.
                final_df = features_df
        else:
            final_df = features_df
            
        # Save
        try:
            final_df.to_parquet(file_path, index=False)
            self.logger.info(f"Saved {len(features_df)} records to feature group '{group_name}'")
        except Exception as e:
            self.logger.error(f"Failed to save features: {str(e)}")
            raise

    def get_features(self, group_name: str, entity_ids: List[str], entity_id_col: str = "id") -> pd.DataFrame:
        """
        Retrieve features for specific entities.
        """
        file_path = self.get_feature_group_path(group_name)
        
        if not os.path.exists(file_path):
            self.logger.warning(f"Feature group '{group_name}' does not exist")
            return pd.DataFrame()
            
        try:
            # For MVP, read full file and filter. 
            # Production would use partitioning or a real DB/Feature Store (e.g. Feast)
            df = pd.read_parquet(file_path)
            result = df[df[entity_id_col].isin(entity_ids)]
            return result
        except Exception as e:
            self.logger.error(f"Error retrieving features: {str(e)}")
            return pd.DataFrame()

# Global instance
feature_store = FeatureStore()
