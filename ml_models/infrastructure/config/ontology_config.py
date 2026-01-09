# Ontology configuration for ML Models
# Defines the structure and relationships for the ML models as an independent system

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum


class ModelType(Enum):
    """Types of models in the ontology"""
    LEAD_SCORING = "lead_scoring"
    CONVERSION_PREDICTION = "conversion_prediction"
    DEAL_SIZE_PREDICTION = "deal_size_prediction"
    TIME_TO_CLOSE_PREDICTION = "time_to_close_prediction"
    REVENUE_FORECAST = "revenue_forecast"
    CUSTOM = "custom"


class DataType(Enum):
    """Data types for features in the ontology"""
    CATEGORICAL = "categorical"
    NUMERICAL = "numerical"
    BOOLEAN = "boolean"
    TEXT = "text"
    DATE = "date"
    DATETIME = "datetime"


@dataclass
class FeatureDefinition:
    """Definition of a feature in the ontology"""
    name: str
    data_type: DataType
    description: str
    required: bool = True
    default_value: Any = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None


@dataclass
class ModelSpecification:
    """Specification of a model in the ontology"""
    model_id: str
    model_type: ModelType
    name: str
    description: str
    version: str
    features: List[FeatureDefinition]
    target_variable: str
    algorithm: str
    hyperparameters: Dict[str, Any]
    performance_metrics: List[str]
    dependencies: List[str]


@dataclass
class DataAdapterSpecification:
    """Specification for data adapters in the ontology"""
    adapter_id: str
    name: str
    description: str
    source_system: str
    source_tables: List[str]
    feature_mappings: Dict[str, str] # ML model feature name to source field name
    required_features: List[str]
    optional_features: List[str]


@dataclass
class ModelOntology:
    """Ontology definition for the ML models system"""
    name: str = "SalesCompass ML Models Ontology"
    version: str = "1.0.0"
    description: str = "Ontology for machine learning models in SalesCompass"
    
    # Model specifications
    models: List[ModelSpecification] = None
    
    # Data adapter specifications
    data_adapters: List[DataAdapterSpecification] = None
    
    # Feature definitions that can be reused across models
    global_features: List[FeatureDefinition] = None
    
    def __post_init__(self):
        if self.models is None:
            self.models = []
        if self.data_adapters is None:
            self.data_adapters = []
        if self.global_features is None:
            self.global_features = []


# Define the main ontology instance
ontology = ModelOntology()


# Predefined feature definitions for lead scoring
LEAD_FEATURES = [
    FeatureDefinition(
        name="lead_score",
        data_type=DataType.NUMERICAL,
        description="Current lead score (0-100)",
        min_value=0,
        max_value=100
    ),
    FeatureDefinition(
        name="profile_completeness_score",
        data_type=DataType.NUMERICAL,
        description="Score based on completeness of lead profile (0-100)",
        min_value=0,
        max_value=100
    ),
    FeatureDefinition(
        name="company_size",
        data_type=DataType.NUMERICAL,
        description="Number of employees at the company",
        min_value=0
    ),
    FeatureDefinition(
        name="annual_revenue",
        data_type=DataType.NUMERICAL,
        description="Annual revenue of the company",
        min_value=0
    ),
    FeatureDefinition(
        name="industry",
        data_type=DataType.CATEGORICAL,
        description="Industry of the lead's company",
        allowed_values=[
            'tech', 'manufacturing', 'finance', 'healthcare', 
            'retail', 'energy', 'education', 'other'
        ]
    ),
    FeatureDefinition(
        name="lead_source",
        data_type=DataType.CATEGORICAL,
        description="Source of the lead",
        allowed_values=[
            'web', 'event', 'referral', 'ads', 'manual'
        ]
    ),
    FeatureDefinition(
        name="marketing_channel",
        data_type=DataType.CATEGORICAL,
        description="Marketing channel that brought the lead",
        allowed_values=[
            'email', 'social', 'paid_ads', 'content', 
            'seo', 'referral', 'event', 'direct', 'other'
        ]
    ),
    FeatureDefinition(
        name="days_since_creation",
        data_type=DataType.NUMERICAL,
        description="Number of days since lead creation",
        min_value=0
    ),
    FeatureDefinition(
        name="interaction_count",
        data_type=DataType.NUMERICAL,
        description="Number of interactions with the lead",
        min_value=0
    ),
    FeatureDefinition(
        name="last_interaction_days",
        data_type=DataType.NUMERICAL,
        description="Days since last interaction with lead",
        min_value=0
    ),
    FeatureDefinition(
        name="email_opened",
        data_type=DataType.BOOLEAN,
        description="Whether lead has opened emails"
    ),
    FeatureDefinition(
        name="link_clicked",
        data_type=DataType.BOOLEAN,
        description="Whether lead has clicked links in emails"
    ),
    FeatureDefinition(
        name="website_visited",
        data_type=DataType.BOOLEAN,
        description="Whether lead has visited website"
    ),
    FeatureDefinition(
        name="demo_requested",
        data_type=DataType.BOOLEAN,
        description="Whether lead has requested a demo"
    ),
    FeatureDefinition(
        name="proposal_downloaded",
        data_type=DataType.BOOLEAN,
        description="Whether lead has downloaded proposal"
    ),
    FeatureDefinition(
        name="is_converted",
        data_type=DataType.BOOLEAN,
        description="Whether lead has converted (target variable)",
        required=True
    )
]


# Predefined model specifications
LEAD_SCORING_MODEL = ModelSpecification(
    model_id="lead_scoring_v1",
    model_type=ModelType.LEAD_SCORING,
    name="Lead Scoring Model",
    description="Predicts the probability of lead conversion",
    version="1.0.0",
    features=LEAD_FEATURES,
    target_variable="is_converted",
    algorithm="RandomForest",
    hyperparameters={
        "n_estimators": 100,
        "max_depth": 10,
        "random_state": 42
    },
    performance_metrics=["precision", "recall", "f1_score", "auc_roc"],
    dependencies=["pandas", "scikit-learn", "numpy"]
)

# Add the model to the ontology
ontology.models.append(LEAD_SCORING_MODEL)


# Data adapter specification for SalesCompass
SALESCOMPASS_ADAPTER = DataAdapterSpecification(
    adapter_id="salescompass_adapter_v1",
    name="SalesCompass Data Adapter",
    description="Adapter for extracting data from SalesCompass system",
    source_system="SalesCompass",
    source_tables=["leads_lead", "leads_leadsource", "leads_leadstatus", 
                   "leads_industry", "leads_marketingchannel", "tasks_task"],
    feature_mappings={
        "lead_score": "leads_lead.lead_score",
        "company_size": "leads_lead.company_size",
        "annual_revenue": "leads_lead.annual_revenue",
        "industry": "leads_lead.industry",
        "lead_source": "leads_lead.lead_source",
        "marketing_channel": "leads_lead.marketing_channel",
        "is_converted": "leads_lead.status == 'converted'"
    },
    required_features=["lead_score", "is_converted"],
    optional_features=["company_size", "annual_revenue", "industry", 
                       "lead_source", "marketing_channel"]
)

# Add the adapter to the ontology
ontology.data_adapters.append(SALESCOMPASS_ADAPTER)
