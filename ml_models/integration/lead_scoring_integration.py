# Integration module for connecting ML models with SalesCompass lead system
# Provides hooks and interfaces to integrate predictive models with the existing lead management system

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import pandas as pd

from ..api.model_api import LeadScoringPredictor
from ..models.base_model import model_registry
from ..data.data_adapter import salescompass_adapter
from ..inference.predictor import create_predictor


class LeadScoringIntegration:
    """
    Integration class to connect ML models with SalesCompass lead management system.
    Provides methods to update lead scores, trigger actions based on predictions, and
    synchronize model predictions with the lead database.
    """
    
    def __init__(self, model_id: str):
        """
        Initialize the lead scoring integration.
        
        Args:
            model_id: ID of the lead scoring model to use
        """
        self.model_id = model_id
        self.logger = logging.getLogger(__name__)
        
        # Create predictor for lead scoring
        self.predictor = create_predictor(model_id)
        if not isinstance(self.predictor, LeadScoringPredictor):
            raise ValueError(f"Model {model_id} is not a lead scoring model")
        
        # Verify model is loaded
        model = model_registry.get_model(model_id)
        if not model or not model.is_trained:
            raise ValueError(f"Model {model_id} is not available or not trained")
    
    def score_single_lead(self, lead_id: int) -> Dict[str, Any]:
        """
        Score a single lead by ID.
        
        Args:
            lead_id: ID of the lead to score
            
        Returns:
            Dictionary with scoring results
        """
        try:
            # Extract lead data using the data adapter
            # For a single lead, we'll query directly from the database
            lead_data = salescompass_adapter.extract_lead_data(limit=1)
            lead_data = lead_data[lead_data['lead_id'] == lead_id]
            
            if lead_data.empty:
                raise ValueError(f"Lead with ID {lead_id} not found")
            
            # Prepare the lead data for scoring (remove lead_id and target variable if present)
            lead_record = lead_data.drop(columns=['lead_id'], errors='ignore').iloc[0].to_dict()
            
            # Score the lead
            result = self.predictor.predict_lead_score(lead_record)
            
            # Update the lead score in the database
            self._update_lead_score_in_db(lead_id, result['lead_score'])
            
            # Log the scoring event
            self.logger.info(f"Lead {lead_id} scored with model {self.model_id}: {result['lead_score']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error scoring lead {lead_id}: {str(e)}")
            raise
    
    def score_multiple_leads(self, lead_ids: List[int]) -> Dict[str, Any]:
        """
        Score multiple leads by their IDs.
        
        Args:
            lead_ids: List of lead IDs to score
            
        Returns:
            Dictionary with scoring results
        """
        try:
            # Extract data for all specified leads
            all_leads_data = salescompass_adapter.extract_lead_data()
            selected_leads = all_leads_data[all_leads_data['lead_id'].isin(lead_ids)]
            
            if selected_leads.empty:
                raise ValueError(f"No leads found for IDs: {lead_ids}")
            
            # Prepare data for scoring (remove lead_id column)
            scoring_data = selected_leads.drop(columns=['lead_id'], errors='ignore').to_dict('records')
            
            # Score all leads
            results = []
            for i, lead_record in enumerate(scoring_data):
                lead_id = lead_ids[i]
                result = self.predictor.predict_lead_score(lead_record)
                
                # Update the lead score in the database
                self._update_lead_score_in_db(lead_id, result['lead_score'])
                
                result['lead_id'] = lead_id
                results.append(result)
            
            # Log the batch scoring event
            self.logger.info(f"Scored {len(results)} leads with model {self.model_id}")
            
            return {
                'model_id': self.model_id,
                'total_leads_scored': len(results),
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error scoring multiple leads: {str(e)}")
            raise
    
    def score_all_leads(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Score all leads in the system.
        
        Args:
            limit: Optional limit on number of leads to score
            
        Returns:
            Dictionary with scoring results
        """
        try:
            # Extract all lead data
            all_leads_data = salescompass_adapter.extract_lead_data(limit=limit)
            
            if all_leads_data.empty:
                self.logger.info("No leads found to score")
                return {
                    'model_id': self.model_id,
                    'total_leads_scored': 0,
                    'results': [],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Prepare data for scoring (remove lead_id column)
            scoring_data = all_leads_data.drop(columns=['lead_id'], errors='ignore').to_dict('records')
            lead_ids = all_leads_data['lead_id'].tolist()
            
            # Score all leads
            results = []
            for i, lead_record in enumerate(scoring_data):
                lead_id = lead_ids[i]
                result = self.predictor.predict_lead_score(lead_record)
                
                # Update the lead score in the database
                self._update_lead_score_in_db(lead_id, result['lead_score'])
                
                result['lead_id'] = lead_id
                results.append(result)
            
            # Log the batch scoring event
            self.logger.info(f"Scored {len(results)} leads with model {self.model_id}")
            
            return {
                'model_id': self.model_id,
                'total_leads_scored': len(results),
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error scoring all leads: {str(e)}")
            raise
    
    def _update_lead_score_in_db(self, lead_id: int, new_score: int):
        """
        Update the lead score in the SalesCompass database.
        
        Args:
            lead_id: ID of the lead to update
            new_score: New lead score to set
        """
        # This would typically involve updating the lead in the Django database
        # For now, we'll just log the update
        self.logger.info(f"Updating lead {lead_id} score to {new_score}")
        
        # In a real implementation, this would be:
        # from core.leads.models import Lead
        # Lead.objects.filter(id=lead_id).update(lead_score=new_score, updated_at=timezone.now())
        
        # Also trigger any necessary events or workflows based on the new score
        self._trigger_score_based_actions(lead_id, new_score)
    
    def _trigger_score_based_actions(self, lead_id: int, new_score: int):
        """
        Trigger actions based on the new lead score.
        
        Args:
            lead_id: ID of the lead
            new_score: New lead score
        """
        # Determine lead qualification based on score
        if new_score >= 70:
            qualification = 'Hot Lead'
            # Trigger immediate follow-up workflow
            self._trigger_immediate_followup(lead_id)
        elif new_score >= 40:
            qualification = 'Warm Lead'
            # Schedule contact within 24 hours
            self._schedule_contact(lead_id)
        elif new_score >= 20:
            qualification = 'Cold Lead'
            # Add to nurturing campaign
            self._add_to_nurturing(lead_id)
        else:
            qualification = 'Unqualified'
            # Consider removing from active list
            self._consider_removal(lead_id)
        
        self.logger.info(f"Triggered actions for lead {lead_id} with score {new_score} ({qualification})")
    
    def _trigger_immediate_followup(self, lead_id: int):
        """
        Trigger immediate follow-up for hot leads.
        
        Args:
            lead_id: ID of the lead
        """
        # This would typically involve creating tasks, sending notifications, etc.
        self.logger.info(f"Scheduled immediate follow-up for lead {lead_id}")
        
        # In a real implementation, this might involve:
        # - Creating a high-priority task for the sales team
        # - Sending an email notification to the lead owner
        # - Triggering an automated phone call
        pass
    
    def _schedule_contact(self, lead_id: int):
        """
        Schedule contact for warm leads.
        
        Args:
            lead_id: ID of the lead
        """
        # This would typically involve creating tasks or scheduling activities
        self.logger.info(f"Scheduled contact for lead {lead_id}")
        pass
    
    def _add_to_nurturing(self, lead_id: int):
        """
        Add cold leads to nurturing campaign.
        
        Args:
            lead_id: ID of the lead
        """
        # This would typically involve adding to email sequences or nurturing workflows
        self.logger.info(f"Added lead {lead_id} to nurturing campaign")
        pass
    
    def _consider_removal(self, lead_id: int):
        """
        Consider removing unqualified leads from active list.
        
        Args:
            lead_id: ID of the lead
        """
        # This might involve flagging for review or adding to a "do not contact" list
        self.logger.info(f"Flagged lead {lead_id} for review (low score)")
        pass
    
    def get_model_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the integrated model.
        
        Returns:
            Dictionary with model performance metrics
        """
        model = model_registry.get_model(self.model_id)
        if not model:
            raise ValueError(f"Model {self.model_id} not found")
        
        return {
            'model_id': self.model_id,
            'model_type': model.model_spec.model_type.value,
            'is_trained': model.is_trained,
            'performance_metrics': model.performance_metrics,
            'feature_names': model.feature_names,
            'last_trained': model.last_trained.isoformat() if model.last_trained else None
        }
    
    def retrain_model_with_new_data(self, 
                                   days_back: int = 30,
                                   retrain_threshold: float = 0.05) -> Dict[str, Any]:
        """
        Retrain the model with recent data if performance has degraded.
        
        Args:
            days_back: Number of days of recent data to use for retraining
            retrain_threshold: Threshold for triggering retraining
            
        Returns:
            Dictionary with retraining results
        """
        from ..training.model_trainer import ModelTrainer
        from ..monitoring.performance_monitor import ModelPerformanceMonitor
        
        # Check if retraining is needed based on performance monitoring
        monitor = ModelPerformanceMonitor(model_registry.get_model(self.model_id))
        should_retrain, reason = monitor.should_retrain()
        
        if should_retrain or reason == "Performance degradation detected":
            self.logger.info(f"Retraining model {self.model_id} due to: {reason}")
            
            # Extract recent data for retraining
            # This would typically involve getting data from the last N days
            recent_data = salescompass_adapter.extract_lead_data(limit=1000)  # Get recent data
            
            if len(recent_data) < 100:  # Minimum data threshold
                self.logger.warning("Insufficient recent data for retraining")
                return {
                    'model_id': self.model_id,
                    'retrain_needed': True,
                    'retrain_performed': False,
                    'reason': 'Insufficient recent data',
                    'data_count': len(recent_data)
                }
            
            # Prepare features and target
            y_col = 'is_converted'  # Assuming this is the target column
            if y_col not in recent_data.columns:
                # If target column not present, we might need to derive it
                # For now, we'll skip retraining if target is missing
                self.logger.warning(f"Target column '{y_col}' not found in data")
                return {
                    'model_id': self.model_id,
                    'retrain_needed': True,
                    'retrain_performed': False,
                    'reason': f"Target column '{y_col}' not found",
                    'data_count': len(recent_data)
                }
            
            X = recent_data.drop(columns=[y_col], errors='ignore')
            y = recent_data[y_col]
            
            # Train the model
            trainer = ModelTrainer()
            results = trainer.train_model(model_registry.get_model(self.model_id), X, y)
            
            # Update the predictor with the retrained model
            self.predictor = create_predictor(self.model_id)
            
            return {
                'model_id': self.model_id,
                'retrain_needed': True,
                'retrain_performed': True,
                'retrain_reason': reason,
                'training_results': results,
                'data_count': len(recent_data)
            }
        else:
            return {
                'model_id': self.model_id,
                'retrain_needed': False,
                'retrain_performed': False,
                'reason': 'No retraining needed at this time',
                'data_count': 0
            }


def initialize_lead_scoring_integration(model_id: str) -> LeadScoringIntegration:
    """
    Initialize and return a lead scoring integration instance.
    
    Args:
        model_id: ID of the lead scoring model to use
        
    Returns:
        LeadScoringIntegration instance
    """
    return LeadScoringIntegration(model_id)
