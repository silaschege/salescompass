# Cross-validation framework for ML Models
# Implements various cross-validation strategies for model evaluation

from typing import Dict, Any, List, Tuple, Optional, Callable
import pandas as pd
import numpy as np
from sklearn.model_selection import (
    cross_val_score, StratifiedKFold, KFold, 
    TimeSeriesSplit, GroupKFold, ShuffleSplit
)
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, 
    f1_score, roc_auc_score, make_scorer
)
import logging

from ..models.base_model import BaseModel


class CrossValidationFramework:
    """
    Comprehensive cross-validation framework for evaluating ML models.
    Supports multiple cross-validation strategies and metrics.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def evaluate_model_cv(self, 
                         model: BaseModel,
                         X: pd.DataFrame, 
                         y: pd.Series,
                         cv_strategy: str = 'stratified_kfold',
                         cv_folds: int = 5,
                         scoring: List[str] = ['f1', 'precision', 'recall', 'accuracy', 'roc_auc'],
                         groups: Optional[np.ndarray] = None,
                         time_series: bool = False) -> Dict[str, Any]:
        """
        Evaluate a model using cross-validation with various strategies.
        
        Args:
            model: Model to evaluate
            X: Features
            y: Targets
            cv_strategy: Cross-validation strategy ('stratified_kfold', 'kfold', 'timeseries', 'group_kfold', 'shuffle')
            cv_folds: Number of folds (ignored for time series split)
            scoring: List of scoring metrics to compute
            groups: Groups for group-based cross-validation
            time_series: Whether to use time series split
            
        Returns:
            Dictionary with cross-validation results
        """
        # Map strategy to sklearn CV object
        cv_objects = {
            'stratified_kfold': StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42),
            'kfold': KFold(n_splits=cv_folds, shuffle=True, random_state=42),
            'shuffle': ShuffleSplit(n_splits=cv_folds, test_size=0.2, random_state=42),
        }
        
        # Handle time series and group-based splits
        if time_series:
            cv = TimeSeriesSplit(n_splits=cv_folds)
        elif cv_strategy == 'group_kfold':
            if groups is None:
                raise ValueError("Groups must be provided for group_kfold strategy")
            cv = GroupKFold(n_splits=cv_folds)
        else:
            cv = cv_objects.get(cv_strategy)
            if cv is None:
                raise ValueError(f"Unknown cross-validation strategy: {cv_strategy}")
        
        # Prepare scoring functions
        scoring_functions = {
            'accuracy': make_scorer(accuracy_score),
            'precision': make_scorer(precision_score, average='weighted', zero_division=0),
            'recall': make_scorer(recall_score, average='weighted', zero_division=0),
            'f1': make_scorer(f1_score, average='weighted', zero_division=0),
            'roc_auc': make_scorer(roc_auc_score, needs_proba=True)
        }
        
        # Compute cross-validation scores for each metric
        results = {
            'cv_strategy': cv_strategy,
            'cv_folds': cv_folds,
            'scoring_metrics': scoring,
            'fold_results': {},
            'aggregate_results': {}
        }
        
        for metric in scoring:
            if metric not in scoring_functions:
                self.logger.warning(f"Unknown scoring metric: {metric}, skipping...")
                continue
            
            # Use sklearn's cross_val_score for efficiency
            if metric == 'roc_auc' and len(np.unique(y)) == 2:  # Binary classification
                # For ROC AUC, ensure we have binary classification
                scores = cross_val_score(
                    model.model, X, y, 
                    cv=cv if cv_strategy != 'group_kfold' else cv.split(X, y, groups),
                    scoring='roc_auc'
                )
            else:
                scores = cross_val_score(
                    model.model, X, y, 
                    cv=cv if cv_strategy != 'group_kfold' else cv.split(X, y, groups),
                    scoring=scoring_functions[metric]
                )
            
            # Store fold results
            results['fold_results'][metric] = scores.tolist()
            
            # Calculate aggregate statistics
            results['aggregate_results'][metric] = {
                'mean': float(np.mean(scores)),
                'std': float(np.std(scores)),
                'min': float(np.min(scores)),
                'max': float(np.max(scores)),
                'median': float(np.median(scores))
            }
        
        # Calculate overall statistics
        results['overall_stats'] = {
            'n_samples': len(X),
            'n_features': X.shape[1],
            'n_classes': len(np.unique(y)),
            'class_distribution': dict(zip(*np.unique(y, return_counts=True)))
        }
        
        self.logger.info(f"Cross-validation completed using {cv_strategy} with {cv_folds} folds")
        
        return results
    
    def compare_cv_strategies(self,
                             model: BaseModel,
                             X: pd.DataFrame,
                             y: pd.Series,
                             strategies: List[str] = ['stratified_kfold', 'kfold', 'shuffle'],
                             cv_folds: int = 5,
                             scoring: str = 'f1') -> Dict[str, Any]:
        """
        Compare different cross-validation strategies for the same model.
        
        Args:
            model: Model to evaluate
            X: Features
            y: Targets
            strategies: List of strategies to compare
            cv_folds: Number of folds for strategies that use it
            scoring: Scoring metric to compare
            
        Returns:
            Dictionary with comparison results
        """
        comparison_results = {
            'scoring_metric': scoring,
            'strategies': {}
        }
        
        for strategy in strategies:
            try:
                results = self.evaluate_model_cv(
                    model, X, y, 
                    cv_strategy=strategy, 
                    cv_folds=cv_folds, 
                    scoring=[scoring]
                )
                comparison_results['strategies'][strategy] = results['aggregate_results'][scoring]
            except Exception as e:
                self.logger.error(f"Error evaluating strategy {strategy}: {str(e)}")
                comparison_results['strategies'][strategy] = {'error': str(e)}
        
        # Identify best strategy
        valid_strategies = {
            k: v for k, v in comparison_results['strategies'].items() 
            if 'error' not in v
        }
        
        if valid_strategies:
            best_strategy = max(valid_strategies, key=lambda k: valid_strategies[k]['mean'])
            comparison_results['best_strategy'] = {
                'strategy': best_strategy,
                'mean_score': valid_strategies[best_strategy]['mean'],
                'std_score': valid_strategies[best_strategy]['std']
            }
        
        return comparison_results
    
    def time_series_cv_evaluation(self,
                                 model: BaseModel,
                                 X: pd.DataFrame,
                                 y: pd.Series,
                                 n_splits: int = 5,
                                 scoring: str = 'f1') -> Dict[str, Any]:
        """
        Perform time series cross-validation, which respects temporal order.
        
        Args:
            model: Model to evaluate
            X: Features (should be ordered by time)
            y: Targets (should be ordered by time)
            n_splits: Number of splits
            scoring: Scoring metric
            
        Returns:
            Dictionary with time series CV results
        """
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        # Perform time series cross-validation manually to have more control
        fold_results = []
        
        for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            # Clone the model for this fold
            from sklearn.base import clone
            fold_model = clone(model.model)
            
            # Train the model
            fold_model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = fold_model.predict(X_test)
            
            # Calculate metrics
            if scoring == 'accuracy':
                score = accuracy_score(y_test, y_pred)
            elif scoring == 'precision':
                score = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            elif scoring == 'recall':
                score = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            elif scoring == 'f1':
                score = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            elif scoring == 'roc_auc' and len(np.unique(y)) == 2:
                y_proba = fold_model.predict_proba(X_test)[:, 1]
                score = roc_auc_score(y_test, y_proba)
            else:
                raise ValueError(f"Unknown scoring metric: {scoring}")
            
            fold_results.append({
                'fold': fold,
                'train_size': len(train_idx),
                'test_size': len(test_idx),
                'score': score,
                'train_date_range': (X.index[train_idx[0]] if hasattr(X.index, '__getitem__') else 'N/A',
                                   X.index[train_idx[-1]] if hasattr(X.index, '__getitem__') else 'N/A'),
                'test_date_range': (X.index[test_idx[0]] if hasattr(X.index, '__getitem__') else 'N/A',
                                  X.index[test_idx[-1]] if hasattr(X.index, '__getitem__') else 'N/A')
            })
        
        # Calculate aggregate results
        scores = [fold['score'] for fold in fold_results]
        aggregate_results = {
            'mean': float(np.mean(scores)),
            'std': float(np.std(scores)),
            'min': float(np.min(scores)),
            'max': float(np.max(scores)),
            'scores_by_fold': scores
        }
        
        return {
            'n_splits': n_splits,
            'scoring': scoring,
            'fold_results': fold_results,
            'aggregate_results': aggregate_results
        }
    
    def nested_cv_evaluation(self,
                           model: BaseModel,
                           X: pd.DataFrame,
                           y: pd.Series,
                           outer_cv_folds: int = 5,
                           inner_cv_folds: int = 3,
                           param_grid: Optional[Dict[str, List[Any]]] = None,
                           scoring: str = 'f1') -> Dict[str, Any]:
        """
        Perform nested cross-validation with hyperparameter tuning.
        
        Args:
            model: Model to evaluate
            X: Features
            y: Targets
            outer_cv_folds: Number of folds for outer CV (model evaluation)
            inner_cv_folds: Number of folds for inner CV (hyperparameter tuning)
            param_grid: Parameter grid for hyperparameter tuning
            scoring: Scoring metric
            
        Returns:
            Dictionary with nested CV results
        """
        from sklearn.model_selection import GridSearchCV
        
        outer_cv = StratifiedKFold(n_splits=outer_cv_folds, shuffle=True, random_state=42)
        inner_cv = StratifiedKFold(n_splits=inner_cv_folds, shuffle=True, random_state=42)
        
        outer_scores = []
        best_params_per_fold = []
        
        for fold, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            # Inner cross-validation for hyperparameter tuning
            if param_grid:
                grid_search = GridSearchCV(
                    estimator=model.model,
                    param_grid=param_grid,
                    cv=inner_cv,
                    scoring=scoring,
                    n_jobs=-1
                )
                grid_search.fit(X_train, y_train)
                
                # Get the best model from inner CV
                best_model = grid_search.best_estimator_
                best_params_per_fold.append(grid_search.best_params_)
                
                # Evaluate on outer test set
                y_pred = best_model.predict(X_test)
            else:
                # If no param_grid, just train the model
                model.model.fit(X_train, y_train)
                y_pred = model.model.predict(X_test)
                best_params_per_fold.append({})
            
            # Calculate score
            if scoring == 'accuracy':
                score = accuracy_score(y_test, y_pred)
            elif scoring == 'precision':
                score = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            elif scoring == 'recall':
                score = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            elif scoring == 'f1':
                score = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            elif scoring == 'roc_auc' and len(np.unique(y)) == 2:
                y_proba = best_model.predict_proba(X_test)[:, 1] if param_grid else model.model.predict_proba(X_test)[:, 1]
                score = roc_auc_score(y_test, y_proba)
            else:
                raise ValueError(f"Unknown scoring metric: {scoring}")
            
            outer_scores.append(score)
            
            self.logger.info(f"Nested CV Fold {fold+1}/{outer_cv_folds}: Score = {score:.4f}")
        
        # Calculate aggregate results
        results = {
            'outer_cv_folds': outer_cv_folds,
            'inner_cv_folds': inner_cv_folds,
            'scoring': scoring,
            'outer_scores': outer_scores,
            'mean_outer_score': float(np.mean(outer_scores)),
            'std_outer_score': float(np.std(outer_scores)),
            'min_outer_score': float(np.min(outer_scores)),
            'max_outer_score': float(np.max(outer_scores)),
            'best_params_per_fold': best_params_per_fold
        }
        
        self.logger.info(f"Nested CV completed. Mean score: {results['mean_outer_score']:.4f} (+/- {results['std_outer_score']*2:.4f})")
        
        return results


def create_cv_report(cv_results: Dict[str, Any]) -> str:
    """
    Create a human-readable report from cross-validation results.
    
    Args:
        cv_results: Results from cross-validation evaluation
        
    Returns:
        Formatted report string
    """
    report = []
    report.append("Cross-Validation Report")
    report.append("=" * 50)
    
    if 'cv_strategy' in cv_results:
        report.append(f"Strategy: {cv_results['cv_strategy']}")
        report.append(f"Folds: {cv_results['cv_folds']}")
    
    if 'overall_stats' in cv_results:
        stats = cv_results['overall_stats']
        report.append(f"Samples: {stats['n_samples']}")
        report.append(f"Features: {stats['n_features']}")
        report.append(f"Classes: {stats['n_classes']}")
    
    if 'aggregate_results' in cv_results:
        report.append("\nResults:")
        for metric, values in cv_results['aggregate_results'].items():
            report.append(f"  {metric}: {values['mean']:.4f} (+/- {values['std']*2:.4f})")
    
    return "\n".join(report)
