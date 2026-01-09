import pandas as pd
from decimal import Decimal
from typing import Dict, Any, List
from django.utils import timezone
from ml_models.engine.models.usecase.sales.revenue_forecast import RevenueForecastingModel

# In a real system, we'd load a trained model. 
# For now, we instantiate the heuristic model.
_model_instance = RevenueForecastingModel()
_model_instance.is_trained = True

def predict_forecast_for_opportunities(opportunities: List[Any]) -> Dict[str, Decimal]:
    """
    Predict forest revenue for a list of Opportunity objects.
    
    Args:
        opportunities: List of Opportunity Django models
        
    Returns:
        Dict with 'forecast_amount' and 'weighted_forecast_amount'
    """
    if not opportunities:
        return {
            'forecast_amount': Decimal('0.00'),
            'weighted_forecast_amount': Decimal('0.00')
        }
        
    # 1. Prepare Features
    # Convert Django objects to DataFrame for the model
    data = []
    for opp in opportunities:
        data.append({
            'amount': float(opp.amount),
            'probability': float(opp.probability or 0.0) 
            # Note: Probability is 0.0-1.0 as per recent fix
        })
        
    df = pd.DataFrame(data)
    
    # 2. Inference
    # Total nominal amount (simple sum)
    total_amount = df['amount'].sum()
    
    # Weighted amount (Model prediction)
    # The model predicts the "expected value" of each deal
    expected_values = _model_instance.predict(df)
    total_weighted = expected_values.sum()
    
    return {
        'forecast_amount': Decimal(str(total_amount)),
        'weighted_forecast_amount': Decimal(str(total_weighted))
    }
