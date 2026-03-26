"""Seed the manufacturing database with realistic confectionery dummy data."""

import asyncio
import json
import math
import os
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "manufacturing.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

random.seed(42)

# ---------------------------------------------------------------------------
# Product catalog – German confectionery names, realistic categories
# ---------------------------------------------------------------------------
PRODUCTS = [
    # Chocolate
    {"name": "Edel-Vollmilch Tafel", "category": "Schokolade", "sku": "CHOC-TAF-001", "seasonal": 0, "season": None, "unit_weight_g": 100, "shelf_life_days": 365, "unit_cost": 0.85, "unit_price": 1.99},
    {"name": "Zartbitter 70% Tafel", "category": "Schokolade", "sku": "CHOC-TAF-002", "seasonal": 0, "season": None, "unit_weight_g": 100, "shelf_life_days": 365, "unit_cost": 0.95, "unit_price": 2.29},
    {"name": "Nougat-Pralinen Klassik", "category": "Schokolade", "sku": "CHOC-PRA-001", "seasonal": 0, "season": None, "unit_weight_g": 200, "shelf_life_days": 180, "unit_cost": 2.10, "unit_price": 5.49},
    {"name": "Trüffel Champagner", "category": "Schokolade", "sku": "CHOC-TRU-001", "seasonal": 0, "season": None, "unit_weight_g": 150, "shelf_life_days": 120, "unit_cost": 2.80, "unit_price": 6.99},
    {"name": "Schoko-Riegel Nuss", "category": "Schokolade", "sku": "CHOC-RIG-001", "seasonal": 0, "season": None, "unit_weight_g": 45, "shelf_life_days": 270, "unit_cost": 0.30, "unit_price": 0.89},
    {"name": "Weiße Schokolade Vanille", "category": "Schokolade", "sku": "CHOC-TAF-003", "seasonal": 0, "season": None, "unit_weight_g": 100, "shelf_life_days": 300, "unit_cost": 0.90, "unit_price": 2.19},
    # Gummy
    {"name": "Fruchtbärchen Original", "category": "Fruchtgummi", "sku": "GUM-BAR-001", "seasonal": 0, "season": None, "unit_weight_g": 200, "shelf_life_days": 540, "unit_cost": 0.55, "unit_price": 1.49},
    {"name": "Saure Würmer Mix", "category": "Fruchtgummi", "sku": "GUM-WUR-001", "seasonal": 0, "season": None, "unit_weight_g": 200, "shelf_life_days": 540, "unit_cost": 0.60, "unit_price": 1.59},
    {"name": "Fruchtschnecken Tropic", "category": "Fruchtgummi", "sku": "GUM-FSC-001", "seasonal": 0, "season": None, "unit_weight_g": 175, "shelf_life_days": 540, "unit_cost": 0.50, "unit_price": 1.39},
    {"name": "Cola-Flaschen", "category": "Fruchtgummi", "sku": "GUM-COL-001", "seasonal": 0, "season": None, "unit_weight_g": 200, "shelf_life_days": 540, "unit_cost": 0.55, "unit_price": 1.49},
    {"name": "Vegane Fruchtherzen", "category": "Fruchtgummi", "sku": "GUM-VEG-001", "seasonal": 0, "season": None, "unit_weight_g": 175, "shelf_life_days": 480, "unit_cost": 0.70, "unit_price": 1.89},
    # Marzipan
    {"name": "Marzipankartoffeln", "category": "Marzipan", "sku": "MAR-KAR-001", "seasonal": 0, "season": None, "unit_weight_g": 125, "shelf_life_days": 180, "unit_cost": 1.20, "unit_price": 2.99},
    {"name": "Marzipanbrot", "category": "Marzipan", "sku": "MAR-BRT-001", "seasonal": 0, "season": None, "unit_weight_g": 200, "shelf_life_days": 180, "unit_cost": 1.80, "unit_price": 4.49},
    {"name": "Edelmarzipan Tafel", "category": "Marzipan", "sku": "MAR-TAF-001", "seasonal": 0, "season": None, "unit_weight_g": 100, "shelf_life_days": 240, "unit_cost": 1.50, "unit_price": 3.99},
    # Seasonal - Easter
    {"name": "Schokoladen-Osterhase", "category": "Saisonware", "sku": "SEA-OST-001", "seasonal": 1, "season": "easter", "unit_weight_g": 150, "shelf_life_days": 270, "unit_cost": 1.10, "unit_price": 3.49},
    {"name": "Ostereier Nougat-Füllung", "category": "Saisonware", "sku": "SEA-OST-002", "seasonal": 1, "season": "easter", "unit_weight_g": 200, "shelf_life_days": 180, "unit_cost": 1.40, "unit_price": 3.99},
    {"name": "Osterhasen Mini-Mix (10er)", "category": "Saisonware", "sku": "SEA-OST-003", "seasonal": 1, "season": "easter", "unit_weight_g": 100, "shelf_life_days": 270, "unit_cost": 2.00, "unit_price": 4.99},
    {"name": "Osternest Pralinenmischung", "category": "Saisonware", "sku": "SEA-OST-004", "seasonal": 1, "season": "easter", "unit_weight_g": 300, "shelf_life_days": 150, "unit_cost": 3.50, "unit_price": 8.99},
    # Seasonal - Christmas
    {"name": "Weihnachtsmann Vollmilch", "category": "Saisonware", "sku": "SEA-WEI-001", "seasonal": 1, "season": "christmas", "unit_weight_g": 125, "shelf_life_days": 270, "unit_cost": 1.00, "unit_price": 2.99},
    {"name": "Adventskalender Premium", "category": "Saisonware", "sku": "SEA-WEI-002", "seasonal": 1, "season": "christmas", "unit_weight_g": 350, "shelf_life_days": 365, "unit_cost": 4.50, "unit_price": 12.99},
    {"name": "Dominosteine Klassik", "category": "Saisonware", "sku": "SEA-WEI-003", "seasonal": 1, "season": "christmas", "unit_weight_g": 250, "shelf_life_days": 180, "unit_cost": 1.60, "unit_price": 3.99},
    {"name": "Lebkuchen-Herzen Schoko", "category": "Saisonware", "sku": "SEA-WEI-004", "seasonal": 1, "season": "christmas", "unit_weight_g": 200, "shelf_life_days": 270, "unit_cost": 1.30, "unit_price": 3.49},
    {"name": "Stollen-Konfekt", "category": "Saisonware", "sku": "SEA-WEI-005", "seasonal": 1, "season": "christmas", "unit_weight_g": 200, "shelf_life_days": 120, "unit_cost": 2.20, "unit_price": 5.49},
    # Gift boxes
    {"name": "Pralinenmischung Deluxe", "category": "Geschenkpackung", "sku": "GIF-PRA-001", "seasonal": 0, "season": None, "unit_weight_g": 400, "shelf_life_days": 180, "unit_cost": 5.00, "unit_price": 14.99},
    {"name": "Schokoladen-Genießer Box", "category": "Geschenkpackung", "sku": "GIF-BOX-001", "seasonal": 0, "season": None, "unit_weight_g": 500, "shelf_life_days": 180, "unit_cost": 6.50, "unit_price": 19.99},
    {"name": "Fruchtgummi Party-Box", "category": "Geschenkpackung", "sku": "GIF-PAR-001", "seasonal": 0, "season": None, "unit_weight_g": 600, "shelf_life_days": 360, "unit_cost": 3.00, "unit_price": 7.99},
    {"name": "Marzipan Auslese", "category": "Geschenkpackung", "sku": "GIF-MAR-001", "seasonal": 0, "season": None, "unit_weight_g": 300, "shelf_life_days": 150, "unit_cost": 4.20, "unit_price": 11.99},
]

