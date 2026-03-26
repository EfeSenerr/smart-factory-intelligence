"""Quality monitoring and document search tools for the Quality Agent."""

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


@tracked_tool("QualityInspector")
async def get_quality_metrics(
    line_id: Annotated[int, Field(description="Production line ID (1-5). 1-2 are chocolate, 3 is gummy, 4 is marzipan, 5 is packaging.")],
    hours: Annotated[int, Field(description="Number of hours of recent data to retrieve")] = 24,
) -> str:
    """Get recent quality metrics for a production line."""
    rows = await _query_db("""
        SELECT qm.*, pl.name as line_name, pl.type as line_type
        FROM quality_metrics qm
        JOIN production_lines pl ON qm.line_id = pl.id
        WHERE qm.line_id = ?
        ORDER BY qm.timestamp DESC
        LIMIT ?
    """, (line_id, hours * 4))  # 4 readings per hour approximation

    if not rows:
        return f"No quality data found for line {line_id}."

    # Calculate summary statistics
    temps = [r["temperature_c"] for r in rows]
    humidities = [r["humidity_pct"] for r in rows]
    weight_devs = [r["weight_deviation_pct"] for r in rows]
    warnings = sum(1 for r in rows if r["status"] == "warning")
    criticals = sum(1 for r in rows if r["status"] == "critical")

    return json.dumps({
        "line_id": line_id,
        "line_name": rows[0]["line_name"],
        "line_type": rows[0]["line_type"],
        "readings_count": len(rows),
        "summary": {
            "temperature": {"min": round(min(temps), 1), "max": round(max(temps), 1), "avg": round(sum(temps)/len(temps), 1)},
            "humidity": {"min": round(min(humidities), 1), "max": round(max(humidities), 1), "avg": round(sum(humidities)/len(humidities), 1)},
            "weight_deviation": {"min": round(min(weight_devs), 2), "max": round(max(weight_devs), 2), "avg": round(sum(weight_devs)/len(weight_devs), 2)},
            "warnings": warnings,
            "criticals": criticals,
        },
        "recent_readings": rows[:12],
    }, default=str)


@tracked_tool("QualityInspector")
async def detect_anomalies(
    line_id: Annotated[int, Field(description="Production line ID to check for anomalies (1-5)")],
) -> str:
    """Detect quality anomalies on a production line by analyzing recent data for warnings, critical events, and trends."""
    rows = await _query_db("""
        SELECT qm.*, pl.name as line_name, pl.type as line_type
        FROM quality_metrics qm
        JOIN production_lines pl ON qm.line_id = pl.id
        WHERE qm.line_id = ?
        ORDER BY qm.timestamp DESC
        LIMIT 48
    """, (line_id,))

    if not rows:
        return f"No data for line {line_id}."

    anomalies = []
    for r in rows:
        if r["status"] in ("warning", "critical"):
            anomalies.append({
                "timestamp": r["timestamp"],
                "status": r["status"],
                "temperature_c": r["temperature_c"],
                "humidity_pct": r["humidity_pct"],
                "weight_deviation_pct": r["weight_deviation_pct"],
                "defect_rate_pct": r["defect_rate_pct"],
            })

    # Check for temperature trends
    temps = [r["temperature_c"] for r in rows[:12]]
    temp_trend = "stable"
    if len(temps) >= 4:
        recent_avg = sum(temps[:4]) / 4
        older_avg = sum(temps[4:8]) / max(1, len(temps[4:8]))
        if recent_avg - older_avg > 1.5:
            temp_trend = "RISING — potential issue"
        elif older_avg - recent_avg > 1.5:
            temp_trend = "FALLING — potential issue"

    return json.dumps({
        "line_id": line_id,
        "line_name": rows[0]["line_name"],
        "anomalies_found": len(anomalies),
        "temperature_trend": temp_trend,
        "anomaly_details": anomalies[:10],
        "recommendation": "Review SOP documentation for corrective actions" if anomalies else "No anomalies detected",
    }, default=str)


@tracked_tool("QualityInspector")
async def get_all_lines_status() -> str:
    """Get current status overview of all production lines including latest quality readings."""
    rows = await _query_db("""
        SELECT pl.id, pl.name, pl.type, pl.capacity_per_hour, pl.status, pl.efficiency_pct,
               (SELECT COUNT(*) FROM quality_metrics qm WHERE qm.line_id = pl.id AND qm.status = 'warning'
                AND qm.timestamp >= datetime('2026-03-25', '-3 days')) as recent_warnings,
               (SELECT COUNT(*) FROM quality_metrics qm WHERE qm.line_id = pl.id AND qm.status = 'critical'
                AND qm.timestamp >= datetime('2026-03-25', '-3 days')) as recent_criticals
        FROM production_lines pl
    """)
    return json.dumps({"production_lines": rows}, default=str)


@tracked_tool("QualityInspector")
async def search_quality_docs(
    query: Annotated[str, Field(description="Search query for quality documentation (e.g. 'temperature fluctuation', 'HACCP chocolate', 'packaging seal')")],
) -> str:
    """Search quality documents (SOPs, HACCP plans, certifications) by keyword. Returns relevant procedures and corrective actions."""
    # Text-based search (in production, this would use embeddings + vector search)
    rows = await _query_db("""
        SELECT id, title, content, category
        FROM quality_documents
        WHERE content LIKE ? OR title LIKE ?
        ORDER BY
            CASE WHEN title LIKE ? THEN 1
                 WHEN content LIKE ? THEN 2
                 ELSE 3 END
        LIMIT 3
    """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))

    if not rows:
        # Broader search: try individual words
        words = query.split()
        for word in words:
            if len(word) > 3:
                rows = await _query_db("""
                    SELECT id, title, content, category
                    FROM quality_documents
                    WHERE content LIKE ? OR title LIKE ?
                    LIMIT 3
                """, (f"%{word}%", f"%{word}%"))
                if rows:
                    break

    if not rows:
        return f"No quality documents found matching '{query}'."

    results = []
    for r in rows:
        results.append({
            "title": r["title"],
            "category": r["category"],
            "content": r["content"][:2000],
        })
    return json.dumps({"search_query": query, "documents_found": len(results), "documents": results}, default=str)
