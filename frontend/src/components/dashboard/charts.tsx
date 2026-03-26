"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
  Cell,
  ReferenceLine,
  ComposedChart,
  Line,
} from "recharts";
import { api, type SalesTrendItem, type InventoryItem, type QualityOverviewItem } from "@/lib/api";
import { AlertTriangle, CheckCircle2 } from "lucide-react";

export function SalesTrendChart() {
  const [data, setData] = useState<SalesTrendItem[]>([]);

  useEffect(() => {
    api.getSalesTrend().then((d) => setData(d.sales_trend)).catch(() => {});
  }, []);

  const chartData = data.map((d) => {
    const month = d.month.slice(2); // "24-04"
    const m = parseInt(d.month.split("-")[1]);
    return {
      month,
      revenue: Math.round(d.revenue / 1000),
      quantity: Math.round(d.quantity / 1000),
      isChristmas: m >= 10 && m <= 12,
      isEaster: m >= 2 && m <= 4,
    };
  });

  return (
    <Card className="border-border/50">
      <CardHeader className="pb-1">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
            Revenue &amp; Volume Trend
          </CardTitle>
          <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-[oklch(0.55_0.18_250)]" />
              Revenue (€k)
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-0.5 bg-[oklch(0.7_0.15_160)]" />
              Volume (k units)
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pb-3">
        {chartData.length === 0 ? (
          <div className="h-[300px] flex items-center justify-center text-muted-foreground text-sm">Loading...</div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="oklch(0.55 0.18 250)" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="oklch(0.55 0.18 250)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.3 0.02 250 / 20%)" />
              <XAxis
                dataKey="month"
                tick={{ fontSize: 10, fill: "oklch(0.55 0.02 250)" }}
                interval={1}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                yAxisId="revenue"
                tick={{ fontSize: 10, fill: "oklch(0.55 0.02 250)" }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => `€${v}k`}
              />
              <YAxis
                yAxisId="quantity"
                orientation="right"
                tick={{ fontSize: 10, fill: "oklch(0.55 0.02 250)" }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => `${v}k`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "oklch(0.16 0.015 250)",
                  border: "1px solid oklch(0.28 0.02 250)",
                  borderRadius: "8px",
                  color: "oklch(0.95 0.005 250)",
                  fontSize: "11px",
                  padding: "8px 12px",
                }}
                formatter={(value, name) => {
                  if (name === "revenue") return [`€${value}k`, "Revenue"];
                  return [`${value}k units`, "Volume"];
                }}
              />
              <Area
                yAxisId="revenue"
                type="monotone"
                dataKey="revenue"
                stroke="oklch(0.55 0.18 250)"
                strokeWidth={2}
                fill="url(#revenueGrad)"
              />
              <Line
                yAxisId="quantity"
                type="monotone"
                dataKey="quantity"
                stroke="oklch(0.7 0.15 160)"
                strokeWidth={1.5}
                strokeDasharray="4 3"
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

export function InventoryChart() {
  const [data, setData] = useState<InventoryItem[]>([]);

  useEffect(() => {
    api.getInventoryLevels().then((d) => setData(d.inventory_levels)).catch(() => {});
  }, []);

  const chartData = data.slice(0, 12).map((d) => ({
    name: d.name.length > 20 ? d.name.slice(0, 18) + "…" : d.name,
    fullName: d.name,
    ratio: d.stock_ratio,
    stock: d.current_stock,
    reorder: d.reorder_point,
    unit: d.unit,
  }));

  const getBarColor = (ratio: number) => {
    if (ratio < 1) return "oklch(0.65 0.22 25)";
    if (ratio < 1.5) return "oklch(0.75 0.16 70)";
    if (ratio < 2.0) return "oklch(0.65 0.15 160)";
    return "oklch(0.6 0.12 160)";
  };

  return (
    <Card className="border-border/50">
      <CardHeader className="pb-1">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
            Raw Material Stock Levels
          </CardTitle>
          <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-sm bg-[oklch(0.65_0.22_25)]" /> &lt;1x
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-sm bg-[oklch(0.75_0.16_70)]" /> 1-1.5x
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-sm bg-[oklch(0.65_0.15_160)]" /> &gt;1.5x
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pb-3">
        {chartData.length === 0 ? (
          <div className="h-[300px] flex items-center justify-center text-muted-foreground text-sm">Loading...</div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 0 }} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.3 0.02 250 / 20%)" horizontal={false} />
              <XAxis
                type="number"
                tick={{ fontSize: 10, fill: "oklch(0.55 0.02 250)" }}
                axisLine={false}
                tickLine={false}
                domain={[0, "dataMax"]}
                tickFormatter={(v) => `${v}x`}
              />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fontSize: 9, fill: "oklch(0.6 0.02 250)" }}
                width={130}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "oklch(0.16 0.015 250)",
                  border: "1px solid oklch(0.28 0.02 250)",
                  borderRadius: "8px",
                  color: "oklch(0.95 0.005 250)",
                  fontSize: "11px",
                  padding: "8px 12px",
                }}
                formatter={(value, _name, props) => {
                  const d = props.payload;
                  return [`${Number(value).toFixed(2)}x — Stock: ${d.stock.toLocaleString()} ${d.unit} (reorder at ${d.reorder.toLocaleString()})`, d.fullName];
                }}
              />
              <ReferenceLine x={1} stroke="oklch(0.65 0.22 25)" strokeDasharray="3 3" strokeWidth={1.5} label={{ value: "Reorder", fill: "oklch(0.65 0.2 25)", fontSize: 9, position: "top" }} />
              <Bar dataKey="ratio" radius={[0, 4, 4, 0]} barSize={16}>
                {chartData.map((entry, index) => (
                  <Cell key={index} fill={getBarColor(entry.ratio)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

export function QualityLinesMonitor({ onInvestigate }: { onInvestigate?: (lineName: string) => void }) {
  const [data, setData] = useState<QualityOverviewItem[]>([]);

  useEffect(() => {
    api.getQualityOverview().then((d) => setData(d.quality_overview)).catch(() => {});
  }, []);

  return (
    <Card className="border-border/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
          Production Lines — Live Quality
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {data.length === 0 ? (
          <div className="h-[120px] flex items-center justify-center text-muted-foreground text-sm">Loading...</div>
        ) : (
          data.map((line) => {
            const hasIssues = line.warnings > 0 || line.criticals > 0;
            return (
              <div
                key={line.line_name}
                className={`flex items-center gap-3 p-2.5 rounded-lg border transition-colors ${
                  line.criticals > 0
                    ? "border-red-500/30 bg-red-500/5"
                    : line.warnings > 0
                    ? "border-amber-500/20 bg-amber-500/5"
                    : "border-border/30 bg-muted/10"
                }`}
              >
                <div className={`shrink-0 p-1.5 rounded-md ${
                  line.criticals > 0 ? "bg-red-500/15" : line.warnings > 0 ? "bg-amber-500/15" : "bg-emerald-500/10"
                }`}>
                  {hasIssues ? (
                    <AlertTriangle className={`h-3.5 w-3.5 ${line.criticals > 0 ? "text-red-400" : "text-amber-400"}`} />
                  ) : (
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium truncate">{line.line_name}</span>
                    <Badge variant="outline" className="text-[9px] border-border/40 text-muted-foreground">
                      {line.type}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-3 mt-0.5 text-[10px] text-muted-foreground">
                    <span>Temp: {line.avg_temp}°C</span>
                    <span>Humidity: {line.avg_humidity}%</span>
                    <span>Defect: {line.avg_defect_rate}%</span>
                  </div>
                </div>
                <div className="shrink-0 text-right">
                  {hasIssues ? (
                    <button
                      onClick={() => onInvestigate?.(line.line_name)}
                      className="flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-medium transition-colors cursor-pointer hover:bg-amber-500/15 border border-amber-500/30"
                    >
                      {line.criticals > 0 && <span className="text-red-400">{line.criticals} crit</span>}
                      {line.warnings > 0 && <span className="text-amber-400">{line.warnings} warn</span>}
                      <span className="text-amber-400 ml-0.5">→ Investigate</span>
                    </button>
                  ) : (
                    <span className="text-[10px] text-emerald-400 font-medium">OK</span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}