PRODUCTION_LINES = [
    {"name": "Schokoladen-Linie 1", "type": "chocolate", "capacity_per_hour": 2000, "status": "running", "efficiency_pct": 94.5},
    {"name": "Schokoladen-Linie 2", "type": "chocolate", "capacity_per_hour": 1800, "status": "running", "efficiency_pct": 91.2},
    {"name": "Fruchtgummi-Linie 1", "type": "gummy", "capacity_per_hour": 3000, "status": "running", "efficiency_pct": 96.1},
    {"name": "Marzipan-Linie 1", "type": "marzipan", "capacity_per_hour": 1200, "status": "running", "efficiency_pct": 93.8},
    {"name": "Verpackungs-Linie 1", "type": "packaging", "capacity_per_hour": 5000, "status": "running", "efficiency_pct": 97.3},
]

SUPPLIERS = [
    {"name": "Westafrika Kakao GmbH", "material_type": "Kakaobohnen", "reliability_score": 0.92, "lead_time_days": 21, "country": "Ghana", "contact_email": "order@westafrika-kakao.de"},
    {"name": "Süddeutsche Zuckerfabrik", "material_type": "Zucker", "reliability_score": 0.98, "lead_time_days": 3, "country": "Germany", "contact_email": "einkauf@sz-zucker.de"},
    {"name": "Alpenmilch Genossenschaft", "material_type": "Milchpulver", "reliability_score": 0.96, "lead_time_days": 5, "country": "Germany", "contact_email": "vertrieb@alpenmilch.de"},
    {"name": "Nordic Gelatine AS", "material_type": "Gelatine", "reliability_score": 0.94, "lead_time_days": 7, "country": "Denmark", "contact_email": "sales@nordic-gelatine.dk"},
    {"name": "Lübecker Mandel Import", "material_type": "Mandeln", "reliability_score": 0.90, "lead_time_days": 14, "country": "Spain", "contact_email": "info@luebecker-mandel.de"},
    {"name": "Bourbon Vanille Direct", "material_type": "Vanille", "reliability_score": 0.85, "lead_time_days": 30, "country": "Madagascar", "contact_email": "export@bvdirect.mg"},
    {"name": "Fruchtkonzentrat Europa", "material_type": "Fruchtkonzentrate", "reliability_score": 0.95, "lead_time_days": 5, "country": "Netherlands", "contact_email": "order@fruchtkonzentrat.nl"},
    {"name": "Kakaobutter Spezial AG", "material_type": "Kakaobutter", "reliability_score": 0.93, "lead_time_days": 18, "country": "Ivory Coast", "contact_email": "supply@kb-spezial.de"},
    {"name": "PackRight Verpackungen", "material_type": "Verpackung", "reliability_score": 0.97, "lead_time_days": 7, "country": "Germany", "contact_email": "bestellung@packright.de"},
    {"name": "Haselnuss Piemont SRL", "material_type": "Haselnüsse", "reliability_score": 0.91, "lead_time_days": 10, "country": "Italy", "contact_email": "ordini@nocciola-piemonte.it"},
]

