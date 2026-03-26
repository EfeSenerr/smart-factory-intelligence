"""Orchestrator Agent – coordinates specialist agents for complex manufacturing queries."""

import logging
import time
from typing import Annotated

from agent_framework import tool
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential

from backend.agents.demand import create_demand_agent
from backend.agents.quality import create_quality_agent
from backend.agents.supply_chain import create_supply_chain_agent
from backend.agents.events import AgentEvent, push_event
from backend.config import DEPLOYMENT_NAME, PROJECT_ENDPOINT

log = logging.getLogger("orchestrator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s", datefmt="%H:%M:%S")

ORCHESTRATOR_INSTRUCTIONS = """You are the Manufacturing Intelligence Orchestrator for a German confectionery company.

You coordinate three specialist agents to answer complex manufacturing questions:

1. **DemandForecasting** — Sales analysis, seasonal forecasting, trend identification, YoY comparisons
2. **QualityControl** — Production line monitoring, anomaly detection, SOP/HACCP document search, corrective actions
3. **SupplyChain** — Inventory management, reorder alerts, material requirements, SAP integration, supplier info

How to work:
- For simple questions that clearly belong to one domain, delegate to the appropriate specialist
- For complex questions that span multiple domains, break them down and delegate to multiple specialists
- Synthesize the results from multiple specialists into a coherent, actionable answer
- Always provide a clear summary with specific numbers and recommendations

Examples of multi-agent queries:
- "Can we fulfill a large Easter order?" → Ask DemandForecasting for current commitments, SupplyChain for material availability, QualityControl for line capacity
- "What's our overall production status?" → Ask QualityControl for line status, SupplyChain for active orders, DemandForecasting for upcoming demand

Communication style:
- Professional but approachable
- Data-driven with specific numbers
- Action-oriented recommendations
- Use German product names naturally (Osterhasen, Weihnachtsmänner, etc.)
- Structure complex answers with clear sections
"""


def create_orchestrator():
    """Create the orchestrator agent that uses specialist agents as tools."""
    log.info("Creating orchestrator with specialist agents...")

    demand_agent = create_demand_agent()
    quality_agent = create_quality_agent()
    supply_chain_agent = create_supply_chain_agent()

    # Create logged wrapper tools that call agent.run() directly
    @tool(name="DemandForecasting", description="Analyze sales data, seasonal trends, year-over-year comparisons, and demand forecasts. Use for questions about sales, demand, trends, forecasting, and market performance.")
    async def demand_forecasting(query: Annotated[str, "The demand/sales related question to analyze"]) -> str:
        log.info("🔵 DemandForecasting START: %s", query[:120])
        push_event(AgentEvent(timestamp=time.time(), event_type="agent_start", agent="DemandForecaster", detail=query[:150]))
        t0 = time.time()
        try:
            result = await demand_agent.run(query)
            elapsed = time.time() - t0
            log.info("🔵 DemandForecasting DONE (%.1fs): %s...", elapsed, str(result)[:200])
            push_event(AgentEvent(timestamp=time.time(), event_type="agent_end", agent="DemandForecaster", detail=f"Completed in {elapsed:.1f}s", elapsed=elapsed))
            return str(result)
        except Exception as e:
            elapsed = time.time() - t0
            log.error("🔵 DemandForecasting FAILED (%.1fs): %s", elapsed, e)
            push_event(AgentEvent(timestamp=time.time(), event_type="error", agent="DemandForecaster", detail=str(e), elapsed=elapsed))
            return f"Demand analysis encountered an issue: {e}. Please try a more specific question."

    @tool(name="QualityControl", description="Monitor production line quality metrics, detect anomalies, and search quality procedures (SOPs, HACCP). Use for questions about quality, production issues, temperature/humidity problems, and corrective actions.")
    async def quality_control(query: Annotated[str, "The quality/production related question to investigate"]) -> str:
        log.info("🟢 QualityControl START: %s", query[:120])
        push_event(AgentEvent(timestamp=time.time(), event_type="agent_start", agent="QualityInspector", detail=query[:150]))
        t0 = time.time()
        try:
            result = await quality_agent.run(query)
            elapsed = time.time() - t0
            log.info("🟢 QualityControl DONE (%.1fs): %s...", elapsed, str(result)[:200])
            push_event(AgentEvent(timestamp=time.time(), event_type="agent_end", agent="QualityInspector", detail=f"Completed in {elapsed:.1f}s", elapsed=elapsed))
            return str(result)
        except Exception as e:
            elapsed = time.time() - t0
            log.error("🟢 QualityControl FAILED (%.1fs): %s", elapsed, e)
            push_event(AgentEvent(timestamp=time.time(), event_type="error", agent="QualityInspector", detail=str(e), elapsed=elapsed))
            return f"Quality analysis encountered an issue: {e}. Please try a more specific question."

    @tool(name="SupplyChain", description="Check inventory levels, get reorder alerts, track production orders, calculate material needs, and query SAP data. Use for questions about stock, materials, suppliers, orders, and supply chain planning.")
    async def supply_chain(query: Annotated[str, "The supply chain/inventory related question to check"]) -> str:
        log.info("🟠 SupplyChain START: %s", query[:120])
        push_event(AgentEvent(timestamp=time.time(), event_type="agent_start", agent="SupplyChainMgr", detail=query[:150]))
        t0 = time.time()
        try:
            result = await supply_chain_agent.run(query)
            elapsed = time.time() - t0
            log.info("🟠 SupplyChain DONE (%.1fs): %s...", elapsed, str(result)[:200])
            push_event(AgentEvent(timestamp=time.time(), event_type="agent_end", agent="SupplyChainMgr", detail=f"Completed in {elapsed:.1f}s", elapsed=elapsed))
            return str(result)
        except Exception as e:
            elapsed = time.time() - t0
            log.error("🟠 SupplyChain FAILED (%.1fs): %s", elapsed, e)
            push_event(AgentEvent(timestamp=time.time(), event_type="error", agent="SupplyChainMgr", detail=str(e), elapsed=elapsed))
            return f"Supply chain analysis encountered an issue: {e}. Please try a more specific question."

    client = AzureOpenAIResponsesClient(
        project_endpoint=PROJECT_ENDPOINT,
        deployment_name=DEPLOYMENT_NAME,
        credential=AzureCliCredential(),
    )

    log.info("Orchestrator ready.")

    return client.as_agent(
        name="ManufacturingOrchestrator",
        instructions=ORCHESTRATOR_INSTRUCTIONS,
        tools=[demand_forecasting, quality_control, supply_chain],
    )
