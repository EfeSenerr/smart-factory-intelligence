"""Supply chain and inventory management tools for the Supply Chain Agent."""

import json
from typing import Annotated

import aiosqlite
from pydantic import Field

from backend.config import DB_PATH
from backend.tools.tracking import tracked_tool


async def _query_db(sql: str, params: tuple = ()) -> list[dict]:
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@tracked_tool("SupplyChainMgr")
async def check_inventory(
    material_name: Annotated[str, Field(description="Raw material name or partial name (e.g. 'Kakao', 'Zucker', 'Milchpulver')")],
) -> str:
    """Check current inventory level for a raw material, including stock status and supplier info."""
    rows = await _query_db("""
        SELECT rm.*, s.name as supplier_name, s.reliability_score, s.country, s.contact_email
        FROM raw_materials rm
        JOIN suppliers s ON rm.supplier_id = s.id
        WHERE rm.name LIKE ?
    """, (f"%{material_name}%",))

    if not rows:
        return f"No material found matching '{material_name}'."

    results = []
    for r in rows:
        stock_ratio = r["current_stock"] / r["reorder_point"]
        if stock_ratio < 1.0:
            status = "CRITICAL — below reorder point!"
        elif stock_ratio < 1.5:
            status = "LOW — approaching reorder point"
        elif stock_ratio < 2.5:
            status = "OK"
        else:
            status = "GOOD — well stocked"

        results.append({
            "material": r["name"],
            "current_stock": r["current_stock"],
            "unit": r["unit"],
            "reorder_point": r["reorder_point"],
            "stock_status": status,
            "stock_ratio": round(stock_ratio, 2),
            "lead_time_days": r["lead_time_days"],
            "unit_cost": r["unit_cost"],
            "supplier": r["supplier_name"],
            "supplier_reliability": r["reliability_score"],
            "supplier_country": r["country"],
        })
    return json.dumps({"search": material_name, "materials": results}, default=str)


@tracked_tool("SupplyChainMgr")
async def get_reorder_alerts() -> str:
    """Get all raw materials that are at or below their reorder point — these need immediate attention."""
    rows = await _query_db("""
        SELECT rm.*, s.name as supplier_name, s.reliability_score, s.lead_time_days as supplier_lead_time, s.country
        FROM raw_materials rm
        JOIN suppliers s ON rm.supplier_id = s.id
        WHERE rm.current_stock <= rm.reorder_point * 1.5
        ORDER BY (rm.current_stock * 1.0 / rm.reorder_point) ASC
    """)

    if not rows:
        return "All materials are well stocked — no reorder alerts."

    alerts = []
    for r in rows:
        ratio = r["current_stock"] / r["reorder_point"]
        urgency = "CRITICAL" if ratio < 1.0 else "WARNING"
        alerts.append({
            "material": r["name"],
            "current_stock": f"{r['current_stock']} {r['unit']}",
            "reorder_point": f"{r['reorder_point']} {r['unit']}",
            "stock_ratio": round(ratio, 2),
            "urgency": urgency,
            "lead_time_days": r["lead_time_days"],
            "supplier": r["supplier_name"],
            "supplier_country": r["country"],
            "estimated_cost": round(r["reorder_point"] * r["unit_cost"], 2),
        })
    return json.dumps({"reorder_alerts": alerts, "total_alerts": len(alerts)}, default=str)


@tracked_tool("SupplyChainMgr")
async def get_production_orders_status(
    status_filter: Annotated[str | None, Field(description="Filter by status: planned, in_progress, completed. Leave empty for all.")] = None,
) -> str:
    """Get production orders with their current status, products, and line assignments."""
    sql = """
        SELECT po.*, p.name as product_name, p.category, pl.name as line_name
        FROM production_orders po
        JOIN products p ON po.product_id = p.id
        JOIN production_lines pl ON po.line_id = pl.id
    """
    params: list = []
    if status_filter:
        sql += " WHERE po.status = ?"
        params.append(status_filter)
    sql += " ORDER BY po.priority DESC, po.start_date ASC"

    rows = await _query_db(sql, tuple(params))
    return json.dumps({"production_orders": rows, "count": len(rows)}, default=str)