RAW_MATERIALS = [
    {"name": "Kakaobohnen (Rohkakao)", "unit": "kg", "current_stock": 12500, "reorder_point": 5000, "lead_time_days": 21, "supplier_id": 1, "unit_cost": 4.20},
    {"name": "Kristallzucker", "unit": "kg", "current_stock": 28000, "reorder_point": 10000, "lead_time_days": 3, "supplier_id": 2, "unit_cost": 0.85},
    {"name": "Vollmilchpulver", "unit": "kg", "current_stock": 8500, "reorder_point": 3000, "lead_time_days": 5, "supplier_id": 3, "unit_cost": 3.50},
    {"name": "Gelatine (Blatt)", "unit": "kg", "current_stock": 2200, "reorder_point": 800, "lead_time_days": 7, "supplier_id": 4, "unit_cost": 12.00},
    {"name": "Mandeln (geschält)", "unit": "kg", "current_stock": 3800, "reorder_point": 1500, "lead_time_days": 14, "supplier_id": 5, "unit_cost": 8.50},
    {"name": "Bourbon-Vanilleschoten", "unit": "kg", "current_stock": 45, "reorder_point": 20, "lead_time_days": 30, "supplier_id": 6, "unit_cost": 320.00},
    {"name": "Fruchtkonzentrate Mix", "unit": "kg", "current_stock": 5500, "reorder_point": 2000, "lead_time_days": 5, "supplier_id": 7, "unit_cost": 2.80},
    {"name": "Kakaobutter", "unit": "kg", "current_stock": 6200, "reorder_point": 2500, "lead_time_days": 18, "supplier_id": 8, "unit_cost": 7.80},
    {"name": "Verpackungsfolie (Rolle)", "unit": "Rolle", "current_stock": 850, "reorder_point": 300, "lead_time_days": 7, "supplier_id": 9, "unit_cost": 25.00},
    {"name": "Kartonagen (Palette)", "unit": "Palette", "current_stock": 120, "reorder_point": 40, "lead_time_days": 7, "supplier_id": 9, "unit_cost": 180.00},
    {"name": "Haselnüsse (geröstet)", "unit": "kg", "current_stock": 4100, "reorder_point": 1500, "lead_time_days": 10, "supplier_id": 10, "unit_cost": 9.20},
    {"name": "Zitronensäure", "unit": "kg", "current_stock": 1800, "reorder_point": 500, "lead_time_days": 5, "supplier_id": 7, "unit_cost": 1.90},
    {"name": "Lebensmittelfarben Set", "unit": "Liter", "current_stock": 320, "reorder_point": 100, "lead_time_days": 7, "supplier_id": 7, "unit_cost": 15.00},
    {"name": "Nougat-Masse", "unit": "kg", "current_stock": 3200, "reorder_point": 1200, "lead_time_days": 5, "supplier_id": 3, "unit_cost": 6.50},
    {"name": "Marzipan-Rohmasse", "unit": "kg", "current_stock": 2800, "reorder_point": 1000, "lead_time_days": 7, "supplier_id": 5, "unit_cost": 7.80},
]

