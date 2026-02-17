# SalesCompass ML Engine (Decoupled)

## Architecture Overview
The ML module functions as a **High-Performance Inference Microservice** built with **FastAPI**. It is radically decoupled from the main CRM codebase, communicating exclusively via RESTful JSON/HTTP. This ensure maximum performance, independent scalability, and a clean separation of concerns.

### Key Technologies
- **Inference Server**: FastAPI (Asynchronous & Pydantic-driven)
- **Engine**: Scikit-Learn, XGBoost, Pandas
- **Ontology**: Custom Knowledge Graph for semantic reasoning
- **API Specs**: Automatic OpenAPI/Swagger generation

### Directory Structure
- **`main.py`**: FastAPI entry point and API route definitions.
- **`core/`**: Ontological foundations (Concepts, Relationships, Knowledge Graph).
- **`engine/`**: 
  - **`models/`**: Foundational algorithms (foundation/) and domain models (usecase/).
  - **`agents/`**: Autonomous Action Agents for executing business logic based on ML insights.
- **`infrastructure/`**:
  - **`config/`**: Registry and specification management for models.
  - **`monitoring/`**: Performance tracking and drift detection logic.
- **`services/`**: High-level semantic services (Scoring, Prediction, Recommendation, NLP).
- **`templates/`**: Jinja2 templates for the standalone ML Dashboard.

## Key Components

### 1. Unified Inference API
All ML interactions occur via POST requests with JSON payloads. This eliminates the need for the ML module to access the CRM database directly.

### 2. Standalone Dashboard
A lightweight monitoring interface available at `http://localhost:8001/` providing:
- Model Registry & Health
- Inference Performance Analytics
- Explainability (XAI) deep-dives
- Agent Policy Management

## API Reference
Standard endpoints are available under `/api/v1/ml/` for common tasks:

- `POST /api/v1/ml/lead-score`: Accepts lead features (industry, size, etc.) and returns a score.
- `POST /api/v1/ml/win-probability`: Accepts opportunity data and predicts win probability.
- `POST /api/v1/ml/revenue-forecast`: Aggregates opportunity data for weighted forecasting.

Interactive documentation: `http://localhost:8001/docs`

## Run Command
```bash
uvicorn main:app --port 8001 --reload
```
