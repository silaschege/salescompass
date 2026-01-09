"""
Configuration Templates for ML Ontologies.
Provides default settings and mapping rules for various domain ontologies.
"""

ONTOLOGY_CONFIG = {
    "competitive": {
        "update_frequency": "daily",
        "scrape_competitors": False, # Placeholder for web crawler
        "monitored_domains": ["competitor-a.com", "competitor-b.com"],
        "relationship_weights": {
            "feature_overlap": 0.8,
            "pricing_pressure": 0.9
        }
    },
    "product": {
        "sync_with_crm_catalog": True,
        "recommendation_threshold": 0.65,
        "max_recommendations": 3,
        "solution_mappings": {
            "crm": ["Sales Automation", "Lead Management"],
            "marketing": ["Email Campaigns", "Social Analytics"]
        }
    },
    "export": {
        "format": "turtle",
        "auto_export": False,
        "export_path": "exports/ontology/"
    },
    "models": {
        "registry_path": "ml_models.infrastructure.config.model_registry_config.MODEL_IMPLEMENTATIONS",
        "auto_register_enabled": True,
        "default_candidates": ["xgboost", "random_forest", "logistic_regression", "mlp"]
    }
}

def get_config(domain: str):
    return ONTOLOGY_CONFIG.get(domain, {})