CHANNELS = ["retail", "wholesale", "online"]
REGIONS = ["Nord", "Süd", "West", "Ost", "Export"]


def _seasonal_multiplier(date: datetime, product: dict) -> float:
    """Generate realistic seasonal demand multipliers."""
    month = date.month
    is_seasonal = product["seasonal"]
    season = product.get("season")

    # Base noise
    base = 1.0 + random.gauss(0, 0.08)

    if is_seasonal and season == "easter":
        # Easter products: ramp Jan-Mar, peak Mar, drop April
        if month == 1:
            return base * 1.5
        elif month == 2:
            return base * 3.0
        elif month == 3:
            return base * 5.0
        elif month == 4:
            return base * 2.0
        else:
            return base * 0.05  # near-zero off-season
    elif is_seasonal and season == "christmas":
        # Christmas: ramp Sep, peak Oct-Nov-Dec
        if month == 9:
            return base * 1.8
        elif month == 10:
            return base * 3.5
        elif month == 11:
            return base * 5.5
        elif month == 12:
            return base * 6.0
        else:
            return base * 0.05
    else:
        # Year-round products: mild seasonal variation
        # Summer dip for chocolate, slight holiday lift
        if product["category"] == "Schokolade":
            summer_dip = 1.0 - 0.25 * math.exp(-((month - 7) ** 2) / 2)
            holiday_lift = 1.0 + 0.3 * math.exp(-((month - 12) ** 2) / 1.5)
            return base * summer_dip * holiday_lift
        elif product["category"] == "Fruchtgummi":
            # Slight summer boost
            summer_boost = 1.0 + 0.15 * math.exp(-((month - 7) ** 2) / 3)
            return base * summer_boost
        elif product["category"] == "Geschenkpackung":
            # Holiday gift peaks
            if month in (11, 12):
                return base * 2.5
            elif month in (3, 4):
                return base * 1.5
            else:
                return base * 0.7
        else:
            return base


def _year_over_year_growth(year: int) -> float:
    """Simulate slight YoY growth."""
    if year == 2024:
        return 1.0
    elif year == 2025:
        return 1.06  # 6% growth
    else:
        return 1.12  # 12% cumulative


def generate_sales_data(products: list[dict], start_date: datetime, end_date: datetime) -> list[tuple]:
    """Generate daily sales data with seasonal patterns."""
    rows = []
    current = start_date
    while current <= end_date:
        for idx, product in enumerate(products):
            product_id = idx + 1
            multiplier = _seasonal_multiplier(current, product)
            yoy = _year_over_year_growth(current.year)

            if multiplier < 0.1:
                # Off-season: occasional small sale
                if random.random() < 0.05:
                    for channel in random.sample(CHANNELS, 1):
                        qty = random.randint(1, 20)
                        revenue = round(qty * product["unit_price"] * random.uniform(0.9, 1.0), 2)
                        region = random.choice(REGIONS)
                        rows.append((product_id, current.strftime("%Y-%m-%d"), qty, revenue, channel, region))
                continue

            # Generate 1-3 channel entries per day
            active_channels = random.sample(CHANNELS, k=random.randint(1, 3))
            for channel in active_channels:
                base_qty = {"retail": 150, "wholesale": 500, "online": 60}[channel]
                qty = max(1, int(base_qty * multiplier * yoy * random.uniform(0.7, 1.3)))
                # Wholesale gets volume discount
                price_mult = 0.75 if channel == "wholesale" else (0.95 if channel == "online" else 1.0)
                revenue = round(qty * product["unit_price"] * price_mult, 2)
                region = random.choice(REGIONS)
                rows.append((product_id, current.strftime("%Y-%m-%d"), qty, revenue, channel, region))

        current += timedelta(days=1)
    return rows


