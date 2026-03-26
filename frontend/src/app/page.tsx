"use client";

import { KPICards } from "@/components/dashboard/kpi-cards";
import { SalesTrendChart, InventoryChart, QualityLinesMonitor } from "@/components/dashboard/charts";
import { ProductionOrdersTable } from "@/components/dashboard/production-orders";
import { ConnectedToolsPanel } from "@/components/tools-panel/connected-tools";
import { AgentChat } from "@/components/chat/agent-chat";
import { PipelineAnalysis } from "@/components/pipeline/pipeline-analysis";
import { DataOverview } from "@/components/dashboard/data-overview";
import { AgentHub } from "@/components/agent-hub/agent-hub";
import { Factory, Sun, Moon, LayoutDashboard, Bot } from "lucide-react";
import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";

type TabId = "dashboard" | "agent-hub";

export default function Home() {
  const [isDark, setIsDark] = useState(true);
  const [activeTab, setActiveTab] = useState<TabId>("dashboard");
  const [investigateQuery, setInvestigateQuery] = useState<string | null>(null);

  const toggleTheme = () => {
    setIsDark(!isDark);
    document.documentElement.classList.toggle("dark");
  };

  const handleInvestigate = useCallback((lineName: string) => {
    setInvestigateQuery(`Quality metrics on ${lineName} show warnings. What is happening? Check for anomalies, search SOPs, and recommend corrective actions.`);
    setActiveTab("agent-hub");
  }, []);

  const tabs = [
    { id: "dashboard" as TabId, label: "Dashboard", icon: LayoutDashboard },
    { id: "agent-hub" as TabId, label: "Agent Hub", icon: Bot },
  ];

  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="border-b border-border/50 bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-1.5 rounded-lg bg-primary/10 border border-primary/20">
              <Factory className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-tight">Smart Factory Intelligence</h1>
              <p className="text-[10px] text-muted-foreground">
                Multi-Agent Manufacturing PoC &middot; Azure AI Foundry
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            {/* Tab navigation */}
            <div className="flex items-center bg-muted/30 rounded-lg p-0.5 mr-3">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                    activeTab === tab.id
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <tab.icon className="h-3.5 w-3.5" />
                  {tab.label}
                </button>
              ))}
            </div>
            <span className="text-[10px] text-muted-foreground font-mono bg-muted/50 px-2 py-1 rounded">
              agent-framework + AG-UI
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={toggleTheme}
            >
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-[1600px] mx-auto w-full px-6 py-6">
        {activeTab === "dashboard" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left column: Dashboard */}
            <div className="lg:col-span-2 space-y-6">
              <KPICards />
              <DataOverview />
              <SalesTrendChart />
              <PipelineAnalysis />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <InventoryChart />
                <QualityLinesMonitor onInvestigate={handleInvestigate} />
              </div>
              <ProductionOrdersTable />
            </div>

            {/* Right column: Chat + Tools */}
            <div className="space-y-6">
              <div className="h-[600px]">
                <AgentChat />
              </div>
              <ConnectedToolsPanel />
            </div>
          </div>
        )}

        {activeTab === "agent-hub" && (
          <AgentHub />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-border/30 py-3">
        <div className="max-w-[1600px] mx-auto px-6 flex items-center justify-between text-[10px] text-muted-foreground">
          <span>Manufacturing Intelligence PoC &middot; Microsoft Agent Framework &middot; Azure AI Foundry</span>
          <span className="font-mono">GPT-5 &middot; GPT-5-mini &middot; text-embedding-large</span>
        </div>
      </footer>
    </div>
  );
}
