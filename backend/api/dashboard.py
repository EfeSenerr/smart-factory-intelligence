"""Dashboard and data API endpoints."""

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.config import DB_PATH, DEPLOYMENT_NAME, EMBEDDING_DEPLOYMENT_NAME, MINI_DEPLOYMENT_NAME
from backend.agents.events import get_recent_events, subscribe, unsubscribe

import aiosqlite

router = APIRouter(prefix="/api")


async def _query_db(sql: str, params: tuple = ()) -> list[dict]:
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/dashboard")
async def get_dashboard():
    """Get KPI data for the dashboard."""
    # Today's production
    active_orders = await _query_db("""
        SELECT COUNT(*) as count, SUM(quantity) as total_qty
        FROM production_orders WHERE status = 'in_progress'
    """)

    # Quality score (% of OK readings in last 3 days)
    quality = await _query_db("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) as ok_count
        FROM quality_metrics
        WHERE timestamp >= datetime('2026-03-23')
    """)

    # Inventory alerts
    inventory_alerts = await _query_db("""
        SELECT COUNT(*) as count
        FROM raw_materials
        WHERE current_stock <= reorder_point * 1.5
    """)

    # Revenue this month
    revenue = await _query_db("""
        SELECT ROUND(SUM(revenue), 2) as total
        FROM sales_history
        WHERE date LIKE '2026-03%'
    """)

    # Revenue last month for comparison
    revenue_last = await _query_db("""
        SELECT ROUND(SUM(revenue), 2) as total
        FROM sales_history
        WHERE date LIKE '2026-02%'
    """)

    q = quality[0] if quality else {"total": 1, "ok_count": 1}
    quality_score = round((q["ok_count"] / max(q["total"], 1)) * 100, 1)

    return {
        "kpis": {
            "active_orders": active_orders[0]["count"] if active_orders else 0,
            "units_in_production": active_orders[0]["total_qty"] if active_orders else 0,
            "quality_score": quality_score,
            "inventory_alerts": inventory_alerts[0]["count"] if inventory_alerts else 0,
            "revenue_this_month": revenue[0]["total"] if revenue and revenue[0]["total"] else 0,
            "revenue_last_month": revenue_last[0]["total"] if revenue_last and revenue_last[0]["total"] else 0,
        }
    }


@router.get("/dashboard/sales-trend")
async def get_sales_trend():
    """Get monthly sales trend for charts."""
    rows = await _query_db("""
        SELECT strftime('%Y-%m', date) as month,
               ROUND(SUM(revenue), 2) as revenue,
               SUM(quantity) as quantity
        FROM sales_history
        GROUP BY month
        ORDER BY month
    """)
    return {"sales_trend": rows}


@router.get("/dashboard/quality-overview")
async def get_quality_overview():
    """Get quality metrics overview for charts."""
    rows = await _query_db("""
        SELECT pl.name as line_name, pl.type,
               ROUND(AVG(qm.temperature_c), 1) as avg_temp,
               ROUND(AVG(qm.humidity_pct), 1) as avg_humidity,
               ROUND(AVG(qm.weight_deviation_pct), 2) as avg_weight_dev,
               ROUND(AVG(qm.defect_rate_pct), 2) as avg_defect_rate,
               SUM(CASE WHEN qm.status = 'warning' THEN 1 ELSE 0 END) as warnings,
               SUM(CASE WHEN qm.status = 'critical' THEN 1 ELSE 0 END) as criticals,
               COUNT(*) as total_readings
        FROM quality_metrics qm
        JOIN production_lines pl ON qm.line_id = pl.id
        WHERE qm.timestamp >= datetime('2026-03-23')
        GROUP BY pl.id
    """)
    return {"quality_overview": rows}


@router.get("/dashboard/inventory-levels")
async def get_inventory_levels():
    """Get current inventory levels for charts."""
    rows = await _query_db("""
        SELECT rm.name, rm.current_stock, rm.reorder_point, rm.unit,
               ROUND(rm.current_stock * 1.0 / rm.reorder_point, 2) as stock_ratio
        FROM raw_materials rm
        ORDER BY stock_ratio ASC
    """)
    return {"inventory_levels": rows}


@router.get("/dashboard/production-orders")
async def get_production_orders():
    """Get current production orders."""
    rows = await _query_db("""
        SELECT po.id, p.name as product, pl.name as line, po.quantity,
               po.start_date, po.end_date, po.status, po.priority
        FROM production_orders po
        JOIN products p ON po.product_id = p.id
        JOIN production_lines pl ON po.line_id = pl.id
        ORDER BY
            CASE po.status
                WHEN 'in_progress' THEN 1
                WHEN 'planned' THEN 2
                WHEN 'completed' THEN 3
            END,
            CASE po.priority
                WHEN 'high' THEN 1
                WHEN 'normal' THEN 2
                WHEN 'low' THEN 3
            END
    """)
    return {"production_orders": rows}


@router.get("/tools/status")
async def get_tools_status():
    """Get connected tools/MCP server status for the tools panel."""
    return {
        "connected_tools": [
            {
                "id": "sap-odata",
                "name": "SAP S/4HANA OData",
                "type": "MCP Server",
                "status": "connected",
                "description": "Production orders (PP), Material master (MM), Stock overview",
                "icon": "database",
                "tools_count": 3,
                "last_sync": "2026-03-26T08:00:00Z",
            },
            {
                "id": "quality-docs",
                "name": "Quality Documents (HACCP/SOP)",
                "type": "RAG / Vector Search",
                "status": "connected",
                "description": "6 embedded quality documents via text-embedding-large",
                "icon": "file-search",
                "tools_count": 1,
                "last_sync": "2026-03-26T07:30:00Z",
            },
            {
                "id": "production-sensors",
                "name": "Production Line Sensors",
                "type": "Function Tool",
                "status": "connected",
                "description": "Real-time quality metrics from 5 production lines",
                "icon": "activity",
                "tools_count": 3,
                "last_sync": "2026-03-26T09:15:00Z",
            },
            {
                "id": "inventory",
                "name": "Inventory Management",
                "type": "Function Tool",
                "status": "connected",
                "description": "Stock levels, reorder alerts, supplier data for 15 materials",
                "icon": "package",
                "tools_count": 4,
                "last_sync": "2026-03-26T09:00:00Z",
            },
            {
                "id": "foundry",
                "name": "Azure AI Foundry",
                "type": "Model Provider",
                "status": "connected",
                "description": f"Models: {DEPLOYMENT_NAME}, {MINI_DEPLOYMENT_NAME}, {EMBEDDING_DEPLOYMENT_NAME}",
                "icon": "brain",
                "tools_count": 3,
                "last_sync": "2026-03-26T09:20:00Z",
            },
        ]
    }


@router.get("/events")
async def get_events():
    """Get recent agent activity events."""
    return {"events": get_recent_events(50)}


@router.get("/events/stream")
async def stream_events():
    """SSE stream of agent activity events in real-time."""
    q = await subscribe()

    async def event_generator():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield f"data: {json.dumps(event.to_dict(), default=str)}\n\n"
                except asyncio.TimeoutError:
                    yield f": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            unsubscribe(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
