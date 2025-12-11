# Model training framework for ML Models
# Handles the training process for different ML models

from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import make_scorer
import logging
import time
from datetime import datetime

from ..models.base_model import BaseModel
from ..config.settings import config


class ModelTrainer:
    """
    Training framework for ML models.
    Handles model training, validation, and hyperparameter tuning.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def train_model(self, 
                   model: BaseModel, 
                   X: pd.DataFrame, 
                   y: pd.Series,
                   validation_split: float = 0.2,
                   **kwargs) -> Dict[str, Any]:
        """
        Train a model with validation and performance tracking.
        
        Args:
            model: Model instance to train
            X: Training features
            y: Training targets
            validation_split: Proportion of data to use for validation
            **kwargs: Additional training parameters
            
        Returns:
            Dictionary with training results and metrics
        """
        start_time = time.time()
        
        # Perform training
        train_results = model.train(X, y, **kwargs)
        
        # Evaluate on training data
        train_metrics = model.evaluate(X, y)
        
        # Record training time
        train_results['training_time'] = time.time() - start_time
        train_results['completed_at'] = datetime.now().isoformat()
        
        # Add training metrics to results
        train_results['train_metrics'] = train_metrics
        
        self.logger.info(f"Model {model.model_spec.model_id} trained successfully in {train_results['training_time']:.2f}s")
        
        return train_results
    
    def cross_validate_model(self, 
                           model: BaseModel, 
                           X: pd.DataFrame, 
                           y: pd.Series,
                           cv_folds: int = 5,
                           scoring: str = 'f1') -> Dict[str, Any]:
        """
        Perform cross-validation on the model.
        
        Args:
            model: Model instance to validate
            X: Features for validation
            y: Targets for validation
            cv_folds: Number of cross-validation folds
            scoring: Scoring metric to use
            
        Returns:
            Dictionary with cross-validation results
        """
        if not model.is_trained:
            # For cross-validation, we need to train the model multiple times
            # so we'll use the sklearn estimator directly
            sklearn_model = model.model
        else:
            # If already trained, we can still do cross-validation with the underlying sklearn model
            sklearn_model = model.model
        
        # Set up cross-validation
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=config.random_state)
        
        # Perform cross-validation
        cv_scores = cross_val_score(sklearn_model, X, y, cv=cv, scoring=scoring)
        
        # Calculate statistics
        cv_results = {
            'cv_scores': cv_scores.tolist(),
            'mean_cv_score': float(np.mean(cv_scores)),
            'std_cv_score': float(np.std(cv_scores)),
            'min_cv_score': float(np.min(cv_scores)),
            'max_cv_score': float(np.max(cv_scores)),
            'cv_folds': cv_folds,
            'scoring': scoring
        }
        
        self.logger.info(f"Cross-validation completed. Mean {scoring}: {cv_results['mean_cv_score']:.4f} (+/- {cv_results['std_cv_score']*2:.4f})")
        
        return cv_results
    
    def hyperparameter_tuning(self, 
                            model: BaseModel,
                            X: pd.DataFrame,
                            y: pd.Series,
                            param_grid: Dict[str, List[Any]],
                            cv_folds: int = 3,
                            scoring: str = 'f1') -> Dict[str, Any]:
        """
        Perform hyperparameter tuning using grid search.
        
        Args:
            model: Model instance to tune
            X: Training features
            y: Training targets
            param_grid: Dictionary with parameter names as keys and lists of values to try
            cv_folds: Number of cross-validation folds
            scoring: Scoring metric to optimize
            
        Returns:
            Dictionary with best parameters and performance
        """
        from sklearn.model_selection import GridSearchCV
        
        # Create parameter grid combinations
        # For this basic implementation, we'll do a simple grid search
        # In a more advanced implementation, we could use RandomizedSearchCV or Bayesian optimization
        
        # Get the sklearn model
        sklearn_model = model.model
        
        # Set up grid search
        grid_search = GridSearchCV(
            estimator=sklearn_model,
            param_grid=param_grid,
            cv=cv_folds,
            scoring=scoring,
            n_jobs=-1,
            verbose=1
        )
        
        # Perform grid search
        grid_search.fit(X, y)
        
        # Update model with best parameters
        model.update_hyperparameters(**grid_search.best_params_)
        
        # Train the model with best parameters
        final_results = self.train_model(model, X, y)
        
        # Prepare results
        tuning_results = {
            'best_params': grid_search.best_params_,
            'best_score': float(grid_search.best_score_),
            'best_estimator': grid_search.best_estimator_,
            'all_results': [
                {
                    'params': result['params'],
                    'mean_test_score': float(result['mean_test_score']),
                    'std_test_score': float(result['std_test_score'])
                }
                for result in grid_search.cv_results_['params']
            ],
            'final_training_results': final_results
        }
        
        self.logger.info(f"Hyperparameter tuning completed. Best score: {tuning_results['best_score']:.4f}")
        
        return tuning_results
    
    def train_ensemble(self,
                      models: List[BaseModel],
                      X: pd.DataFrame,
                      y: pd.Series,
                      ensemble_weights: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Train an ensemble of models.
        
        Args:
            models: List of model instances to include in ensemble
            X: Training features
            y: Training targets
            ensemble_weights: Optional weights for each model in the ensemble
            
        Returns:
            Dictionary with ensemble training results
        """
        from ..models.ensemble_model import create_lead_scoring_ensemble
        
        # Train each individual model
        individual_results = []
        for i, model in enumerate(models):
            self.logger.info(f"Training individual model {i+1}/{len(models)}: {model.model_spec.name}")
            result = self.train_model(model, X, y)
            individual_results.append(result)
        
        # Create ensemble model
        ensemble_model = create_lead_scoring_ensemble(models)
        
        # Train the ensemble (this just sets up the voting mechanism)
        ensemble_results = ensemble_model.train(X, y)
        
        # Evaluate the ensemble
        ensemble_metrics = ensemble_model.evaluate(X, y)
        ensemble_results['ensemble_metrics'] = ensemble_metrics
        
        # Compare with individual models
        ensemble_results['individual_results'] = individual_results
        ensemble_results['ensemble_comparison'] = self._compare_ensemble_performance(
            individual_results, ensemble_metrics
        )
        
        self.logger.info(f"Ensemble training completed with {len(models)} base models")
        
        return ensemble_results
    
    def _compare_ensemble_performance(self, 
                                    individual_results: List[Dict[str, Any]], 
                                    ensemble_metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Compare ensemble performance with individual models.
        
        Args:
            individual_results: Results from individual model training
            ensemble_metrics: Metrics from ensemble evaluation
            
        Returns:
            Dictionary with comparison results
        """
        comparison = {
            'ensemble_metrics': ensemble_metrics
        }
        
        # Extract key metrics from individual models
        individual_metrics = []
        for i, result in enumerate(individual_results):
            if 'train_metrics' in result:
                individual_metrics.append(result['train_metrics'])
            else:
                # If train_metrics not in result, try to get evaluation metrics
                # This would require having evaluated the individual models separately
                pass
        
        # Calculate ensemble advantage for each metric
        if individual_metrics:
            for metric_name in individual_metrics[0].keys():
                if metric_name in ensemble_metrics:
                    ensemble_score = ensemble_metrics[metric_name]
                    individual_scores = [m[metric_name] for m in individual_metrics]
                    best_individual_score = max(individual_scores)
                    
                    comparison[f'{metric_name}_improvement'] = ensemble_score - best_individual_score
                    comparison[f'best_individual_{metric_name}'] = best_individual_score
        
        return comparison


class AutoMLTrainer(ModelTrainer):
    """
    Automated machine learning trainer that tries multiple algorithms and selects the best one.
    """
    
    def __init__(self):
        super().__init__()
        self.best_model = None
        self.best_score = 0
        self.best_model_name = ""
    
    def auto_train(self, 
                  model_candidates: List[BaseModel],
                  X: pd.DataFrame,
                  y: pd.Series,
                  validation_metric: str = 'f1',
                  cv_folds: int = 5) -> Dict[str, Any]:
        """
        Automatically train multiple models and select the best one.
        
        Args:
            model_candidates: List of model instances to try
            X: Training features
            y: Training targets
            validation_metric: Metric to use for model selection
            cv_folds: Number of cross-validation folds
            
        Returns:
            Dictionary with results for all models and the best model
        """
        results = {
            'candidate_models': [],
            'best_model_info': {},
            'training_summary': {}
        }
        
        for i, model in enumerate(model_candidates):
            self.logger.info(f"Training candidate model {i+1}/{len(model_candidates)}: {model.model_spec.name}")
            
            # Train the model
            train_result = self.train_model(model, X, y)
            
            # Perform cross-validation
            cv_result = self.cross_validate_model(model, X, y, cv_folds, validation_metric)
            
            # Store results
            model_result = {
                'model_id': model.model_spec.model_id,
                'model_name': model.model_spec.name,
                'training_result': train_result,
                'cv_result': cv_result,
                'is_best': False
            }
            
            results['candidate_models'].append(model_result)
            
            # Check if this is the best model so far
            cv_score = cv_result['mean_cv_score']
            if cv_score > self.best_score:
                self.best_score = cv_score
                self.best_model = model
                self.best_model_name = model.model_spec.name
                # Mark as best in results
                model_result['is_best'] = True
        
        # Set the best model info
        results['best_model_info'] = {
            'model_id': self.best_model.model_spec.model_id if self.best_model else None,
            'model_name': self.best_model_name,
            'best_cv_score': self.best_score
        }
        
        # Create training summary
        results['training_summary'] = {
            'total_models_trained': len(model_candidates),
            'best_model': self.best_model_name,
            'best_cv_score': self.best_score,
            'validation_metric': validation_metric
        }
        
        self.logger.info(f"AutoML training completed. Best model: {self.best_model_name} with CV score: {self.best_score:.4f}")
        
        return results
