"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type ConnectedTool } from "@/lib/api";
import {
  Database,
  FileSearch,
  Activity,
  Package,
  Brain,
  CheckCircle2,
  Plug,
} from "lucide-react";

const iconMap: Record<string, typeof Database> = {
  database: Database,
  "file-search": FileSearch,
  activity: Activity,
  package: Package,
  brain: Brain,
};

export function ConnectedToolsPanel() {
  const [tools, setTools] = useState<ConnectedTool[]>([]);

  useEffect(() => {
    api.getToolsStatus().then((d) => setTools(d.connected_tools)).catch(() => {});
  }, []);

  return (
    <Card className="border-border/50">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Plug className="h-4 w-4 text-muted-foreground" />
          <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
            Connected Tools & MCP Servers
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-2.5">
        {tools.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground text-sm">Loading...</div>
        ) : (
          tools.map((tool) => {
            const Icon = iconMap[tool.icon] || Database;
            return (
              <div
                key={tool.id}
                className="flex items-start gap-3 p-3 rounded-lg bg-muted/30 border border-border/30 hover:border-border/60 transition-colors"
              >
                <div className="shrink-0 mt-0.5 p-2 rounded-md bg-chart-2/10">
                  <Icon className="h-4 w-4 text-chart-2" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm">{tool.name}</span>
                    <Badge
                      variant="outline"
                      className="text-[9px] bg-chart-2/10 text-chart-2 border-chart-2/30"
                    >
                      <CheckCircle2 className="h-2.5 w-2.5 mr-0.5" />
                      {tool.status}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">{tool.description}</p>
                  <div className="flex items-center gap-3 mt-1.5">
                    <span className="text-[10px] text-muted-foreground font-mono">
                      {tool.type}
                    </span>
                    <span className="text-[10px] text-muted-foreground">
                      {tool.tools_count} tool{tool.tools_count !== 1 ? "s" : ""}
                    </span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}
