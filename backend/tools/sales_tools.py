"""Sales and demand forecasting tools for the Demand Agent."""

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


@tracked_tool("DemandForecaster")
async def query_sales_history(
    product_name: Annotated[str, Field(description="Product name or partial name to search for (e.g. 'Osterhase', 'Fruchtbärchen')")],
    start_date: Annotated[str, Field(description="Start date in YYYY-MM-DD format")] = "2024-04-01",
    end_date: Annotated[str, Field(description="End date in YYYY-MM-DD format")] = "2026-03-25",
    channel: Annotated[str | None, Field(description="Filter by channel: retail, wholesale, online. Leave empty for all.")] = None,
) -> str:
    """Query sales history for a product within a date range, optionally filtered by channel."""
    sql = """
        SELECT s.date, p.name as product, s.quantity, s.revenue, s.channel, s.region
        FROM sales_history s
        JOIN products p ON s.product_id = p.id
        WHERE p.name LIKE ?
        AND s.date BETWEEN ? AND ?
    """
    params: list = [f"%{product_name}%", start_date, end_date]
    if channel:
        sql += " AND s.channel = ?"
        params.append(channel)
    sql += " ORDER BY s.date DESC LIMIT 100"

    rows = await _query_db(sql, tuple(params))
    if not rows:
        return f"No sales data found for '{product_name}' between {start_date} and {end_date}."

    total_qty = sum(r["quantity"] for r in rows)
    total_rev = sum(r["revenue"] for r in rows)
    return json.dumps({
        "product_search": product_name,
        "period": f"{start_date} to {end_date}",
        "total_records_shown": len(rows),
        "total_quantity": total_qty,
        "total_revenue": round(total_rev, 2),
        "sample_records": rows[:20],
    }, default=str)


@tracked_tool("DemandForecaster")
async def get_sales_summary_by_month(
    product_name: Annotated[str, Field(description="Product name or partial name to search for")],
    year: Annotated[int, Field(description="Year to get monthly summary for (e.g. 2025)")] = 2025,
) -> str:
    """Get monthly sales summary for a product in a given year. Great for trend analysis."""
    rows = await _query_db("""
        SELECT strftime('%Y-%m', s.date) as month,
               SUM(s.quantity) as total_quantity,
               ROUND(SUM(s.revenue), 2) as total_revenue,
               COUNT(*) as num_transactions,
               GROUP_CONCAT(DISTINCT s.channel) as channels
        FROM sales_history s
        JOIN products p ON s.product_id = p.id
        WHERE p.name LIKE ?
        AND strftime('%Y', s.date) = ?
        GROUP BY month
        ORDER BY month
    """, (f"%{product_name}%", str(year)))

    if not rows:
        return f"No sales data found for '{product_name}' in {year}."
    return json.dumps({"product": product_name, "year": year, "monthly_summary": rows}, default=str)


@tracked_tool("DemandForecaster")
async def compare_year_over_year(
    product_name: Annotated[str, Field(description="Product name or partial name")],
    month_start: Annotated[int, Field(description="Start month (1-12)")] = 1,
    month_end: Annotated[int, Field(description="End month (1-12)")] = 12,
) -> str:
    """Compare year-over-year sales for a product across the same months."""
    rows = await _query_db("""
        SELECT strftime('%Y', s.date) as year,
               strftime('%m', s.date) as month,
               SUM(s.quantity) as total_quantity,
               ROUND(SUM(s.revenue), 2) as total_revenue
        FROM sales_history s
        JOIN products p ON s.product_id = p.id
        WHERE p.name LIKE ?
        AND CAST(strftime('%m', s.date) AS INTEGER) BETWEEN ? AND ?
        GROUP BY year, month
        ORDER BY year, month
    """, (f"%{product_name}%", month_start, month_end))

    if not rows:
        return f"No data for '{product_name}' in months {month_start}-{month_end}."
    return json.dumps({"product": product_name, "months": f"{month_start}-{month_end}", "yoy_data": rows}, default=str)


@tracked_tool("DemandForecaster")
async def get_seasonal_forecast(
    product_category: Annotated[str, Field(description="Product category: Schokolade, Fruchtgummi, Marzipan, Saisonware, Geschenkpackung")],
    season: Annotated[str, Field(description="Season to forecast: easter or christmas")],
) -> str:
    """Get sales forecast data for a product category and upcoming season based on historical trends."""
    if season == "easter":
        months = (1, 2, 3, 4)
    elif season == "christmas":
        months = (9, 10, 11, 12)
    else:
        return f"Unknown season '{season}'. Use 'easter' or 'christmas'."

    placeholders = ",".join("?" * len(months))
    rows = await _query_db(f"""
        SELECT strftime('%Y', s.date) as year,
               strftime('%m', s.date) as month,
               p.name as product,
               SUM(s.quantity) as total_quantity,
               ROUND(SUM(s.revenue), 2) as total_revenue,
               ROUND(AVG(s.quantity), 0) as avg_daily_quantity
        FROM sales_history s
        JOIN products p ON s.product_id = p.id
        WHERE p.category = ?
        AND CAST(strftime('%m', s.date) AS INTEGER) IN ({placeholders})
        GROUP BY year, month, p.name
        ORDER BY year, month, p.name
    """, (product_category, *months))

    if not rows:
        return f"No historical data for category '{product_category}' in {season} months."
    return json.dumps({
        "category": product_category,
        "season": season,
        "historical_data": rows,
        "note": "Use these trends to project upcoming season demand. Consider YoY growth rate."
    }, default=str)


@tracked_tool("DemandForecaster")
async def get_top_products(
    start_date: Annotated[str, Field(description="Start date YYYY-MM-DD")] = "2025-01-01",
    end_date: Annotated[str, Field(description="End date YYYY-MM-DD")] = "2026-03-25",
    limit: Annotated[int, Field(description="Number of top products to return")] = 10,
) -> str:
    """Get top-selling products by revenue in a given period."""
    rows = await _query_db("""
        SELECT p.name, p.category, SUM(s.quantity) as total_quantity,
               ROUND(SUM(s.revenue), 2) as total_revenue
        FROM sales_history s
        JOIN products p ON s.product_id = p.id
        WHERE s.date BETWEEN ? AND ?
        GROUP BY p.id
        ORDER BY total_revenue DESC
        LIMIT ?
    """, (start_date, end_date, limit))
    return json.dumps({"period": f"{start_date} to {end_date}", "top_products": rows}, default=str)
