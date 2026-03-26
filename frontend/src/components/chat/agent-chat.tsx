"use client";

import { CopilotChat } from "@copilotkit/react-ui";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Bot, Sparkles } from "lucide-react";

export function AgentChat() {
  return (
    <Card className="border-border/50 flex flex-col h-full">
      <CardHeader className="pb-2 shrink-0">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-primary/10">
            <Bot className="h-4 w-4 text-primary" />
          </div>
          <div>
            <CardTitle className="text-sm font-semibold">Manufacturing Intelligence</CardTitle>
            <p className="text-[10px] text-muted-foreground flex items-center gap-1">
              <Sparkles className="h-2.5 w-2.5" />
              Powered by GPT-5 via Azure AI Foundry
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col p-0 min-h-0">
        <div className="px-4 pb-3 space-y-1.5">
          <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Try asking</p>
          <div className="grid grid-cols-2 gap-1.5">
            {[
              "🐰 200K Easter bunnies by April — can we deliver?",
              "🌡️ Quality on Chocolate Line 2?",
              "📦 Which materials need reordering?",
              "📊 Christmas 2024 vs 2025 trends?",
            ].map((s) => (
              <p
                key={s}
                className="text-[10px] text-muted-foreground bg-muted/30 rounded px-2 py-1.5 border border-border/30"
              >
                {s}
              </p>
            ))}
          </div>
        </div>
        <div className="flex-1 min-h-0">
          <CopilotChat
            className="h-full"
            labels={{
              initial: "Hello! I'm your Manufacturing Intelligence assistant. I coordinate three specialist agents — **Demand Forecasting**, **Quality Control**, and **Supply Chain** — to help you make data-driven decisions.\n\nCopy one of the scenarios above, or ask me anything!",
              placeholder: "Ask about demand, quality, or supply chain...",
              title: "",
            }}
          />
        </div>
      </CardContent>
    </Card>
  );
}
