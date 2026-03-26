"""Human-in-the-Loop pipeline API — runs multi-step agent analysis with SSE progress streaming."""

import asyncio
import json
import logging
import time
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.agents.demand import create_demand_agent
from backend.agents.quality import create_quality_agent
from backend.agents.supply_chain import create_supply_chain_agent

log = logging.getLogger("pipeline")

router = APIRouter(prefix="/api/pipeline")

# In-memory pipeline state (sufficient for demo)
_pipelines: dict[str, dict] = {}


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


async def _run_agent_step(agent, query: str) -> str:
    """Run a single agent and return the text result."""
    result = await agent.run(query)
    return str(result)


async def _easter_rush_pipeline(pipeline_id: str, quantity: int = 200_000) -> AsyncGenerator[str, None]:
    """Run the Easter Rush analysis as a multi-step pipeline, streaming progress via SSE."""

    _pipelines[pipeline_id] = {"status": "running", "steps": {}, "started": time.time()}

    yield _sse("pipeline_start", {
        "id": pipeline_id,
        "title": f"Easter Production Feasibility — {quantity:,} Osterhasen",
        "steps": ["demand", "supply", "quality", "summary"],
    })

    # ── Step 1: Demand Analysis ──
    yield _sse("step_start", {"step": "demand", "label": "Demand Forecasting", "description": "Checking current Easter commitments and seasonal demand..."})

    try:
        demand_agent = create_demand_agent()
        t0 = time.time()
        demand_result = await _run_agent_step(
            demand_agent,
            f"Analyze our current Easter 2026 demand situation. We're considering a large order of {quantity:,} Osterhasen (Easter bunnies) by April 1st. "
            f"What are our current Easter commitments? What does the seasonal demand forecast look like? "
            f"Check sales history for Osterhasen and Easter products."
        )
        elapsed = time.time() - t0
        log.info("Pipeline %s step demand done in %.1fs", pipeline_id, elapsed)
        _pipelines[pipeline_id]["steps"]["demand"] = {"result": demand_result, "elapsed": elapsed}

        yield _sse("step_complete", {
            "step": "demand",
            "elapsed": round(elapsed, 1),
            "result": demand_result,
            "requires_approval": False,
        })
    except Exception as e:
        log.error("Pipeline %s step demand failed: %s", pipeline_id, e)
        yield _sse("step_error", {"step": "demand", "error": str(e)})
        return

    # ── Step 2: Supply Chain / Material Check ──
    yield _sse("step_start", {"step": "supply", "label": "Supply Chain Analysis", "description": "Checking raw material availability, stock levels, and supplier lead times..."})

    try:
        supply_agent = create_supply_chain_agent()
        t0 = time.time()
        supply_result = await _run_agent_step(
            supply_agent,
            f"We need to produce {quantity:,} Osterhasen (chocolate Easter bunnies, ~150g each). "
            f"Calculate the raw material requirements. Check current inventory levels for all needed materials "
            f"(especially Kakaobohnen, Kakaobutter, Zucker, Milchpulver, Verpackung). "
            f"Are there any materials below reorder point? What are the supplier lead times for critical materials? "
            f"Also check SAP for any conflicting production orders."
        )
        elapsed = time.time() - t0
        log.info("Pipeline %s step supply done in %.1fs", pipeline_id, elapsed)
        _pipelines[pipeline_id]["steps"]["supply"] = {"result": supply_result, "elapsed": elapsed}

        yield _sse("step_complete", {
            "step": "supply",
            "elapsed": round(elapsed, 1),
            "result": supply_result,
            "requires_approval": True,
            "approval_question": "Should we proceed with material reorders for the identified shortfalls?",
        })
    except Exception as e:
        log.error("Pipeline %s step supply failed: %s", pipeline_id, e)
        yield _sse("step_error", {"step": "supply", "error": str(e)})
        return

    # ── Step 3: Quality / Line Capacity ──
    yield _sse("step_start", {"step": "quality", "label": "Quality & Capacity Check", "description": "Checking production line status, capacity, and any quality issues..."})

    try:
        quality_agent = create_quality_agent()
        t0 = time.time()
        quality_result = await _run_agent_step(
            quality_agent,
            f"We need to produce {quantity:,} Osterhasen on our chocolate lines. "
            f"Check the current status of all production lines, especially Schokoladen-Linie 1 and 2. "
            f"Are there any quality anomalies or issues? What is the current capacity and efficiency? "
            f"Based on line capacity, how many days would it take to produce {quantity:,} units? "
            f"Check for any relevant SOPs about large chocolate production runs."
        )
        elapsed = time.time() - t0
        log.info("Pipeline %s step quality done in %.1fs", pipeline_id, elapsed)
        _pipelines[pipeline_id]["steps"]["quality"] = {"result": quality_result, "elapsed": elapsed}

        yield _sse("step_complete", {
            "step": "quality",
            "elapsed": round(elapsed, 1),
            "result": quality_result,
            "requires_approval": True,
            "approval_question": "Should we schedule the production run on the identified lines?",
        })
    except Exception as e:
        log.error("Pipeline %s step quality failed: %s", pipeline_id, e)
        yield _sse("step_error", {"step": "quality", "error": str(e)})
        return

    # ── Step 4: Summary ──
    yield _sse("step_start", {"step": "summary", "label": "Executive Summary", "description": "Synthesizing findings from all agents..."})

    demand_data = _pipelines[pipeline_id]["steps"].get("demand", {}).get("result", "")
    supply_data = _pipelines[pipeline_id]["steps"].get("supply", {}).get("result", "")
    quality_data = _pipelines[pipeline_id]["steps"].get("quality", {}).get("result", "")

    from backend.agents.orchestrator import create_orchestrator
    summary_agent_client = __import__("agent_framework.azure", fromlist=["AzureOpenAIResponsesClient"]).AzureOpenAIResponsesClient(
        project_endpoint=__import__("backend.config", fromlist=["PROJECT_ENDPOINT"]).PROJECT_ENDPOINT,
        deployment_name=__import__("backend.config", fromlist=["DEPLOYMENT_NAME"]).DEPLOYMENT_NAME,
        credential=__import__("azure.identity", fromlist=["AzureCliCredential"]).AzureCliCredential(),
    )
    summary_agent = summary_agent_client.as_agent(
        name="SummaryAgent",
        instructions="You synthesize analysis results into a clear executive summary with a GO/NO-GO recommendation. Be concise, use bullet points, and highlight key risks.",
    )

    try:
        t0 = time.time()
        summary_result = await _run_agent_step(
            summary_agent,
            f"Provide an executive summary and GO/NO-GO recommendation for producing {quantity:,} Osterhasen by April 1st, 2026.\n\n"
            f"## Demand Analysis\n{demand_data}\n\n"
            f"## Supply Chain Analysis\n{supply_data}\n\n"
            f"## Quality & Capacity Analysis\n{quality_data}\n\n"
            f"Provide: 1) Overall feasibility assessment 2) Key risks 3) Required actions 4) Timeline estimate 5) GO/NO-GO recommendation"
        )
        elapsed = time.time() - t0
        log.info("Pipeline %s step summary done in %.1fs", pipeline_id, elapsed)
        _pipelines[pipeline_id]["steps"]["summary"] = {"result": summary_result, "elapsed": elapsed}
        _pipelines[pipeline_id]["status"] = "complete"

        total_elapsed = time.time() - _pipelines[pipeline_id]["started"]
        yield _sse("step_complete", {
            "step": "summary",
            "elapsed": round(elapsed, 1),
            "result": summary_result,
            "requires_approval": True,
            "approval_question": "Do you approve the production plan and authorize execution?",
        })

        yield _sse("pipeline_complete", {
            "id": pipeline_id,
            "total_elapsed": round(total_elapsed, 1),
            "status": "complete",
        })

    except Exception as e:
        log.error("Pipeline %s step summary failed: %s", pipeline_id, e)
        yield _sse("step_error", {"step": "summary", "error": str(e)})


