from typing import Dict, Any
import pandas as pd
from ml_models.engine.models.foundation.base_model import model_registry


class LeadScoringService:
    def score_lead(self, lead: Any) -> Dict[str, Any]:
        """
        Coordinates lead scoring using the registered lead scoring model.
        Accepts any object (CRM model or mock) with lead features.
        """
        model = model_registry.get_model("lead_scoring_default")
        if not model:
            # Fallback to simple heuristic
            heuristic_score = getattr(lead, 'calculate_initial_score', lambda: 50)()
            return {'score': heuristic_score, 'method': 'heuristic'}
        
        # Prepare features
        data = {
            'industry': [getattr(lead, 'industry', 'unknown')],
            'company_size': [getattr(lead, 'company_size', 0) or 0],
            'annual_revenue': [float(getattr(lead, 'annual_revenue', 0) or 0)],
            'lead_source': [getattr(lead, 'lead_source', 'unknown')],
        }
        df = pd.DataFrame(data)
        
        score = model.predict_proba(df)[0][1] # Probability of class 1 (Qualified)
        return {'score': int(score * 100), 'method': 'ml'}

class OpportunityWinProbabilityService:
    def predict_win_probability(self, opp: Any) -> Dict[str, Any]:
        """
        Predicts win probability for a given opportunity payload.
        """
        model = model_registry.get_model("win_probability_default")
        if not model:
            # Fallback to stage-based probability or 50%
            stage_prob = 0.5
            if hasattr(opp, 'stage') and opp.stage:
                stage_prob = float(getattr(opp.stage, 'probability', 50)) / 100.0
            elif hasattr(opp, 'probability'):
                 stage_prob = float(opp.probability) / 100.0 if float(opp.probability) > 1 else float(opp.probability)

            return {'probability': stage_prob, 'method': 'stage_default'}
            
        data = {
            'amount': [float(getattr(opp, 'amount', 0))],
            'days_open': [getattr(opp, 'days_open', 30)], 
            'stage_order': [getattr(opp, 'stage_order', 1)],
        }
        df = pd.DataFrame(data)
        
        prob = model.predict_proba(df)[0][1]
        return {'probability': float(prob), 'method': 'ml'}
