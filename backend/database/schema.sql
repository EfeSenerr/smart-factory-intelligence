-- Confectionery Manufacturing Database Schema

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    sku TEXT UNIQUE NOT NULL,
    seasonal INTEGER NOT NULL DEFAULT 0,
    season TEXT,
    unit_weight_g REAL NOT NULL,
    shelf_life_days INTEGER NOT NULL,
    unit_cost REAL NOT NULL,
    unit_price REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS production_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    capacity_per_hour INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    efficiency_pct REAL NOT NULL DEFAULT 95.0
);

CREATE TABLE IF NOT EXISTS sales_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    revenue REAL NOT NULL,
    channel TEXT NOT NULL,
    region TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS quality_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    line_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    temperature_c REAL NOT NULL,
    humidity_pct REAL NOT NULL,
    weight_deviation_pct REAL NOT NULL,
    viscosity REAL,
    defect_rate_pct REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'ok',
    FOREIGN KEY (line_id) REFERENCES production_lines(id)
);

CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    material_type TEXT NOT NULL,
    reliability_score REAL NOT NULL,
    lead_time_days INTEGER NOT NULL,
    country TEXT NOT NULL,
    contact_email TEXT
);

CREATE TABLE IF NOT EXISTS raw_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    unit TEXT NOT NULL,
    current_stock REAL NOT NULL,
    reorder_point REAL NOT NULL,
    lead_time_days INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    unit_cost REAL NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

CREATE TABLE IF NOT EXISTS production_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    line_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'planned',
    priority TEXT NOT NULL DEFAULT 'normal',
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (line_id) REFERENCES production_lines(id)
);

CREATE TABLE IF NOT EXISTS quality_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    embedding TEXT
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_sales_date ON sales_history(date);
CREATE INDEX IF NOT EXISTS idx_sales_product ON sales_history(product_id);
CREATE INDEX IF NOT EXISTS idx_quality_line ON quality_metrics(line_id);
CREATE INDEX IF NOT EXISTS idx_quality_timestamp ON quality_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_production_orders_status ON production_orders(status);
CREATE INDEX IF NOT EXISTS idx_production_orders_dates ON production_orders(start_date, end_date);
