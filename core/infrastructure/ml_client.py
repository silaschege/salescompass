import os
import requests
import logging
from django.conf import settings

logger = logging.getLogger("ml.client")

class MLClient:
    """
    Client for interacting with the decoupled ML service via REST API.
    """
    
    def __init__(self):
        self.base_url = getattr(settings, 'ML_SERVICE_URL', 'http://localhost:8001/api/v1/ml/')
        self.timeout = 5 # seconds

    def get_lead_score(self, lead_instance) -> dict:
        """Fetch lead score from ML service by sending lead features."""
        try:
            url = f"{self.base_url}score/lead/"
            # Collect features needed by the model
            payload = {
                "id": lead_instance.id,
                "industry": getattr(lead_instance, 'industry', 'unknown'),
                "company_size": lead_instance.company_size or 0,
                "annual_revenue": float(lead_instance.annual_revenue or 0),
                "lead_source": lead_instance.lead_source,
            }
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch lead score for {lead_instance.id}: {str(e)}")
            return {"status": "error", "message": str(e)}

    def get_win_probability(self, opp_instance) -> dict:
        """Fetch win probability for an opportunity by sending features."""
        try:
            url = f"{self.base_url}predict/win-probability/"
            # Collect features
            payload = {
                "id": opp_instance.id,
                "amount": float(opp_instance.amount or 0),
                "stage_order": opp_instance.stage.order if opp_instance.stage else 0,
                "days_open": opp_instance.calculate_average_sales_cycle() if hasattr(opp_instance, 'calculate_average_sales_cycle') else 30,
            }
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch win probability for {opp_instance.id}: {str(e)}")
            return {"status": "error", "message": str(e)}

    def predict_revenue_forecast(self, opportunities_data: list) -> dict:
        """
        Request revenue forecast for a list of opportunities from ML engine.
        Expects list of dicts with 'amount' and 'probability'.
        """
        try:
            url = f"{self.base_url}predict/forecast/"
            payload = {"opportunities": opportunities_data}
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch revenue forecast: {str(e)}")
            # Fallback logic if API is down
            total_pipeline = sum(float(o.get('amount', 0)) for o in opportunities_data)
            weighted_forecast = sum(float(o.get('amount', 0)) * float(o.get('probability', 0)) for o in opportunities_data)
            return {
                "forecast_amount": total_pipeline,
                "weighted_forecast_amount": weighted_forecast,
                "status": "error_fallback"
            }

# Singleton Client
ml_client = MLClient()
