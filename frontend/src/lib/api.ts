const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface DashboardKPIs {
  active_orders: number;
  units_in_production: number;
  quality_score: number;
  inventory_alerts: number;
  revenue_this_month: number;
  revenue_last_month: number;
}

export interface SalesTrendItem {
  month: string;
  revenue: number;
  quantity: number;
}

export interface QualityOverviewItem {
  line_name: string;
  type: string;
  avg_temp: number;
  avg_humidity: number;
  avg_weight_dev: number;
  avg_defect_rate: number;
  warnings: number;
  criticals: number;
  total_readings: number;
}

export interface InventoryItem {
  name: string;
  current_stock: number;
  reorder_point: number;
  unit: string;
  stock_ratio: number;
}

export interface ProductionOrder {
  id: number;
  product: string;
  line: string;
  quantity: number;
  start_date: string;
  end_date: string;
  status: string;
  priority: string;
}

export interface ConnectedTool {
  id: string;
  name: string;
  type: string;
  status: string;
  description: string;
  icon: string;
  tools_count: number;
  last_sync: string;
}

async function fetchApi<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  getDashboard: () => fetchApi<{ kpis: DashboardKPIs }>("/api/dashboard"),
  getSalesTrend: () => fetchApi<{ sales_trend: SalesTrendItem[] }>("/api/dashboard/sales-trend"),
  getQualityOverview: () => fetchApi<{ quality_overview: QualityOverviewItem[] }>("/api/dashboard/quality-overview"),
  getInventoryLevels: () => fetchApi<{ inventory_levels: InventoryItem[] }>("/api/dashboard/inventory-levels"),
  getProductionOrders: () => fetchApi<{ production_orders: ProductionOrder[] }>("/api/dashboard/production-orders"),
  getToolsStatus: () => fetchApi<{ connected_tools: ConnectedTool[] }>("/api/tools/status"),
};
