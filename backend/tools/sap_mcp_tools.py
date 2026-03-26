"""Mock SAP OData MCP tools – simulates SAP S/4HANA integration."""

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
async def sap_get_production_orders(
    status: Annotated[str | None, Field(description="SAP order status: CRTD (Created/Planned), REL (Released/In Progress), TECO (Completed). Leave empty for all.")] = None,
) -> str:
    """[SAP S/4HANA] Query production orders from SAP PP module via OData. Returns order details including material, quantity, and scheduling."""
    status_map = {"CRTD": "planned", "REL": "in_progress", "TECO": "completed"}

    sql = """
        SELECT po.id as sap_order_number, p.name as material_description, p.sku as material_number,
               po.quantity as order_quantity, po.start_date as basic_start_date,
               po.end_date as basic_end_date, po.status, po.priority,
               pl.name as work_center
        FROM production_orders po
        JOIN products p ON po.product_id = p.id
        JOIN production_lines pl ON po.line_id = pl.id
    """
    params: list = []
    if status and status in status_map:
        sql += " WHERE po.status = ?"
        params.append(status_map[status])
    sql += " ORDER BY po.start_date"

    rows = await _query_db(sql, tuple(params))

    # Transform to SAP-like field names
    sap_orders = []
    for r in rows:
        sap_status = {v: k for k, v in status_map.items()}.get(r["status"], r["status"])
        sap_orders.append({
            "Aufnr": f"000{1000000 + r['sap_order_number']}",  # SAP order number format
            "Matnr": r["material_number"],
            "Maktx": r["material_description"],
            "Gamng": r["order_quantity"],
            "Gstrp": r["basic_start_date"],
            "Gltrp": r["basic_end_date"],
            "Status": sap_status,
            "Priok": r["priority"],
            "Arbpl": r["work_center"],
        })

    return json.dumps({
        "odata_context": "SAP S/4HANA PP - Production Orders (API_PRODUCTION_ORDER_2_SRV)",
        "results": sap_orders,
        "count": len(sap_orders),
    }, default=str)


@tracked_tool("SupplyChainMgr")
async def sap_get_material_master(
    material_name: Annotated[str | None, Field(description="Material name to search for. Leave empty for all.")] = None,
) -> str:
    """[SAP S/4HANA] Query material master data from SAP MM module via OData. Returns material details, stock info, and pricing."""
    sql = """
        SELECT p.id, p.sku as material_number, p.name as material_description,
               p.category as material_group, p.unit_weight_g, p.shelf_life_days,
               p.unit_cost as standard_price, p.unit_price as sales_price
        FROM products p
    """
    params: list = []
    if material_name:
        sql += " WHERE p.name LIKE ?"
        params.append(f"%{material_name}%")

    rows = await _query_db(sql, tuple(params))

    sap_materials = []
    for r in rows:
        sap_materials.append({
            "Matnr": r["material_number"],
            "Maktx": r["material_description"],
            "Matkl": r["material_group"],
            "Brgew": r["unit_weight_g"],
            "Gewei": "G",
            "Mhdhb": r["shelf_life_days"],
            "Stprs": r["standard_price"],
            "Verpr": r["sales_price"],
            "Werks": "1000",  # Plant
            "Lgort": "0001",  # Storage location
        })

    return json.dumps({
        "odata_context": "SAP S/4HANA MM - Material Master (API_PRODUCT_SRV)",
        "results": sap_materials,
        "count": len(sap_materials),
    }, default=str)


@tracked_tool("SupplyChainMgr")
async def sap_get_stock_overview() -> str:
    """[SAP S/4HANA] Query warehouse stock overview from SAP MM module via OData. Returns current stock levels for raw materials."""
    rows = await _query_db("""
        SELECT rm.name as material_description, rm.unit as base_unit,
               rm.current_stock as unrestricted_stock, rm.reorder_point,
               rm.unit_cost as valuation_price,
               ROUND(rm.current_stock * rm.unit_cost, 2) as stock_value
        FROM raw_materials rm
        ORDER BY rm.name
    """)

    sap_stock = []
    for i, r in enumerate(rows):
        sap_stock.append({
            "Matnr": f"RM-{1000 + i}",
            "Maktx": r["material_description"],
            "Meins": r["base_unit"],
            "Labst": r["current_stock"],  # Unrestricted stock
            "Minbe": r["reorder_point"],
            "Verpr": r["valuation_price"],
            "Salk3": r["stock_value"],  # Total stock value
            "Werks": "1000",
            "Lgort": "0001",
        })

    total_value = sum(r["stock_value"] for r in rows)
    return json.dumps({
        "odata_context": "SAP S/4HANA MM - Stock Overview (API_MATERIAL_STOCK_SRV)",
        "results": sap_stock,
        "count": len(sap_stock),
        "total_stock_value_eur": round(total_value, 2),
    }, default=str)
