import os
import sys
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

# Ensure the project root is in sys.path to import ml_models modules
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from core.orchestrator import orchestrator
from services.intelligence.nlp_service import SentimentAnalyzer
from core.ontology.event_ontology import EventOntology
from infrastructure.compliance.audit_logger import audit_logger

app = FastAPI(
    title="SalesCompass ML Engine",
    description="High-performance decoupled ML inference and monitoring service.",
    version="2.0.0"
)

# Static and Templates
templates_dir = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=templates_dir)

# --- Pydantic Models ---

class LeadData(BaseModel):
    id: str
    industry: Optional[str] = "unknown"
    company_size: Optional[int] = 0
    annual_revenue: Optional[float] = 0.0
    lead_source: Optional[str] = "unknown"

class OpportunityData(BaseModel):
    id: str
    amount: float
    stage_order: Optional[int] = 1
    days_open: Optional[int] = 30
    probability: Optional[float] = 0.5

class ForecastOpportunity(BaseModel):
    amount: float
    probability: float

class ForecastPayload(BaseModel):
    opportunities: List[ForecastOpportunity]

class SentimentPayload(BaseModel):
    text: str
    context: Optional[str] = None

class EventInfo(BaseModel):
    title: str
    event_type: str  # meeting, call, email
    duration_minutes: int
    participants: List[str]

# --- API Routes ---

@app.post("/api/v1/ml/lead-score")
async def lead_score(data: LeadData):
    try:
        from types import SimpleNamespace
        # Convert Pydantic model to namespace for the orchestrator
        lead_instance = SimpleNamespace(**data.model_dump())
        outcome = orchestrator.handle_lead_update(data.id, lead_instance)
        return outcome
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ml/win-probability")
async def win_probability(data: OpportunityData):
    try:
        from types import SimpleNamespace
        opp_instance = SimpleNamespace(**data.model_dump())
        outcome = orchestrator.handle_opportunity_update(data.id, opp_instance)
        return outcome
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ml/revenue-forecast")
async def revenue_forecast(payload: ForecastPayload):
    try:
        total_pipeline = sum(opp.amount for opp in payload.opportunities)
        weighted_forecast = sum(opp.amount * opp.probability for opp in payload.opportunities)
        return {
            "forecast_amount": total_pipeline,
            "weighted_forecast_amount": weighted_forecast
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ml/predict/sentiment")
async def predict_sentiment(payload: SentimentPayload):
    try:
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze(payload.text)
        
        # Log Audit
        audit_logger.log_inference(
            model_id="sentiment_v1",
            inputs={"text_length": len(payload.text)},
            outputs=result.to_dict(),
            latency_ms=10.0
        )
        
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ml/ontology/event")
async def validate_event(event_info: EventInfo):
    try:
        ontology = EventOntology()
        # Create a concept simulation
        concept = ontology.create_meeting_event(
            meeting_id="sim_123",
            title=event_info.title,
            duration_min=event_info.duration_minutes,
            participants=event_info.participants
        )
        return {
            "valid": True,
            "concept_id": concept.id,
            "ontology_version": ontology.version,
            "inferred_type": concept.concept_type.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Dashboard View Routes ---

@app.get("/", response_class=HTMLResponse)
async def overview(request: Request):
    return templates.TemplateResponse("ml_dashboard/overview.html", {
        "request": request,
        "models": ['win_probability', 'lead_scoring', 'revenue_forecast', 'sentiment_analysis', 'event_reasoning'],
        "system_status": "FastAPI Active"
    })

@app.get("/monitoring", response_class=HTMLResponse)
async def monitoring(request: Request):
    return templates.TemplateResponse("ml_dashboard/monitoring.html", {
        "request": request,
        "alerts": [
            {'type': 'drift', 'message': 'Feature drift in Win Probability', 'time': '12m ago'},
            {'type': 'success', 'message': 'Auto-retrain of Lead Scoring complete', 'time': '1h ago'}
        ]
    })

@app.get("/insights", response_class=HTMLResponse)
async def insights(request: Request, model_id: str = "win_probability"):
    stats = {
        'f1': 0.912,
        'recall': 0.865,
        'auc': 0.934,
        'algorithm': 'FastAPI-XGBoost',
        'features': 45
    }
    return templates.TemplateResponse("ml_dashboard/insights.html", {
        "request": request,
        "stats": stats,
        "model_id": model_id
    })

@app.get("/user-guide", response_class=HTMLResponse)
async def user_guide(request: Request):
    return templates.TemplateResponse("ml_dashboard/user_guide.html", {"request": request})

@app.get("/policies", response_class=HTMLResponse)
async def policies(request: Request):
    return templates.TemplateResponse("ml_dashboard/agent_policies.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
