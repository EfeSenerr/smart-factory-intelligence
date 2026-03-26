"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { api, type DashboardKPIs } from "@/lib/api";
import {
  Factory,
  ShieldCheck,
  AlertTriangle,
  TrendingUp,
} from "lucide-react";

export function KPICards() {
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);

  useEffect(() => {
    api.getDashboard().then((d) => setKpis(d.kpis)).catch(() => {});
  }, []);

  if (!kpis) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-5">
              <div className="h-16 bg-muted rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const revenueChange = kpis.revenue_last_month
    ? ((kpis.revenue_this_month - kpis.revenue_last_month) / kpis.revenue_last_month) * 100
    : 0;

  const cards = [
    {
      label: "Active Production",
      value: `${kpis.active_orders} orders`,
      detail: `${(kpis.units_in_production ?? 0).toLocaleString()} units`,
      icon: Factory,
      color: "text-chart-1",
      bg: "bg-chart-1/10",
    },
    {
      label: "Quality Score",
      value: `${kpis.quality_score}%`,
      detail: kpis.quality_score >= 95 ? "Excellent" : kpis.quality_score >= 90 ? "Good" : "Needs attention",
      icon: ShieldCheck,
      color: kpis.quality_score >= 95 ? "text-chart-2" : "text-chart-5",
      bg: kpis.quality_score >= 95 ? "bg-chart-2/10" : "bg-chart-5/10",
    },
    {
      label: "Inventory Alerts",
      value: kpis.inventory_alerts.toString(),
      detail: kpis.inventory_alerts === 0 ? "All stocked" : "Materials low",
      icon: AlertTriangle,
      color: kpis.inventory_alerts > 0 ? "text-chart-5" : "text-chart-2",
      bg: kpis.inventory_alerts > 0 ? "bg-chart-5/10" : "bg-chart-2/10",
    },
    {
      label: "Revenue (Mar)",
      value: `€${(kpis.revenue_this_month / 1000).toFixed(0)}k`,
      detail: `${revenueChange >= 0 ? "+" : ""}${revenueChange.toFixed(1)}% vs Feb`,
      icon: TrendingUp,
      color: "text-chart-1",
      bg: "bg-chart-1/10",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <Card key={card.label} className="border-border/50 hover:border-border transition-colors">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  {card.label}
                </p>
                <p className="text-2xl font-bold tracking-tight">{card.value}</p>
                <p className="text-xs text-muted-foreground">{card.detail}</p>
              </div>
              <div className={`${card.bg} p-2.5 rounded-lg`}>
                <card.icon className={`h-5 w-5 ${card.color}`} />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
