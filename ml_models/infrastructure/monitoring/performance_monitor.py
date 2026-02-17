# Performance monitoring for ML Models
# Tracks model performance, detects drift, and manages model lifecycle

from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import pickle
import sqlite3
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, 
    f1_score, roc_auc_score, mean_squared_error
)
import json
import os

from ..config.settings import config
from ..models.base_model import BaseModel


class ModelPerformanceMonitor:
    """
    Monitors model performance, detects data/model drift, and manages model lifecycle.
    """
    
    def __init__(self, model: BaseModel, db_path: Optional[str] = None):
        """
        Initialize the performance monitor.
        
        Args:
            model: Model to monitor
            db_path: Path to SQLite database for storing metrics (defaults to config value)
        """
        self.model = model
        self.model_id = model.model_spec.model_id
        self.logger = logging.getLogger(__name__)
        
        # Use provided db path or default from config
        self.db_path = db_path or config.monitoring_db_path
        self._init_database()
        
        # Performance thresholds
        self.performance_thresholds = {
            'accuracy': config.min_precision_threshold,
            'precision': config.min_precision_threshold,
            'recall': config.min_recall_threshold,
            'f1_score': config.min_precision_threshold,
            'auc_roc': config.min_precision_threshold
        }
        
        # Drift detection parameters
        self.drift_threshold = config.drift_detection_threshold
        self.performance_check_interval = config.performance_check_interval  # seconds
    
    def _init_database(self):
        """Initialize the monitoring database with required tables."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create table for performance metrics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    data_hash TEXT,
                    sample_size INTEGER
                )
            ''')
            
            # Create table for drift detection
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS drift_detection (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    drift_type TEXT NOT NULL,  -- 'data_drift' or 'model_drift'
                    drift_score REAL NOT NULL,
                    threshold REAL NOT NULL,
                    is_drift_detected BOOLEAN NOT NULL,
                    feature_name TEXT
                )
            ''')
            
            # Create table for model versions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metrics_json TEXT NOT NULL
                )
            ''')
            
            conn.commit()
    
    def log_performance_metric(self, metric_name: str, metric_value: float, 
                              sample_size: Optional[int] = None, 
                              data_hash: Optional[str] = None):
        """
        Log a performance metric to the database.
        
        Args:
            metric_name: Name of the metric (e.g., 'accuracy', 'precision')
            metric_value: Value of the metric
            sample_size: Size of the sample used for the metric
            data_hash: Hash of the data used for metric calculation
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO performance_metrics 
                (model_id, metric_name, metric_value, sample_size, data_hash)
                VALUES (?, ?, ?, ?, ?)
            ''', (self.model_id, metric_name, metric_value, sample_size, data_hash))
            conn.commit()
        
        self.logger.info(f"Logged metric {metric_name} = {metric_value} for model {self.model_id}")
    
    def calculate_and_log_metrics(self, X: pd.DataFrame, y_true: pd.Series, 
                                 y_pred: Optional[pd.Series] = None) -> Dict[str, float]:
        """
        Calculate common performance metrics and log them.
        
        Args:
            X: Input features
            y_true: True target values
            y_pred: Predicted values (if None, will be calculated)
            
        Returns:
            Dictionary of calculated metrics
        """
        if y_pred is None:
            y_pred = pd.Series(self.model.predict(X))
        
        # Calculate metrics
        metrics = {}
        
        # Accuracy
        metrics['accuracy'] = accuracy_score(y_true, y_pred)
        
        # Precision (handle binary and multiclass cases)
        try:
            metrics['precision'] = precision_score(y_true, y_pred, average='weighted', zero_division=0)
        except:
            metrics['precision'] = 0.0
        
        # Recall
        try:
            metrics['recall'] = recall_score(y_true, y_pred, average='weighted', zero_division=0)
        except:
            metrics['recall'] = 0.0
        
        # F1 Score
        try:
            metrics['f1_score'] = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        except:
            metrics['f1_score'] = 0.0
        
        # AUC-ROC (only for binary classification)
        if len(np.unique(y_true)) == 2:
            try:
                y_proba = self.model.predict_proba(X)[:, 1]  # Get probability of positive class
                metrics['auc_roc'] = roc_auc_score(y_true, y_proba)
            except:
                metrics['auc_roc'] = 0.0
        
        # Log all metrics
        for metric_name, metric_value in metrics.items():
            self.log_performance_metric(metric_name, metric_value, sample_size=len(X))
        
        return metrics
    
    def detect_data_drift(self, reference_data: pd.DataFrame, current_data: pd.DataFrame,
                         features: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Detect data drift between reference and current data distributions.
        
        Args:
            reference_data: Reference dataset (typically training data)
            current_data: Current dataset to check for drift
            features: Specific features to check for drift (if None, uses all features)
            
        Returns:
            Dictionary with drift detection results
        """
        if features is None:
            features = list(reference_data.columns)
        
        drift_results = {
            'overall_drift_score': 0.0,
            'feature_drift_scores': {},
            'drift_detected': False,
            'features_with_drift': []
        }
        
        # Calculate drift for each feature
        for feature in features:
            if feature not in reference_data.columns or feature not in current_data.columns:
                continue
            
            ref_values = reference_data[feature].dropna()
            curr_values = current_data[feature].dropna()
            
            # Calculate drift using a simple statistical test (e.g., Kolmogorov-Smirnov)
            # For simplicity, we'll use a basic approach comparing statistical properties
            if pd.api.types.is_numeric_dtype(ref_values):
                # For numerical features, compare means and stds
                ref_mean, ref_std = ref_values.mean(), ref_values.std()
                curr_mean, curr_std = curr_values.mean(), curr_values.std()
                
                # Calculate standardized difference
                mean_diff = abs(ref_mean - curr_mean) / (ref_std + 1e-8)
                std_diff = abs(ref_std - curr_std) / (ref_std + 1e-8)
                
                drift_score = (mean_diff + std_diff) / 2
            else:
                # For categorical features, compare value distributions
                ref_dist = ref_values.value_counts(normalize=True)
                curr_dist = curr_values.value_counts(normalize=True)
                
                # Calculate overlap between distributions
                common_values = set(ref_dist.index) & set(curr_dist.index)
                if common_values:
                    drift_score = 1 - sum(min(ref_dist[v], curr_dist[v]) for v in common_values)
                else:
                    drift_score = 1.0  # Complete drift if no common values
            
            drift_results['feature_drift_scores'][feature] = drift_score
            
            # Check if this feature has significant drift
            if drift_score > self.drift_threshold:
                drift_results['drift_detected'] = True
                drift_results['features_with_drift'].append(feature)
            
            # Log drift detection result
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO drift_detection 
                    (model_id, drift_type, drift_score, threshold, is_drift_detected, feature_name)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (self.model_id, 'data_drift', drift_score, self.drift_threshold, 
                      drift_score > self.drift_threshold, feature))
                conn.commit()
        
        # Calculate overall drift score as average of feature drift scores
        if drift_results['feature_drift_scores']:
            drift_results['overall_drift_score'] = np.mean(
                list(drift_results['feature_drift_scores'].values())
            )
        
        return drift_results
    
    def check_model_performance_degradation(self, 
                                          recent_window_hours: int = 24,
                                          historical_window_hours: int = 168) -> Dict[str, Any]:
        """
        Check if model performance has degraded compared to historical performance.
        
        Args:
            recent_window_hours: Hours for recent performance window
            historical_window_hours: Hours for historical performance window
            
        Returns:
            Dictionary with performance degradation analysis
        """
        with sqlite3.connect(self.db_path) as conn:
            # Get recent performance metrics
            recent_cutoff = datetime.now() - timedelta(hours=recent_window_hours)
            historical_cutoff = datetime.now() - timedelta(hours=historical_window_hours)
            
            query = '''
                SELECT metric_name, AVG(metric_value) as avg_value, COUNT(*) as count
                FROM performance_metrics
                WHERE model_id = ? AND timestamp > ?
                GROUP BY metric_name
            '''
            
            recent_cursor = conn.execute(query, (self.model_id, recent_cutoff.isoformat()))
            recent_metrics = {row[0]: {'avg': row[1], 'count': row[2]} for row in recent_cursor.fetchall()}
            
            historical_cursor = conn.execute(query, (self.model_id, historical_cutoff.isoformat()))
            historical_metrics = {row[0]: {'avg': row[1], 'count': row[2]} for row in historical_cursor.fetchall()}
        
        degradation_results = {
            'performance_degraded': False,
            'degraded_metrics': [],
            'recent_performance': recent_metrics,
            'historical_performance': historical_metrics
        }
        
        # Compare recent vs historical performance
        for metric_name in recent_metrics:
            if metric_name in historical_metrics:
                recent_avg = recent_metrics[metric_name]['avg']
                historical_avg = historical_metrics[metric_name]['avg']
                
                # Calculate degradation (for most metrics, higher is better)
                degradation = historical_avg - recent_avg
                
                # Check if degradation exceeds threshold
                if degradation > (1.0 - self.performance_thresholds.get(metric_name, 0.7)):
                    degradation_results['performance_degraded'] = True
                    degradation_results['degraded_metrics'].append({
                        'metric': metric_name,
                        'recent_avg': recent_avg,
                        'historical_avg': historical_avg,
                        'degradation': degradation
                    })
        
        return degradation_results
    
    def should_retrain(self) -> Tuple[bool, str]:
        """
        Determine if the model should be retrained based on performance and drift.
        
        Returns:
            Tuple of (should_retrain: bool, reason: str)
        """
        # Check for data drift
        drift_check = self._check_recent_drift()
        
        # Check for performance degradation
        perf_check = self.check_model_performance_degradation()
        
        if drift_check.get('drift_detected', False):
            return True, "Data drift detected"
        elif perf_check.get('performance_degraded', False):
            return True, "Performance degradation detected"
        else:
            return False, "No retraining needed"
    
    def _check_recent_drift(self, hours: int = 24) -> Dict[str, Any]:
        """
        Check for drift detection results in the recent time window.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dictionary with drift check results
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as drift_count
                FROM drift_detection
                WHERE model_id = ? AND timestamp > ? AND is_drift_detected = 1
            ''', (self.model_id, cutoff_time.isoformat()))
            
            result = cursor.fetchone()
            drift_count = result[0] if result else 0
        
        return {
            'drift_detected': drift_count > 0,
            'recent_drift_count': drift_count
        }
    
    def get_performance_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get a summary of model performance over the specified number of days.
        
        Args:
            days: Number of days to include in summary
            
        Returns:
            Dictionary with performance summary
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            # Get performance metrics
            query = '''
                SELECT metric_name, 
                       AVG(metric_value) as avg_value,
                       MIN(metric_value) as min_value,
                       MAX(metric_value) as max_value,
                       COUNT(*) as count
                FROM performance_metrics
                WHERE model_id = ? AND timestamp > ?
                GROUP BY metric_name
            '''
            
            cursor = conn.execute(query, (self.model_id, cutoff_date.isoformat()))
            metrics_summary = {
                row[0]: {
                    'avg_value': row[1],
                    'min_value': row[2],
                    'max_value': row[3],
                    'count': row[4]
                } for row in cursor.fetchall()
            }
        
        return {
            'model_id': self.model_id,
            'days': days,
            'metrics_summary': metrics_summary,
            'total_evaluations': sum(m['count'] for m in metrics_summary.values()) if metrics_summary else 0
        }
    
    def store_model_version(self, metrics: Dict[str, float], version: str = None):
        """
        Store a model version with its performance metrics.
        
        Args:
            metrics: Performance metrics for this version
            version: Version string (if None, uses model version)
        """
        if version is None:
            version = self.model.version
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO model_versions (model_id, version, metrics_json)
                VALUES (?, ?, ?)
            ''', (self.model_id, version, json.dumps(metrics)))
            conn.commit()
        
        self.logger.info(f"Stored model version {version} for {self.model_id}")


class ModelLifecycleManager:
    """
    Manages the lifecycle of ML models including versioning, deployment, and retirement.
    """
    
    def __init__(self, monitor: ModelPerformanceMonitor):
        """
        Initialize the lifecycle manager.
        
        Args:
            monitor: Performance monitor to use for lifecycle decisions
        """
        self.monitor = monitor
        self.model = monitor.model
        self.logger = logging.getLogger(__name__)
    
    def evaluate_and_decide(self) -> Dict[str, Any]:
        """
        Evaluate model health and decide next steps.
        
        Returns:
            Dictionary with evaluation results and recommendations
        """
        # Check performance degradation
        perf_check = self.monitor.check_model_performance_degradation()
        
        # Check data drift
        drift_check = self.monitor._check_recent_drift()
        
        # Determine if retraining is needed
        should_retrain, retrain_reason = self.monitor.should_retrain()
        
        evaluation = {
            'model_id': self.model.model_spec.model_id,
            'current_version': self.model.version,
            'performance_degraded': perf_check['performance_degraded'],
            'degraded_metrics': perf_check['degraded_metrics'],
            'drift_detected': drift_check['drift_detected'],
            'recent_drift_count': drift_check['recent_drift_count'],
            'should_retrain': should_retrain,
            'retrain_reason': retrain_reason,
            'recommendation': self._get_recommendation(should_retrain, retrain_reason),
            'evaluation_timestamp': datetime.now().isoformat()
        }
        
        return evaluation
    
    def _get_recommendation(self, should_retrain: bool, reason: str) -> str:
        """
        Get a recommendation based on evaluation results.
        
        Args:
            should_retrain: Whether retraining is recommended
            reason: Reason for the recommendation
            
        Returns:
            Recommendation string
        """
        if should_retrain:
            if 'drift' in reason.lower():
                return "Retrain model with new data to address data drift"
            elif 'degradation' in reason.lower():
                return "Retrain model to address performance degradation"
            else:
                return "Consider retraining model"
        else:
            return "Model is performing well, no immediate action needed"
    
    def deploy_model_version(self, model_path: str, version: str) -> bool:
        """
        Deploy a new model version.
        
        Args:
            model_path: Path to the saved model file
            version: Version string for the new model
            
        Returns:
            True if deployment was successful, False otherwise
        """
        try:
            # Load the new model
            self.model.load_model(model_path)
            
            # Update model version
            self.model.version = version
            
            # Store in model registry
            from ..models.base_model import model_registry
            model_registry.register_model(self.model)
            
            self.logger.info(f"Deployed model version {version} for {self.model_spec.model_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deploy model version {version}: {str(e)}")
            return False