def generate_quality_metrics(lines: list[dict], start_date: datetime, end_date: datetime) -> list[tuple]:
    """Generate quality metrics with occasional anomalies."""
    rows = []
    current = start_date
    while current <= end_date:
        for idx, line in enumerate(lines):
            line_id = idx + 1
            # 4 readings per day (every 6 hours)
            for hour in [6, 12, 18, 0]:
                ts = current.replace(hour=hour).strftime("%Y-%m-%d %H:%M:%S")

                # Base values by line type
                if line["type"] == "chocolate":
                    temp = 31.5 + random.gauss(0, 0.3)
                    humidity = 45.0 + random.gauss(0, 2.0)
                    viscosity = 2800 + random.gauss(0, 50)
                elif line["type"] == "gummy":
                    temp = 85.0 + random.gauss(0, 1.0)
                    humidity = 55.0 + random.gauss(0, 3.0)
                    viscosity = 1200 + random.gauss(0, 30)
                elif line["type"] == "marzipan":
                    temp = 22.0 + random.gauss(0, 0.5)
                    humidity = 40.0 + random.gauss(0, 2.0)
                    viscosity = 5000 + random.gauss(0, 100)
                else:  # packaging
                    temp = 20.0 + random.gauss(0, 0.5)
                    humidity = 50.0 + random.gauss(0, 2.0)
                    viscosity = None

                weight_dev = abs(random.gauss(0, 0.5))
                defect_rate = abs(random.gauss(0.3, 0.2))

                # Inject anomalies (2% chance)
                status = "ok"
                if random.random() < 0.02:
                    anomaly_type = random.choice(["temp", "humidity", "weight"])
                    if anomaly_type == "temp":
                        temp += random.choice([-5, 5, -8, 8])
                        status = "warning" if abs(temp - 31.5) < 6 else "critical"
                    elif anomaly_type == "humidity":
                        humidity += random.choice([-10, 10, -15, 15])
                        status = "warning"
                    else:
                        weight_dev = random.uniform(2.0, 5.0)
                        defect_rate = random.uniform(2.0, 8.0)
                        status = "warning" if weight_dev < 3.0 else "critical"

                    # Make Line 2 have more recent issues (for demo scenario)
                    if line_id == 2 and current >= end_date - timedelta(days=3):
                        if random.random() < 0.3:
                            temp += random.uniform(3, 6)
                            status = "warning"

                rows.append((
                    line_id, ts, round(temp, 1), round(humidity, 1),
                    round(weight_dev, 2), round(viscosity, 0) if viscosity else None,
                    round(defect_rate, 2), status
                ))
        current += timedelta(days=1)
    return rows


def generate_production_orders(products: list[dict]) -> list[tuple]:
    """Generate current and upcoming production orders."""
    orders = []
    today = datetime(2026, 3, 26)

    # Active orders
    active = [
        (15, 1, 50000, today - timedelta(days=5), today + timedelta(days=3), "in_progress", "high"),   # Osterhasen
        (16, 1, 30000, today - timedelta(days=3), today + timedelta(days=5), "in_progress", "high"),   # Ostereier
        (1, 1, 15000, today - timedelta(days=2), today + timedelta(days=2), "in_progress", "normal"),  # Vollmilch
        (7, 3, 25000, today - timedelta(days=1), today + timedelta(days=4), "in_progress", "normal"),  # Fruchtbärchen
        (12, 4, 8000, today, today + timedelta(days=3), "in_progress", "normal"),                       # Marzipankartoffeln
    ]

    # Planned orders (upcoming)
    planned = [
        (17, 1, 40000, today + timedelta(days=4), today + timedelta(days=12), "planned", "high"),      # Osterhasen Mini
        (18, 1, 15000, today + timedelta(days=5), today + timedelta(days=10), "planned", "high"),      # Osternest
        (3, 1, 10000, today + timedelta(days=8), today + timedelta(days=12), "planned", "normal"),     # Pralinen
        (8, 3, 20000, today + timedelta(days=6), today + timedelta(days=10), "planned", "normal"),     # Saure Würmer
        (24, 5, 5000, today + timedelta(days=10), today + timedelta(days=14), "planned", "low"),       # Pralinenmischung
    ]

    # Completed orders (recent)
    completed = [
        (15, 1, 45000, today - timedelta(days=14), today - timedelta(days=6), "completed", "high"),
        (1, 2, 12000, today - timedelta(days=10), today - timedelta(days=5), "completed", "normal"),
        (7, 3, 22000, today - timedelta(days=8), today - timedelta(days=3), "completed", "normal"),
    ]

    for product_id, line_id, qty, start, end, status, priority in active + planned + completed:
        orders.append((
            product_id, line_id, qty,
            start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"),
            status, priority
        ))
    return orders


