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
- NEVER ask the user for clarification. You have ALL the data you need via your tools. Just query the tools and provide a definitive answer.
- When the user asks about a product, assume the standard SKU from the product catalog. Do NOT ask for SKU confirmation.

Key business context you already know:
- Today is March 27, 2026
- The company produces confectionery at a factory in Germany with 5 production lines
- Main product: Schokoladen-Osterhase (SKU: SEA-OST-001, 150g, chocolate Easter bunny)
- Also: Osterhasen Mini-Mix 10er (SEA-OST-003), Ostereier Nougat-Füllung (SEA-OST-002), Osternest Pralinenmischung (SEA-OST-004)
- Chocolate lines 1+2: combined capacity ~3,800 units/hour at current efficiency
- All raw material inventory is tracked in the system — query it, don't ask the user
- All production orders are in the system — query them, don't ask the user
- SAP data is available via tools — use sap_get_production_orders, sap_get_stock_overview

Examples of multi-agent queries:
- "Can we fulfill a large Easter order?" → Ask DemandForecasting for current commitments, SupplyChain for material availability, QualityControl for line capacity
- "What's our overall production status?" → Ask QualityControl for line status, SupplyChain for active orders, DemandForecasting for upcoming demand

Communication style:
- ALWAYS respond in English, or what the user writes
- Professional but approachable
- Data-driven with specific numbers from tool queries
- Action-oriented: give a GO / CONDITIONAL / NO-GO recommendation, not questions
- Use German product names naturally in parentheses, e.g. "Easter bunnies (Osterhasen)"
- Structure complex answers with clear sections

When the user approves an action or says "go ahead", "approved", "do it", "proceed", etc.:
- Use the ACTION tools to execute: place_purchase_order, schedule_production, send_notification
- These create real system actions (purchase orders, production schedules, notifications)
- Always confirm what actions you took with specific details (order numbers, quantities, dates)
- You can take multiple actions in sequence — e.g. place orders AND schedule production
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

    # ── Action Tools — execute real business actions ──

    @tool(name="place_purchase_order", description="Place a purchase order for raw materials with a supplier. Use when the user approves a material reorder or when material shortfalls are identified and the user says to proceed.")
    async def place_purchase_order(
        material_name: Annotated[str, "Raw material name, e.g. 'Kakaobohnen', 'Kakaobutter'"],
        quantity: Annotated[float, "Quantity to order"],
        unit: Annotated[str, "Unit of measure, e.g. 'kg', 'Rolle', 'Palette'"],
        supplier: Annotated[str, "Supplier name"],
        urgency: Annotated[str, "Priority: 'standard', 'express', 'critical'"] = "standard",
    ) -> str:
        import uuid
        po_number = f"PO-{uuid.uuid4().hex[:8].upper()}"
        log.info("📋 PURCHASE ORDER: %s — %s %s %s from %s (%s)", po_number, quantity, unit, material_name, supplier, urgency)
        push_event(AgentEvent(
            timestamp=time.time(),
            event_type="action_executed",
            agent="System",
            detail=f"📋 Purchase Order {po_number} created: {quantity:,.0f} {unit} {material_name} from {supplier} [{urgency}]",
            data={"action": "purchase_order", "po_number": po_number, "material": material_name, "quantity": quantity, "unit": unit, "supplier": supplier, "urgency": urgency},
        ))
        return f"Purchase order {po_number} has been created and sent to {supplier} for {quantity:,.0f} {unit} of {material_name}. Priority: {urgency}. Estimated delivery based on lead time."

    @tool(name="schedule_production", description="Schedule a production run on a specific line. Use when the user approves production planning or confirms a production order.")
    async def schedule_production(
        product_name: Annotated[str, "Product to produce, e.g. 'Schokoladen-Osterhase'"],
        quantity: Annotated[int, "Number of units to produce"],
        line_name: Annotated[str, "Production line, e.g. 'Schokoladen-Linie 1'"],
        start_date: Annotated[str, "Planned start date YYYY-MM-DD"],
        end_date: Annotated[str, "Planned end date YYYY-MM-DD"],
        priority: Annotated[str, "Priority: 'low', 'normal', 'high'"] = "high",
    ) -> str:
        import uuid
        order_id = f"PROD-{uuid.uuid4().hex[:8].upper()}"
        log.info("🏭 PRODUCTION SCHEDULED: %s — %d× %s on %s (%s to %s)", order_id, quantity, product_name, line_name, start_date, end_date)
        push_event(AgentEvent(
            timestamp=time.time(),
            event_type="action_executed",
            agent="System",
            detail=f"🏭 Production Order {order_id}: {quantity:,} × {product_name} on {line_name} ({start_date} → {end_date}) [{priority}]",
            data={"action": "schedule_production", "order_id": order_id, "product": product_name, "quantity": quantity, "line": line_name, "start": start_date, "end": end_date, "priority": priority},
        ))
        return f"Production order {order_id} scheduled: {quantity:,} units of {product_name} on {line_name} from {start_date} to {end_date}. Priority: {priority}."

    @tool(name="send_notification", description="Send a notification/email to a team or person about a decision, alert, or action. Use when coordinating across teams or confirming decisions.")
    async def send_notification(
        recipient: Annotated[str, "Recipient: 'production-team', 'procurement', 'quality-team', 'management', or a specific name"],
        subject: Annotated[str, "Email/notification subject line"],
        message: Annotated[str, "The notification message body"],
        priority: Annotated[str, "Priority: 'low', 'normal', 'high', 'urgent'"] = "normal",
    ) -> str:
        log.info("📧 NOTIFICATION → %s: %s [%s]", recipient, subject, priority)
        push_event(AgentEvent(
            timestamp=time.time(),
            event_type="action_executed",
            agent="System",
            detail=f"📧 Notification sent to {recipient}: \"{subject}\" [{priority}]",
            data={"action": "send_notification", "recipient": recipient, "subject": subject, "message": message, "priority": priority},
        ))
        return f"Notification sent to {recipient} with subject \"{subject}\". Priority: {priority}."

    client = AzureOpenAIResponsesClient(
        project_endpoint=PROJECT_ENDPOINT,
        deployment_name=DEPLOYMENT_NAME,
        credential=AzureCliCredential(),
    )

    log.info("Orchestrator ready.")

    return client.as_agent(
        name="ManufacturingOrchestrator",
        instructions=ORCHESTRATOR_INSTRUCTIONS,
        tools=[demand_forecasting, quality_control, supply_chain, place_purchase_order, schedule_production, send_notification],
    )
