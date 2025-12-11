# API endpoints for ML Models
# Provides REST API for model inference and management

from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import pandas as pd

from ..models.base_model import model_registry
from ..inference.predictor import create_predictor, LeadScoringPredictor
from ..config.settings import config
from ..training.model_trainer import ModelTrainer


# Pydantic models for request/response validation
class PredictionRequest(BaseModel):
    """Request model for making predictions"""
    model_id: str = Field(..., description="ID of the model to use for prediction")
    input_data: List[Dict[str, Any]] = Field(..., description="List of input records to predict")
    include_probability: bool = Field(default=True, description="Whether to include prediction probability")
    include_explanation: bool = Field(default=False, description="Whether to include feature importance explanation")


class PredictionResponse(BaseModel):
    """Response model for prediction results"""
    predictions: List[Dict[str, Any]]
    model_id: str
    request_timestamp: str
    processing_time_ms: float


class LeadScoringRequest(BaseModel):
    """Request model for lead scoring"""
    model_id: str = Field(..., description="ID of the lead scoring model to use")
    lead_data: List[Dict[str, Any]] = Field(..., description="List of lead records to score")
    scoring_method: str = Field(default="probability", description="Method to convert prediction to score")


class LeadScoringResponse(BaseModel):
    """Response model for lead scoring results"""
    lead_scores: List[Dict[str, Any]]
    model_id: str
    request_timestamp: str
    processing_time_ms: float


class ModelInfoResponse(BaseModel):
    """Response model for model information"""
    model_id: str
    model_type: str
    name: str
    description: str
    is_trained: bool
    created_at: str
    last_trained: Optional[str]
    performance_metrics: Dict[str, Any]
    feature_names: List[str]
    algorithm: str


class ModelHealthResponse(BaseModel):
    """Response model for model health check"""
    status: str
    model_id: str
    loaded_models: int
    request_timestamp: str


# Initialize FastAPI app
app = FastAPI(
    title="SalesCompass ML Models API",
    description="API for machine learning models in SalesCompass",
    version="1.0.0"
)

# Initialize components
trainer = ModelTrainer()
logger = logging.getLogger(__name__)


@app.get("/")
def read_root():
    """Root endpoint for API health check"""
    return {
        "name": "SalesCompass ML Models API",
        "version": "1.0.0",
        "status": "running",
        "models_loaded": len(model_registry.models)
    }


@app.get("/health")
def health_check() -> ModelHealthResponse:
    """Health check endpoint"""
    return ModelHealthResponse(
        status="healthy",
        model_id="all",
        loaded_models=len(model_registry.models),
        request_timestamp=datetime.now().isoformat()
    )


@app.get("/models")
def list_models() -> List[str]:
    """List all available models"""
    return model_registry.list_models()


@app.get("/models/{model_id}")
def get_model_info(model_id: str) -> ModelInfoResponse:
    """Get information about a specific model"""
    model = model_registry.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model with ID '{model_id}' not found")
    
    model_info = model.get_model_info()
    
    return ModelInfoResponse(
        model_id=model_info['model_id'],
        model_type=model_info['model_type'],
        name=model_info['name'],
        description=model_info['description'],
        is_trained=model_info['is_trained'],
        created_at=model_info['created_at'],
        last_trained=model_info['last_trained'],
        performance_metrics=model_info['performance_metrics'],
        feature_names=model_info['feature_names'],
        algorithm=model_info['algorithm']
    )


@app.post("/predict", response_model=PredictionResponse)
def make_prediction(request: PredictionRequest) -> PredictionResponse:
    """Make predictions using a trained model"""
    import time
    start_time = time.time()
    
    try:
        # Create predictor
        predictor = create_predictor(request.model_id)
        
        # Make predictions
        predictions = predictor.predict_batch(
            request.input_data,
            include_probability=request.include_probability,
            include_explanation=request.include_explanation
        )
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return PredictionResponse(
            predictions=predictions,
            model_id=request.model_id,
            request_timestamp=datetime.now().isoformat(),
            processing_time_ms=processing_time
        )
    
    except Exception as e:
        logger.error(f"Error making prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error making prediction: {str(e)}")