QUALITY_DOCUMENTS = [
    {
        "title": "SOP-CHOC-001: Temperierverfahren Schokolade",
        "category": "SOP",
        "content": """Standard Operating Procedure: Chocolate Tempering Process

1. SCOPE: Applies to all chocolate production lines (Linie 1, Linie 2).

2. TEMPERATURE RANGES:
   - Dark chocolate: 31-32°C working temperature
   - Milk chocolate: 29-31°C working temperature  
   - White chocolate: 27-29°C working temperature
   
3. CRITICAL CONTROL POINTS:
   - Temperature deviation > ±2°C from target: PAUSE production, recalibrate
   - Temperature deviation > ±5°C: STOP production immediately, notify shift supervisor
   - Temperature fluctuation pattern (>3 deviations in 1 hour): Check tempering machine cooling system, inspect water circulation pump
   
4. CORRECTIVE ACTIONS FOR TEMPERATURE FLUCTUATIONS:
   a) Check cooling water temperature and flow rate
   b) Inspect tempering unit sensors for calibration drift
   c) Verify ambient room temperature (should be 18-22°C)
   d) Check if chocolate mass viscosity is within spec (2600-3000 cP for milk chocolate)
   e) If fluctuations persist: Contact maintenance team, document in quality log
   
5. DOCUMENTATION: Record all deviations in QMS system within 30 minutes."""
    },
    {
        "title": "SOP-GUM-001: Fruchtgummi-Herstellung Qualitätskontrolle",
        "category": "SOP",
        "content": """Standard Operating Procedure: Gummy Production Quality Control

1. SCOPE: Fruchtgummi-Linie 1, all gummy candy products.

2. CRITICAL PARAMETERS:
   - Cooking temperature: 82-88°C (mix-dependent)
   - Moisture content: 17-21% at depositing
   - pH value: 3.2-3.8 (sour variants: 2.8-3.2)
   - Gelatin bloom strength: 220-250 for standard, 180-200 for soft variants
   
3. WEIGHT CONTROL:
   - Individual piece weight tolerance: ±5% of target
   - Bag weight tolerance: ±3% of declared weight
   - Sampling: Every 30 minutes, 10 pieces per sample
   
4. DEFECT CLASSIFICATION:
   - Critical: Foreign body, allergen cross-contamination → STOP, quarantine batch
   - Major: Color deviation, shape deformation >10% → Segregate, quality review
   - Minor: Surface imperfection, slight color variation → Accept with documentation
   
5. CORRECTIVE ACTIONS:
   a) Weight deviation: Check depositor nozzles, adjust pump pressure
   b) Texture issues: Verify gelatin concentration and cooking time
   c) Color inconsistency: Check colorant dosing system, verify raw material batch"""
    },
    {
        "title": "HACCP-001: Hazard Analysis Schokoladenproduktion",
        "category": "HACCP",
        "content": """HACCP Plan: Chocolate Production Facility

1. PRODUCT DESCRIPTION: Chocolate confectionery products including bars, pralines, and seasonal items.

2. CRITICAL CONTROL POINTS (CCPs):

   CCP1 - Raw Material Reception:
   - Hazard: Allergen cross-contamination (nuts, milk, soy)
   - Critical Limit: Allergen certificates for each delivery
   - Monitoring: Check certificates, visual inspection
   - Corrective Action: Reject non-conforming deliveries
   
   CCP2 - Roasting (Cocoa Beans):
   - Hazard: Salmonella, pathogenic bacteria
   - Critical Limit: Core temperature ≥120°C for ≥20 minutes
   - Monitoring: Continuous temperature recording
   - Corrective Action: Re-roast or reject batch
   
   CCP3 - Tempering:
   - Hazard: Microbiological (if temperature drops below 25°C for extended period)
   - Critical Limit: Maintain 27-32°C during processing
   - Monitoring: Automated temperature sensors every 30 seconds
   - Corrective Action: Discard affected batch if temperature < 25°C for > 30 min
   
   CCP4 - Metal Detection:
   - Hazard: Physical contamination (metal fragments)
   - Critical Limit: Fe ≥1.5mm, Non-Fe ≥2.0mm, SS ≥2.5mm
   - Monitoring: Every product unit passes through detector
   - Corrective Action: Reject and quarantine non-compliant product
   
3. ALLERGEN MANAGEMENT:
   - Dedicated lines for nut-free products where possible
   - Cleaning validation between allergen changeovers
   - "May contain traces of" labeling per EU Regulation 1169/2011"""
    },
    {
        "title": "SOP-MAR-001: Marzipan-Qualitätsstandards",
        "category": "SOP",
        "content": """Standard Operating Procedure: Marzipan Quality Standards

1. SCOPE: Marzipan-Linie 1, all marzipan products.

2. RAW MATERIAL REQUIREMENTS:
   - Almonds: California or Mediterranean origin, Class I
   - Sugar content: Max 35% for Edelmarzipan (per German Leitsätze)
   - Moisture: 12-17% in finished product
   
3. PRODUCTION PARAMETERS:
   - Grinding temperature: Max 40°C (prevent oil separation)
   - Roasting: Light roast at 150°C for 8-12 minutes
   - Kneading time: 15-20 minutes at room temperature
   
4. QUALITY TESTS:
   - Fat content analysis: Weekly (target: 28-32%)
   - Water activity (aw): Daily (target: 0.65-0.75)
   - Sensory evaluation: Each batch (color, taste, texture)
   - Shelf life testing: Monthly accelerated stability tests
   
5. COMMON ISSUES AND CORRECTIVE ACTIONS:
   a) Oil separation: Reduce grinding speed, check almond moisture content
   b) Grainy texture: Extend grinding time, verify roller gap settings
   c) Off-flavor: Check almond freshness, verify sugar source
   d) Color too dark: Reduce roasting time/temperature"""
    },
    {
        "title": "SOP-PKG-001: Verpackungslinien-Kontrolle",
        "category": "SOP",
        "content": """Standard Operating Procedure: Packaging Line Control

1. SCOPE: Verpackungs-Linie 1 and all secondary packaging operations.

2. PRE-PRODUCTION CHECKS:
   - Verify correct packaging material for product (barcode scan)
   - Check date coding equipment calibration
   - Verify seal temperature: 140-160°C for standard film
   - Check weight verification system calibration
   
3. IN-PROCESS CONTROLS:
   - Seal integrity: Visual check every 15 minutes
   - Date code legibility: Verify every 30 minutes
   - Metal detector challenge test: Every 2 hours with test pieces
   - Weight check: Continuous inline, sample verification hourly
   
4. LABELING REQUIREMENTS (EU):
   - Product name, ingredient list, allergen declaration (bold)
   - Net weight, best before date, batch/lot number
   - Nutritional information per 100g and per portion
   - Origin labeling for main ingredient if applicable
   
5. CORRECTIVE ACTIONS:
   a) Seal failure: Stop line, adjust temperature/pressure, retest
   b) Weight deviations: Recalibrate filler, check product density
   c) Label errors: Quarantine mislabeled product, correct and rework"""
    },
    {
        "title": "CERT-001: IFS Food Zertifizierung Anforderungen",
        "category": "Zertifizierung",
        "content": """IFS Food Certification Requirements Summary

1. OVERVIEW: International Featured Standards (IFS) Food is required for supplying to major European retailers.

2. KEY REQUIREMENTS:
   - HACCP-based food safety management system
   - Senior management commitment and food safety policy
   - Resource management including training programs
   - Production process controls and traceability
   - Measurement, analysis, and improvement procedures
   
3. SCORING: 
   - Fundamental requirements must score ≥ B
   - Major non-conformities: Score D on any question
   - KO (Knock Out) criteria: Automatic failure
   
4. KO CRITERIA (10 items):
   - Senior management commitment
   - HACCP monitoring system
   - Personnel hygiene
   - Raw material specifications
   - Compliance with product formulations
   - Management of foreign bodies
   - Traceability system
   - Internal audits
   - Product recall/withdrawal procedure
   - Corrective actions process
   
5. ANNUAL AUDIT: Typically 2-3 days, unannounced audits possible."""
    },
]


