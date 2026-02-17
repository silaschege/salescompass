# SalesCompass ML Engine (Decoupled)

## Architecture Overview
The ML module functions as a **High-Performance Inference Microservice** built with **FastAPI**. It is radically decoupled from the main CRM codebase, communicating exclusively via RESTful JSON/HTTP. This ensures maximum performance, independent scalability, and a clean separation of concerns.

### Key Technologies
- **Inference Server**: FastAPI 2.0 (Asynchronous & Pydantic-driven)
- **Intelligence Core**: Knowledge Graph & Ontological Reasoning
- **Engine**: Scikit-Learn, XGBoost, Pandas, PyTorch
- **API Specs**: Automatic OpenAPI/Swagger generation (available at `/docs`)

## Directory Structure

- **`main.py`**: FastAPI entry point and API route definitions.
- **`core/`**: The "Intelligence Core" of the system.
  - **`orchestrator.py`**: Manages the flow between CRM data and ML inference.
  - **`knowledge_graph.py`**: Core semantic data structure.
  - **`ontology/`**: Domain-specific event and entity definitions.
- **`engine/`**: 
  - **`models/`**: Foundational algorithms and specific use-case models.
  - **`agents/`**: Autonomous Action Agents for executing business logic based on ML insights.
  - **`inference/`**: Low-level prediction and execution logic.
- **`services/`**: High-level specialized services.
  - **`intelligence/`**: NLP services including **Sentiment Analysis**.
  - **`scoring/`**: Lead and opportunity scoring engines.
  - **`prediction/`**: Revenue and sales forecasting.
- **`infrastructure/`**: Compliance logging (Audit Trail), model registry, and performance monitoring.
- **`templates/`**: Standalone ML Dashboard for real-time monitoring.

## API Reference

The ML Engine provides several specialized endpoints under `/api/v1/ml/`:

### 1. Sales Intelligence
- `POST /api/v1/ml/lead-score`: Predicts lead quality based on industry, size, and source.
- `POST /api/v1/ml/win-probability`: Calculates the likelihood of closing a specific opportunity.
- `POST /api/v1/ml/revenue-forecast`: Provides weighted pipeline forecasting.

### 2. Cognitive Services
- `POST /api/v1/ml/predict/sentiment`: Analyzes text for positive/negative/neutral sentiment.
- `POST /api/v1/ml/ontology/event`: Validates and categorizes CRM events (meetings, calls) against the semantic ontology.

### 3. Monitoring & Insights
- **Interactive Docs**: `http://localhost:8001/docs`
- **Dashboard**: `http://localhost:8001/` provides health checks, drift detection, and agent policy management.

## Deployment & Run

### Development
```bash
uvicorn main:app --port 8001 --reload
```

### Production
The service is containerized and managed via Docker Compose.
- **Internal URL**: `http://ml_service:8001` (accessible by the CRM `web` container)
- **External URL**: Configure via `ML_SERVICE_URL` in the CRM environment settings.
