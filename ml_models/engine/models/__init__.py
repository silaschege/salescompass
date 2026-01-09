# ML Model Hierarchy
# Separated into foundational algorithms and specific usecase models

from . import foundation
from . import usecase

# Re-export key components for convenience
from .foundation import (
    BaseModel,
    ModelType,
    model_registry,
    XGBoostModel,
    RandomForestModel,
    EnsembleModel,
)
from .usecase.sales import (
    BaseOpportunityModel,
    WinProbabilityModel,
    DealScoringModel,
    RevenueForecastingModel,
)
from .usecase.customer import (
    LeadScoringXGBoostModel,
)

__all__ = [
    'foundation',
    'usecase',
    'BaseModel',
    'ModelType',
    'model_registry',
    'XGBoostModel',
    'RandomForestModel',
    'EnsembleModel',
    'BaseOpportunityModel',
    'WinProbabilityModel',
    'DealScoringModel',
    'RevenueForecastingModel',
    'LeadScoringXGBoostModel',
]
