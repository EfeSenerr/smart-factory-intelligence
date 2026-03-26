"""FastAPI application with AG-UI endpoint for the manufacturing orchestrator."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent_framework_ag_ui import add_agent_framework_fastapi_endpoint

from backend.agents.orchestrator import create_orchestrator
from backend.api.dashboard import router as dashboard_router
from backend.api.pipeline import router as pipeline_router

app = FastAPI(
    title="Manufacturing Intelligence API",
    description="Multi-agent manufacturing PoC powered by Microsoft Agent Framework & Azure AI Foundry",
    version="0.1.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dashboard and data APIs
app.include_router(dashboard_router)
app.include_router(pipeline_router)

# AG-UI endpoint for the orchestrator agent
orchestrator = create_orchestrator()
add_agent_framework_fastapi_endpoint(app, agent=orchestrator, path="/agent")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "manufacturing-intelligence"}
