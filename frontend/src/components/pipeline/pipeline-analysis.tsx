"use client";

import { useState, useRef, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Play,
  CheckCircle2,
  XCircle,
  Loader2,
  TrendingUp,
  Package,
  ShieldCheck,
  FileText,
  Clock,
  ChevronDown,
  ChevronRight,
  Rocket,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface StepData {
  step: string;
  label: string;
  description: string;
  status: "pending" | "running" | "complete" | "error" | "approved" | "rejected";
  result?: string;
  elapsed?: number;
  error?: string;
  requires_approval?: boolean;
  approval_question?: string;
}

const STEP_ICONS: Record<string, typeof TrendingUp> = {
  demand: TrendingUp,
  supply: Package,
  quality: ShieldCheck,
  summary: FileText,
};

const STEP_COLORS: Record<string, string> = {
  demand: "text-blue-400",
  supply: "text-amber-400",
  quality: "text-emerald-400",
  summary: "text-violet-400",
};

export function PipelineAnalysis() {
  const [isRunning, setIsRunning] = useState(false);
  const [pipelineId, setPipelineId] = useState<string | null>(null);
  const [pipelineTitle, setPipelineTitle] = useState("");
  const [steps, setSteps] = useState<StepData[]>([]);
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const [totalElapsed, setTotalElapsed] = useState<number | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const toggleExpand = (step: string) => {
    setExpandedSteps(prev => {
      const next = new Set(prev);
      if (next.has(step)) next.delete(step);
      else next.add(step);
      return next;
    });
  };

  const startPipeline = useCallback(async () => {
    setIsRunning(true);
    setIsComplete(false);
    setTotalElapsed(null);
    setSteps([]);
    setExpandedSteps(new Set());

    abortRef.current = new AbortController();

    try {
      const res = await fetch(`${API_BASE}/api/pipeline/easter-rush?quantity=200000`, {
        signal: abortRef.current.signal,
      });

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      if (!reader) return;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let eventType = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith("data: ") && eventType) {
            try {
              const data = JSON.parse(line.slice(6));
              handleSSEEvent(eventType, data);
            } catch {}
            eventType = "";
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== "AbortError") {
        console.error("Pipeline error:", err);
      }
    } finally {
      setIsRunning(false);
    }
  }, []);

  const handleSSEEvent = (event: string, data: Record<string, unknown>) => {
    switch (event) {
      case "pipeline_start":
        setPipelineId(data.id as string);
        setPipelineTitle(data.title as string);
        const stepNames = data.steps as string[];
        setSteps(stepNames.map(s => ({
          step: s,
          label: "",
          description: "",
          status: "pending",
        })));
        break;

      case "step_start":
        setSteps(prev => prev.map(s =>
          s.step === data.step ? { ...s, status: "running" as const, label: data.label as string, description: data.description as string } : s
        ));
        break;

      case "step_complete":
        setSteps(prev => prev.map(s =>
          s.step === data.step ? {
            ...s,
            status: "complete" as const,
            result: data.result as string,
            elapsed: data.elapsed as number,
            requires_approval: data.requires_approval as boolean,
            approval_question: data.approval_question as string | undefined,
          } : s
        ));
        // Only show latest completed step expanded
        setExpandedSteps(new Set([data.step as string]));
        break;

      case "step_error":
        setSteps(prev => prev.map(s =>
          s.step === data.step ? { ...s, status: "error" as const, error: data.error as string } : s
        ));
        break;

      case "pipeline_complete":
        setTotalElapsed(data.total_elapsed as number);
        setIsComplete(true);
        break;
    }
  };

  const handleApprove = async (step: string) => {
    setSteps(prev => prev.map(s =>
      s.step === step ? { ...s, status: "approved" as const } : s
    ));
    if (pipelineId) {
      await fetch(`${API_BASE}/api/pipeline/approve/${pipelineId}/${step}`, { method: "POST" });
    }
  };

  const handleReject = async (step: string) => {
    setSteps(prev => prev.map(s =>
      s.step === step ? { ...s, status: "rejected" as const } : s
    ));
    if (pipelineId) {
      await fetch(`${API_BASE}/api/pipeline/reject/${pipelineId}/${step}`, { method: "POST" });
    }
  };

  return (
    <Card className="border-border/50">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Rocket className="h-4 w-4 text-primary" />
            <CardTitle className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
              Production Analysis Pipeline
            </CardTitle>
          </div>
          {!isRunning && !isComplete && (
            <Button size="sm" onClick={startPipeline} className="gap-1.5 text-xs">
              <Play className="h-3 w-3" />
              Run Easter Rush Analysis
            </Button>
          )}
          {isComplete && (
            <Button size="sm" variant="outline" onClick={startPipeline} className="gap-1.5 text-xs">
              <Play className="h-3 w-3" />
              Run Again
            </Button>
          )}
        </div>
        {pipelineTitle && (
          <p className="text-xs text-muted-foreground mt-1">{pipelineTitle}</p>
        )}
      </CardHeader>

      <CardContent className="space-y-0">
        {steps.length === 0 && !isRunning && (
          <div className="text-center py-8 text-muted-foreground">
            <Rocket className="h-8 w-8 mx-auto mb-3 opacity-30" />
            <p className="text-sm font-medium">Multi-Agent Analysis Pipeline</p>
            <p className="text-xs mt-1 max-w-sm mx-auto">
              Runs Demand, Supply Chain, and Quality agents in sequence. Review results and approve at each checkpoint.
            </p>
          </div>
        )}

        {steps.map((step, idx) => {
          const Icon = STEP_ICONS[step.step] || FileText;
          const color = STEP_COLORS[step.step] || "text-muted-foreground";
          const isExpanded = expandedSteps.has(step.step);

          return (
            <div key={step.step}>
              {idx > 0 && (
                <div className="flex justify-center py-1">
                  <div className={`w-px h-4 ${step.status === "pending" ? "bg-border/30" : "bg-border"}`} />
                </div>
              )}
              <div className={`rounded-lg border transition-colors overflow-hidden ${
                step.status === "running" ? "border-primary/40 bg-primary/5" :
                step.status === "approved" ? "border-emerald-500/30 bg-emerald-500/5" :
                step.status === "rejected" ? "border-red-500/30 bg-red-500/5" :
                step.status === "complete" ? "border-border/60 bg-muted/20" :
                step.status === "error" ? "border-red-500/40 bg-red-500/5" :
                "border-border/30 bg-transparent"
              }`}>
                {/* Step header */}
                <button
                  onClick={() => step.result && toggleExpand(step.step)}
                  className="w-full flex items-center gap-3 p-3 text-left"
                >
                  <div className={`shrink-0 ${color}`}>
                    {step.status === "running" ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : step.status === "approved" ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    ) : step.status === "rejected" ? (
                      <XCircle className="h-4 w-4 text-red-400" />
                    ) : step.status === "complete" ? (
                      <Icon className="h-4 w-4" />
                    ) : step.status === "error" ? (
                      <XCircle className="h-4 w-4 text-red-400" />
                    ) : (
                      <Icon className="h-4 w-4 opacity-30" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-medium ${step.status === "pending" ? "text-muted-foreground/50" : ""}`}>
                        {step.label || step.step}
                      </span>
                      {step.elapsed && (
                        <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
                          <Clock className="h-2.5 w-2.5" />
                          {step.elapsed}s
                        </span>
                      )}
                      {step.status === "running" && (
                        <Badge variant="outline" className="text-[9px] bg-primary/10 text-primary border-primary/30 animate-pulse">
                          running
                        </Badge>
                      )}
                    </div>
                    {step.description && step.status === "running" && (
                      <p className="text-[11px] text-muted-foreground mt-0.5">{step.description}</p>
                    )}
                  </div>
                  {step.result && (
                    <div className="shrink-0 text-muted-foreground">
                      {isExpanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                    </div>
                  )}
                </button>

                {/* Expanded result */}
                {isExpanded && step.result && (
                  <div className="px-3 pb-3 space-y-3">
                    <Separator className="bg-border/30" />
                    <div className="max-h-[250px] overflow-y-auto overscroll-contain">
                      <div className="text-xs text-muted-foreground whitespace-pre-wrap leading-relaxed font-mono pr-2">
                        {step.result}
                      </div>
                    </div>

                    {/* Approval buttons */}
                    {step.requires_approval && step.status === "complete" && (
                      <div className="space-y-2 pt-1 border-t border-border/20 mt-2">
                        <p className="text-xs font-medium text-foreground pt-2">{step.approval_question}</p>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            className="gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-700"
                            onClick={(e) => { e.stopPropagation(); handleApprove(step.step); }}
                          >
                            <CheckCircle2 className="h-3 w-3" />
                            Approve
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="gap-1.5 text-xs border-red-500/30 text-red-400 hover:bg-red-500/10"
                            onClick={(e) => { e.stopPropagation(); handleReject(step.step); }}
                          >
                            <XCircle className="h-3 w-3" />
                            Reject
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Pipeline complete */}
        {isComplete && totalElapsed && (
          <div className="mt-4 pt-3 border-t border-border/30 flex items-center justify-between text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              Analysis complete
            </span>
            <span className="flex items-center gap-1 font-mono">
              <Clock className="h-3 w-3" />
              {totalElapsed}s total
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
