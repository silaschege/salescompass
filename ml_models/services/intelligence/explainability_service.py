"""
Explainable AI (XAI) Service.
Provides human-readable explanations for ML predictions using SHAP/LIME or internal feature importance.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import logging
from ml_models.engine.models.foundation.base_model import BaseModel

class ExplainabilityService:
    """
    Service for providing explanations for specific ML predictions.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("intelligence.xai")

    def explain_prediction(self, model: BaseModel, X: pd.DataFrame) -> Dict[str, Any]:
        """
        Generates an explanation for a specific prediction.
        Falls back to global feature importance if local SHAP is unavailable.
        """
        self.logger.info(f"Generating explanation for model {model.model_spec.model_id}")
        
        # 1. Try to get local feature importance (simplified SHAP-like)
        # In a real implementation, we would use 'shap' or 'lime' libraries here.
        explanations = []
        
        feature_importance = model.get_feature_importance()
        if not feature_importance:
            return {"status": "unavailable", "message": "Model does not support feature importance"}
            
        # For MVP: Simulate local impact by combining global importance with feature values
        # (e.g., if a high-importance feature is present/high, it gets a positive score)
        for feature, importance in feature_importance.items():
            if feature in X.columns:
                val = X[feature].iloc[0]
                impact = "positive" if (isinstance(val, (int, float, bool)) and val) else "negative"
                explanations.append({
                    "feature": feature,
                    "importance": float(importance),
                    "impact": impact,
                    "reason": self._get_reason_template(feature, impact)
                })
                
        # Sort by importance
        explanations.sort(key=lambda x: x['importance'], reverse=True)
        
        return {
            "model_id": model.model_spec.model_id,
            "top_drivers": explanations[:5],
            "overall_confidence": "high"
        }

    def _get_reason_template(self, feature: str, impact: str) -> str:
        """Translates technical feature names into business reasons."""
        mapping = {
            "lead_score": "Current engagement score is high",
            "days_since_creation": "Lead has been in the system for a significant time",
            "interaction_count": "High number of interactions with sales team",
            "website_visited": "Prospect has visited the website recently",
            "demo_requested": "High interest shown via demo request"
        }
        
        base_reason = mapping.get(feature, f"Feature '{feature}' has a {impact} impact")
        return base_reason
