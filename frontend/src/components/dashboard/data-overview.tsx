"use client";

import { Card, CardContent } from "@/components/ui/card";
import {
  Database,
  ShoppingCart,
  Factory as FactoryIcon,
  Package,
  Users,
  FileText,
  Candy,
} from "lucide-react";

const DATA_POINTS = [
  { icon: Candy, label: "Products", value: "27", detail: "confectionery SKUs" },
  { icon: ShoppingCart, label: "Sales Records", value: "21K+", detail: "24 months history" },
  { icon: FactoryIcon, label: "Production Lines", value: "5", detail: "choc / gummy / marzipan" },
  { icon: Package, label: "Raw Materials", value: "15", detail: "tracked with reorder" },
  { icon: Users, label: "Suppliers", value: "10", detail: "6 countries" },
  { icon: FileText, label: "Quality Docs", value: "6", detail: "SOPs & HACCP" },
];

export function DataOverview() {
  return (
    <Card className="border-border/50 bg-muted/10">
      <CardContent className="py-3 px-4">
        <div className="flex items-center gap-2 mb-2">
          <Database className="h-3.5 w-3.5 text-primary" />
          <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-widest">
            Sample Data Powering This Demo
          </span>
        </div>
        <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
          {DATA_POINTS.map((d) => (
            <div key={d.label} className="flex items-center gap-2">
              <div className="shrink-0 p-1.5 rounded-md bg-primary/5 border border-primary/10">
                <d.icon className="h-3 w-3 text-primary/70" />
              </div>
              <div>
                <p className="text-sm font-bold leading-none">{d.value}</p>
                <p className="text-[9px] text-muted-foreground leading-tight mt-0.5">{d.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