@router.get("/easter-rush")
async def run_easter_rush_pipeline(quantity: int = 200_000):
    """Launch the Easter Rush analysis pipeline. Returns SSE stream of progress events."""
    pipeline_id = str(uuid.uuid4())[:8]
    log.info("Starting Easter Rush pipeline %s for %d units", pipeline_id, quantity)

    return StreamingResponse(
        _easter_rush_pipeline(pipeline_id, quantity),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/approve/{pipeline_id}/{step}")
async def approve_step(pipeline_id: str, step: str):
    """Record human approval for a pipeline step."""
    if pipeline_id in _pipelines:
        if step in _pipelines[pipeline_id].get("steps", {}):
            _pipelines[pipeline_id]["steps"][step]["approved"] = True
            log.info("Pipeline %s step %s APPROVED", pipeline_id, step)
            return {"status": "approved", "pipeline_id": pipeline_id, "step": step}
    return {"status": "not_found"}


@router.post("/reject/{pipeline_id}/{step}")
async def reject_step(pipeline_id: str, step: str, reason: str = ""):
    """Record human rejection for a pipeline step."""
    if pipeline_id in _pipelines:
        if step in _pipelines[pipeline_id].get("steps", {}):
            _pipelines[pipeline_id]["steps"][step]["approved"] = False
            _pipelines[pipeline_id]["steps"][step]["rejection_reason"] = reason
            log.info("Pipeline %s step %s REJECTED: %s", pipeline_id, step, reason)
            return {"status": "rejected", "pipeline_id": pipeline_id, "step": step}
    return {"status": "not_found"}