def seed_database():
    """Create and populate the manufacturing database."""
    # Remove existing DB
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Create schema
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    cursor.executescript(schema_sql)

    # Insert products
    for p in PRODUCTS:
        cursor.execute(
            "INSERT INTO products (name, category, sku, seasonal, season, unit_weight_g, shelf_life_days, unit_cost, unit_price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (p["name"], p["category"], p["sku"], p["seasonal"], p["season"], p["unit_weight_g"], p["shelf_life_days"], p["unit_cost"], p["unit_price"])
        )

    # Insert production lines
    for pl in PRODUCTION_LINES:
        cursor.execute(
            "INSERT INTO production_lines (name, type, capacity_per_hour, status, efficiency_pct) VALUES (?, ?, ?, ?, ?)",
            (pl["name"], pl["type"], pl["capacity_per_hour"], pl["status"], pl["efficiency_pct"])
        )

    # Insert suppliers
    for s in SUPPLIERS:
        cursor.execute(
            "INSERT INTO suppliers (name, material_type, reliability_score, lead_time_days, country, contact_email) VALUES (?, ?, ?, ?, ?, ?)",
            (s["name"], s["material_type"], s["reliability_score"], s["lead_time_days"], s["country"], s["contact_email"])
        )

    # Insert raw materials
    for rm in RAW_MATERIALS:
        cursor.execute(
            "INSERT INTO raw_materials (name, unit, current_stock, reorder_point, lead_time_days, supplier_id, unit_cost) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (rm["name"], rm["unit"], rm["current_stock"], rm["reorder_point"], rm["lead_time_days"], rm["supplier_id"], rm["unit_cost"])
        )

    # Generate and insert sales history (24 months: 2024-04 to 2026-03)
    print("Generating sales history...")
    start = datetime(2024, 4, 1)
    end = datetime(2026, 3, 25)
    sales = generate_sales_data(PRODUCTS, start, end)
    cursor.executemany(
        "INSERT INTO sales_history (product_id, date, quantity, revenue, channel, region) VALUES (?, ?, ?, ?, ?, ?)",
        sales
    )
    print(f"  → {len(sales)} sales records")

    # Generate and insert quality metrics (last 90 days for manageable size)
    print("Generating quality metrics...")
    qm_start = datetime(2026, 1, 1)
    qm_end = datetime(2026, 3, 25)
    metrics = generate_quality_metrics(PRODUCTION_LINES, qm_start, qm_end)
    cursor.executemany(
        "INSERT INTO quality_metrics (line_id, timestamp, temperature_c, humidity_pct, weight_deviation_pct, viscosity, defect_rate_pct, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        metrics
    )
    print(f"  → {len(metrics)} quality records")

    # Insert production orders
    orders = generate_production_orders(PRODUCTS)
    cursor.executemany(
        "INSERT INTO production_orders (product_id, line_id, quantity, start_date, end_date, status, priority) VALUES (?, ?, ?, ?, ?, ?, ?)",
        orders
    )
    print(f"  → {len(orders)} production orders")

    # Insert quality documents (without embeddings for now)
    for doc in QUALITY_DOCUMENTS:
        cursor.execute(
            "INSERT INTO quality_documents (title, content, category) VALUES (?, ?, ?)",
            (doc["title"], doc["content"], doc["category"])
        )
    print(f"  → {len(QUALITY_DOCUMENTS)} quality documents")

    conn.commit()

    # Print summary
    cursor.execute("SELECT COUNT(*) FROM products")
    print(f"\nDatabase seeded at: {DB_PATH}")
    print(f"  Products: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM sales_history")
    print(f"  Sales records: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM quality_metrics")
    print(f"  Quality metrics: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM production_orders")
    print(f"  Production orders: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM raw_materials")
    print(f"  Raw materials: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM suppliers")
    print(f"  Suppliers: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM quality_documents")
    print(f"  Quality documents: {cursor.fetchone()[0]}")

    # Quick sanity check: seasonal pattern visible?
    cursor.execute("""
        SELECT strftime('%Y-%m', date) as month, SUM(quantity) as total
        FROM sales_history
        WHERE product_id = 15  -- Osterhasen
        GROUP BY month ORDER BY month
    """)
    print("\n  Osterhase (Easter bunny) sales by month:")
    for row in cursor.fetchall():
        bar = "█" * (row[1] // 2000)
        print(f"    {row[0]}: {row[1]:>8,} {bar}")

    conn.close()


if __name__ == "__main__":
    seed_database()