@tracked_tool("SupplyChainMgr")
async def calculate_material_needs(
    product_name: Annotated[str, Field(description="Product name (e.g. 'Osterhase', 'Praline')")],
    quantity: Annotated[int, Field(description="Number of units to produce")],
) -> str:
    """Estimate raw material needs for a production run of a given product and quantity."""
    # Simplified material requirements (in production, this would be a proper BOM)
    product_rows = await _query_db("SELECT * FROM products WHERE name LIKE ?", (f"%{product_name}%",))
    if not product_rows:
        return f"Product '{product_name}' not found."

    product = product_rows[0]
    weight_kg = (product["unit_weight_g"] * quantity) / 1000

    # Material requirements based on category (simplified BOM)
    requirements: dict[str, float] = {}
    if product["category"] in ("Schokolade", "Saisonware"):
        requirements = {
            "Kakaobohnen (Rohkakao)": weight_kg * 0.35,
            "Kristallzucker": weight_kg * 0.30,
            "Kakaobutter": weight_kg * 0.15,
            "Vollmilchpulver": weight_kg * 0.12,
            "Verpackungsfolie (Rolle)": quantity / 500,  # 500 units per roll
        }
    elif product["category"] == "Fruchtgummi":
        requirements = {
            "Kristallzucker": weight_kg * 0.45,
            "Gelatine (Blatt)": weight_kg * 0.08,
            "Fruchtkonzentrate Mix": weight_kg * 0.15,
            "Zitronensäure": weight_kg * 0.02,
            "Verpackungsfolie (Rolle)": quantity / 500,
        }
    elif product["category"] == "Marzipan":
        requirements = {
            "Marzipan-Rohmasse": weight_kg * 0.65,
            "Kristallzucker": weight_kg * 0.25,
            "Mandeln (geschält)": weight_kg * 0.40,
            "Verpackungsfolie (Rolle)": quantity / 400,
        }
    else:
        requirements = {
            "Kristallzucker": weight_kg * 0.20,
            "Verpackungsfolie (Rolle)": quantity / 300,
            "Kartonagen (Palette)": quantity / 200,
        }

    # Check current stock for each material
    material_status = []
    for material_name, needed in requirements.items():
        stock_rows = await _query_db(
            "SELECT * FROM raw_materials WHERE name LIKE ?",
            (f"%{material_name.split('(')[0].strip()}%",)
        )
        if stock_rows:
            stock = stock_rows[0]
            sufficient = stock["current_stock"] >= needed
            material_status.append({
                "material": material_name,
                "needed": round(needed, 1),
                "unit": stock["unit"],
                "current_stock": stock["current_stock"],
                "sufficient": sufficient,
                "shortfall": round(needed - stock["current_stock"], 1) if not sufficient else 0,
                "lead_time_days": stock["lead_time_days"],
            })

    all_sufficient = all(m["sufficient"] for m in material_status)
    return json.dumps({
        "product": product["name"],
        "quantity": quantity,
        "total_weight_kg": round(weight_kg, 1),
        "materials_needed": material_status,
        "all_materials_sufficient": all_sufficient,
        "recommendation": "All materials available — production can proceed." if all_sufficient else "Some materials insufficient — reorder required before production.",
    }, default=str)


@tracked_tool("SupplyChainMgr")
async def get_supplier_info(
    supplier_name: Annotated[str | None, Field(description="Supplier name to search for. Leave empty for all suppliers.")] = None,
) -> str:
    """Get supplier information including reliability scores and lead times."""
    if supplier_name:
        rows = await _query_db("SELECT * FROM suppliers WHERE name LIKE ?", (f"%{supplier_name}%",))
    else:
        rows = await _query_db("SELECT * FROM suppliers ORDER BY reliability_score DESC")
    return json.dumps({"suppliers": rows}, default=str)
