"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type ProductionOrder } from "@/lib/api";

const statusColors: Record<string, string> = {
  in_progress: "bg-chart-1/15 text-chart-1 border-chart-1/30",
  planned: "bg-chart-3/15 text-chart-3 border-chart-3/30",
  completed: "bg-chart-2/15 text-chart-2 border-chart-2/30",
};

const priorityLabels: Record<string, string> = {
  high: "🔴",
  normal: "🟡",
  low: "🟢",
};

export function ProductionOrdersTable() {
  const [orders, setOrders] = useState<ProductionOrder[]>([]);

  useEffect(() => {
    api.getProductionOrders().then((d) => setOrders(d.production_orders)).catch(() => {});
  }, []);

  return (
    <Card className="border-border/50">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
          Production Orders
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border/50">
                <th className="text-left py-2.5 px-4 text-xs font-medium text-muted-foreground uppercase">Product</th>
                <th className="text-left py-2.5 px-4 text-xs font-medium text-muted-foreground uppercase">Line</th>
                <th className="text-right py-2.5 px-4 text-xs font-medium text-muted-foreground uppercase">Qty</th>
                <th className="text-center py-2.5 px-4 text-xs font-medium text-muted-foreground uppercase">Status</th>
                <th className="text-center py-2.5 px-4 text-xs font-medium text-muted-foreground uppercase">Priority</th>
              </tr>
            </thead>
            <tbody>
              {orders.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-muted-foreground">Loading...</td>
                </tr>
              ) : (
                orders.map((order) => (
                  <tr key={order.id} className="border-b border-border/30 hover:bg-muted/30 transition-colors">
                    <td className="py-2.5 px-4 font-medium">{order.product}</td>
                    <td className="py-2.5 px-4 text-muted-foreground text-xs">{order.line}</td>
                    <td className="py-2.5 px-4 text-right font-mono text-xs">
                      {order.quantity.toLocaleString()}
                    </td>
                    <td className="py-2.5 px-4 text-center">
                      <Badge
                        variant="outline"
                        className={`text-[10px] font-medium ${statusColors[order.status] || ""}`}
                      >
                        {order.status.replace("_", " ")}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-4 text-center text-xs">
                      {priorityLabels[order.priority] || order.priority}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