@app.post("/lead-score", response_model=LeadScoringResponse)
def score_leads(request: LeadScoringRequest) -> LeadScoringResponse:
    """Score leads using a lead scoring model"""
    import time
    start_time = time.time()
    
    try:
        # Create lead scoring predictor
        predictor = create_predictor(request.model_id)
        if not isinstance(predictor, LeadScoringPredictor):
            raise HTTPException(
                status_code=400, 
                detail=f"Model '{request.model_id}' is not a lead scoring model"
            )
        
        # Score leads
        lead_scores = []
        for lead_data in request.lead_data:
            score_result = predictor.predict_lead_score(
                lead_data,
                scoring_method=request.scoring_method
            )
            lead_scores.append(score_result)
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return LeadScoringResponse(
            lead_scores=lead_scores,
            model_id=request.model_id,
            request_timestamp=datetime.now().isoformat(),
            processing_time_ms=processing_time
        )
    
    except Exception as e:
        logger.error(f"Error scoring leads: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scoring leads: {str(e)}")


@app.post("/batch-predict/{model_id}")
def batch_predict(model_id: str, input_data: List[Dict[str, Any]]) -> PredictionResponse:
    """Make batch predictions using a trained model (alternative endpoint)"""
    import time
    start_time = time.time()
    
    try:
        # Create predictor
        predictor = create_predictor(model_id)
        
        # Make predictions
        predictions = predictor.predict_batch(input_data)
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return PredictionResponse(
            predictions=predictions,
            model_id=model_id,
            request_timestamp=datetime.now().isoformat(),
            processing_time_ms=processing_time
        )
    
    except Exception as e:
        logger.error(f"Error making batch prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error making batch prediction: {str(e)}")


@app.get("/model-performance/{model_id}")
def get_model_performance(model_id: str):
    """Get performance metrics for a trained model"""
    model = model_registry.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model with ID '{model_id}' not found")
    
    if not model.is_trained:
        raise HTTPException(status_code=400, detail=f"Model '{model_id}' is not trained")
    
    return {
        "model_id": model_id,
        "performance_metrics": model.performance_metrics,
        "last_evaluated": datetime.now().isoformat()
    }


@app.post("/retrain/{model_id}")
def retrain_model(model_id: str, training_data: Dict[str, Any]):
    """Retrain a model with new data"""
    model = model_registry.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model with ID '{model_id}' not found")
    
    try:
        # Convert training data to DataFrame
        X = pd.DataFrame(training_data.get('features', []))
        y = pd.Series(training_data.get('targets', []))
        
        if len(X) != len(y):
            raise HTTPException(status_code=400, detail="Features and targets must have the same length")
        
        # Retrain the model
        results = model.train(X, y)
        
        return {
            "model_id": model_id,
            "retrain_results": results,
            "completed_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error retraining model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retraining model: {str(e)}")


# Additional utility endpoints
@app.get("/feature-importance/{model_id}")
def get_feature_importance(model_id: str):
    """Get feature importance for a trained model"""
    model = model_registry.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model with ID '{model_id}' not found")
    
    if not model.is_trained:
        raise HTTPException(status_code=400, detail=f"Model '{model_id}' is not trained")
    
    importance = model.get_feature_importance()
    
    return {
        "model_id": model_id,
        "feature_importance": importance,
        "retrieved_at": datetime.now().isoformat()
    }


@app.get("/model-registry")
def get_model_registry():
    """Get information about all registered models"""
    registry_info = {}
    for model_id in model_registry.list_models():
        model = model_registry.get_model(model_id)
        if model:
            registry_info[model_id] = {
                "model_type": model.model_spec.model_type.value,
                "name": model.model_spec.name,
                "is_trained": model.is_trained,
                "algorithm": model.model_spec.algorithm
            }
    
    return {
        "registered_models": registry_info,
        "total_models": len(registry_info),
        "retrieved_at": datetime.now().isoformat()
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Resource not found", "detail": str(exc)}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


def start_api(host: str = config.api_host, port: int = config.api_port):
    """
    Start the ML models API server.
    
    Args:
        host: Host to bind the server to
        port: Port to bind the server to
    """
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    # This would be run when executing this file directly
    # In practice, the API would be served through a proper ASGI server
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
