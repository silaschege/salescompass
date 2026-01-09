"""
Configuration for Model Registry and Factory.
Maps algorithm identifiers to their corresponding class implementations.
"""

MODEL_IMPLEMENTATIONS = {
    "random_forest": "ml_models.engine.models.foundation.random_forest.RandomForestModel",
    "xgboost": "ml_models.engine.models.foundation.xgboost.XGBoostModel",
    "logistic_regression": "ml_models.engine.models.foundation.logistic_regression.LogisticRegressionModel",
    "svm": "ml_models.engine.models.foundation.support_vector_machine.SupportVectorMachineModel",
    "mlp": "ml_models.engine.models.foundation.neural_network.MultiLayerPerceptronModel",
    "lstm": "ml_models.engine.models.foundation.time_series_lstm.LSTMFineTuner",
    "transformer": "ml_models.engine.models.foundation.transformer_nlp.TransformerNLPModel",
    "lightgbm": "ml_models.engine.models.foundation.lightgbm_model.LightGBMModel",
}

def get_implementation_path(algorithm_id: str) -> str:
    """Returns the full module path for a given algorithm ID."""
    return MODEL_IMPLEMENTATIONS.get(algorithm_id.lower())
