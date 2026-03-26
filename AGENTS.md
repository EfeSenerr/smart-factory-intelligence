# Smart Factory Intelligence — Development Guidelines

Last updated: 2026-03-26

## Active Technologies

- Python 3.12 (backend): FastAPI, Microsoft Agent Framework (`agent-framework`), AG-UI protocol (`agent-framework-ag-ui`), aiosqlite
- TypeScript 5.9 (frontend): Next.js 15, React 19, CopilotKit, shadcn/ui, Recharts, Lucide icons
- Azure AI Foundry: GPT-5 (or GPT-4o/4.1), GPT-5-mini, text-embedding-large

## Project Structure

```
backend/
  main.py              — FastAPI app, AG-UI endpoint, CORS, router registration
  config.py            — Foundry endpoint, model deployments, env vars
  agents/
    orchestrator.py    — Orchestrator: wraps specialists as @tool, calls via agent.run()
    demand.py          — Demand forecasting agent (GPT-5)
    quality.py         — Quality control agent + RAG (GPT-5)
    supply_chain.py    — Supply chain agent (GPT-5-mini)
    events.py          — Global activity event bus (push_event, subscribe, SSE)
  tools/
    sales_tools.py     — Sales queries: history, monthly summary, YoY, forecasts
    quality_tools.py   — Quality metrics, anomaly detection, SOP/HACCP search
    supply_tools.py    — Inventory check, reorder alerts, material needs, suppliers
    sap_mcp_tools.py   — Mock SAP S/4HANA OData (production orders, material master, stock)
    tracking.py        — @tracked_tool decorator: pushes tool-call events to activity feed
  api/
    dashboard.py       — KPIs, charts, quality overview, inventory, tools status, events SSE
    pipeline.py        — HITL pipeline: Easter Rush multi-step analysis with approve/reject
  database/
    schema.sql         — SQLite schema (8 tables)
    seed.py            — Dummy data: 27 products, 21K+ sales, 5 lines, 15 materials, 6 SOPs
    connection.py      — Async DB connection utility

frontend/
  src/app/
    layout.tsx         — Root layout with CopilotKit provider (runtimeUrl=/api/copilotkit)
    page.tsx           — Tab navigation: Dashboard | Agent Hub
    api/copilotkit/    — CopilotRuntime proxy route (HttpAgent → backend /agent)
  src/components/
    dashboard/         — KPI cards, revenue+volume chart, inventory chart, quality monitor, data overview, production orders table
    chat/              — CopilotKit chat integration
    pipeline/          — HITL pipeline analysis (SSE progress, approve/reject per step)
    agent-hub/         — Agent Hub: orchestration viz, AI chat, live activity feed
    tools-panel/       — Connected Tools & MCP Servers visualization
  src/lib/
    api.ts             — Dashboard API client with TypeScript interfaces
```

## Commands

```bash
# Backend
python backend/database/seed.py                    # Seed the database
uvicorn backend.main:app --reload --port 8000      # Run backend (from project root)

# Frontend
cd frontend && npm install                         # Install dependencies
cd frontend && npm run dev                         # Run frontend dev server (port 3000)
```

## Key Patterns

### Agent Tool Registration
Specialist agents are created with `client.as_agent(name, instructions, tools)`. The orchestrator wraps them with `@tool` decorators that call `await agent.run(query)` — NOT `.as_tool()` (that API has `kwargs` issues). Error handling is in each wrapper.

### Tool Tracking
All tool functions in `backend/tools/` use `@tracked_tool("AgentLabel")` decorator from `tracking.py`. This pushes `tool_call` and `tool_result` events to the global event bus, streamed to the Agent Hub's activity feed via SSE.

### CopilotKit ↔ AG-UI Bridge
CopilotKit requires a `CopilotRuntime` proxy in Next.js (`/api/copilotkit/route.ts`). This uses `HttpAgent` from `@ag-ui/client` pointing at `http://localhost:8000/agent`. The frontend CopilotKit provider points at `/api/copilotkit`, NOT directly at the backend.

### HITL Pipeline
`/api/pipeline/easter-rush` runs 4 sequential agent steps (Demand → Supply → Quality → Summary), streaming SSE events. Each step can be approved/rejected via POST endpoints.

## Code Style

- Python: async/await throughout, type annotations, Google-style docstrings
- TypeScript: "use client" components, hooks for state, shadcn/ui components
- No authentication (demo only)
- SQLite for zero-infrastructure data storage

## Recent Changes

- 2026-03-26: Initial project scaffold — full backend (agents, tools, API) and frontend (dashboard, chat, tools panel)


