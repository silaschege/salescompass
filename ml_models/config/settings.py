# Configuration settings for ML Models package

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class MLModelConfig:
    """Configuration for ML Models"""
    
    # Database settings for accessing SalesCompass data
    database_url: str = os.getenv('DATABASE_URL', 'sqlite:///salescompass.db')
    
    # Model storage settings
    model_storage_path: str = os.getenv('MODEL_STORAGE_PATH', './models/')
    model_version: str = os.getenv('MODEL_VERSION', 'v1.0.0')
    
    # Feature engineering settings
    max_features: int = int(os.getenv('MAX_FEATURES', '100'))
    feature_scaling_method: str = os.getenv('FEATURE_SCALING_METHOD', 'standard')
    
    # Training settings
    test_size: float = float(os.getenv('TEST_SIZE', '0.2'))
    random_state: int = int(os.getenv('RANDOM_STATE', '42'))
    cross_validation_folds: int = int(os.getenv('CV_FOLDS', '5'))
    
    # Model performance thresholds
    min_precision_threshold: float = float(os.getenv('MIN_PRECISION_THRESHOLD', '0.7'))
    min_recall_threshold: float = float(os.getenv('MIN_RECALL_THRESHOLD', '0.6'))
    
    # API settings
    api_host: str = os.getenv('API_HOST', '0.0.0.0')
    api_port: int = int(os.getenv('API_PORT', '8000'))
    api_workers: int = int(os.getenv('API_WORKERS', '1'))
    
    # Monitoring settings
    enable_monitoring: bool = os.getenv('ENABLE_MONITORING', 'true').lower() == 'true'
    monitoring_db_path: str = os.getenv('MONITORING_DB_PATH', './monitoring.db')
    
    # Performance tracking
    drift_detection_threshold: float = float(os.getenv('DRIFT_DETECTION_THRESHOLD', '0.1'))
    performance_check_interval: int = int(os.getenv('PERFORMANCE_CHECK_INTERVAL', '3600'))  # seconds


# Default configuration instance
config = MLModelConfig()
