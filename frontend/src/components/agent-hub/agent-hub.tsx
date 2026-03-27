"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Bot,
  TrendingUp,
  ShieldCheck,
  Package,
  ArrowDown,
  Zap,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Send,
  Database,
  Wrench,
  Rocket,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AgentEvent {
  timestamp: number;
  time_str: string;
  event_type: string;
  agent: string;
  detail: string;
  elapsed: number | null;
}

interface AgentStatus {
  name: string;
  label: string;
  description: string;
  icon: typeof TrendingUp;
  color: string;
  borderColor: string;
  bgColor: string;
  status: "idle" | "working" | "done" | "error";
}

export function AgentHub() {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [agentStatuses, setAgentStatuses] = useState<Record<string, "idle" | "working" | "done" | "error">>({
    DemandForecaster: "idle",
    QualityInspector: "idle",
    SupplyChainMgr: "idle",
  });
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<{ role: string; content: string }[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const eventsEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Connect to SSE event stream
  useEffect(() => {
    // Load existing events
    fetch(`${API_BASE}/api/events`)
      .then((r) => r.json())
      .then((d) => setEvents(d.events || []))
      .catch(() => {});

    // Subscribe to live events
    const es = new EventSource(`${API_BASE}/api/events/stream`);
    eventSourceRef.current = es;

    es.onmessage = (e) => {
      try {
        const event: AgentEvent = JSON.parse(e.data);
        setEvents((prev) => [...prev.slice(-100), event]);

        // Update agent status
        if (event.event_type === "agent_start") {
          setAgentStatuses((prev) => ({ ...prev, [event.agent]: "working" }));
        } else if (event.event_type === "agent_end") {
          setAgentStatuses((prev) => ({ ...prev, [event.agent]: "done" }));
          // Reset to idle after 5s
          setTimeout(() => {
            setAgentStatuses((prev) => ({ ...prev, [event.agent]: "idle" }));
          }, 5000);
        } else if (event.event_type === "action_executed") {
          // Show toast for actions
          const detail = event.detail || "";
          if (detail.includes("Purchase Order")) {
            toast.success(detail, { description: "Purchase order created in SAP" });
          } else if (detail.includes("Production Order")) {
            toast.success(detail, { description: "Production run scheduled" });
          } else if (detail.includes("Notification")) {
            toast.info(detail, { description: "Notification dispatched" });
          } else {
            toast.success(detail);
          }
        } else if (event.event_type === "error") {
          setAgentStatuses((prev) => ({ ...prev, [event.agent]: "error" }));
        }
      } catch {}
    };

    return () => {
      es.close();
    };
  }, []);

  // Auto-scroll events
  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  const sendMessage = useCallback(async () => {
    if (!chatInput.trim() || isProcessing) return;
    const msg = chatInput.trim();
    setChatInput("");
    setChatMessages((prev) => [...prev, { role: "user", content: msg }]);
    setIsProcessing(true);

    try {
      const res = await fetch(`${API_BASE}/agent`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify({ messages: [{ role: "user", content: msg }] }),
      });

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let assistantMsg = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const evt = JSON.parse(line.slice(6));
                if (evt.type === "TEXT_MESSAGE_CONTENT" && evt.delta) {
                  assistantMsg += evt.delta;
                }
              } catch {}
            }
          }
        }
      }

      if (assistantMsg) {
        setChatMessages((prev) => [...prev, { role: "assistant", content: assistantMsg }]);
      }
    } catch (err) {
      setChatMessages((prev) => [...prev, { role: "assistant", content: "Error communicating with the agent." }]);
    } finally {
      setIsProcessing(false);
    }
  }, [chatInput, isProcessing]);

  const agents: AgentStatus[] = [
    {
      name: "DemandForecaster",
      label: "Demand Forecaster",
      description: "Sales & demand analysis",
      icon: TrendingUp,
      color: "text-blue-400",
      borderColor: "border-blue-500/40",
      bgColor: "bg-blue-500/5",
      status: agentStatuses.DemandForecaster,
    },
    {
      name: "QualityInspector",
      label: "Quality Inspector",
      description: "Production quality monitoring",
      icon: ShieldCheck,
      color: "text-emerald-400",
      borderColor: "border-emerald-500/40",
      bgColor: "bg-emerald-500/5",
      status: agentStatuses.QualityInspector,
    },
    {
      name: "SupplyChainMgr",
      label: "Supply Chain Mgr",
      description: "Inventory & procurement",
      icon: Package,
      color: "text-amber-400",
      borderColor: "border-amber-500/40",
      bgColor: "bg-amber-500/5",
      status: agentStatuses.SupplyChainMgr,
    },
  ];

  const getEventIcon = (type: string) => {
    switch (type) {
      case "agent_start": return <Zap className="h-3 w-3 text-blue-400" />;
      case "agent_end": return <CheckCircle2 className="h-3 w-3 text-emerald-400" />;
      case "tool_call": return <Database className="h-3 w-3 text-cyan-400" />;
      case "tool_result": return <Wrench className="h-3 w-3 text-violet-400" />;
      case "action_executed": return <Rocket className="h-3 w-3 text-orange-400" />;
      case "error": return <AlertCircle className="h-3 w-3 text-red-400" />;
      default: return <Zap className="h-3 w-3 text-muted-foreground" />;
    }
  };

  const getEventBorderColor = (type: string) => {
    switch (type) {
      case "agent_start": return "border-blue-500/30";
      case "agent_end": return "border-emerald-500/30";
      case "tool_call": return "border-cyan-500/20";
      case "tool_result": return "border-violet-500/20";
      case "action_executed": return "border-orange-500/40";
      case "error": return "border-red-500/30";
      default: return "border-primary/20";
    }
  };

  const getAgentColor = (agent: string) => {
    if (agent.includes("Demand")) return "text-blue-400";
    if (agent.includes("Quality")) return "text-emerald-400";
    if (agent.includes("Supply")) return "text-amber-400";
    if (agent === "System") return "text-orange-400";
    return "text-muted-foreground";
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Chat */}
        <div className="lg:col-span-2">
          <Card className="border-border/50 h-[500px] flex flex-col">
            <CardHeader className="pb-2 shrink-0">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Bot className="h-4 w-4 text-primary" />
                  <CardTitle className="text-sm font-semibold">AI Agent Chat</CardTitle>
                </div>
                <Badge variant="outline" className="text-[9px]">Orchestrator</Badge>
              </div>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col min-h-0 p-0">
              {/* Messages */}
              <div className="flex-1 overflow-y-auto px-4 py-2 space-y-3">
                {chatMessages.length === 0 && (
                  <p className="text-xs text-muted-foreground text-center py-8">
                    Ask the orchestrator agent anything. Watch the Agent Orchestration panel to see which specialists get invoked.
                  </p>
                )}
                {chatMessages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div className={`max-w-[85%] rounded-lg px-3 py-2 text-xs ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted/50 border border-border/50"
                    }`}>
                      {msg.role === "user" ? (
                        <div className="whitespace-pre-wrap">{msg.content}</div>
                      ) : (
                        <div className="prose prose-xs prose-invert max-w-none [&_p]:my-1 [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:mt-3 [&_h3]:mb-1 [&_h2]:text-sm [&_h2]:font-bold [&_h2]:mt-3 [&_h2]:mb-1 [&_ul]:my-1 [&_ol]:my-1 [&_li]:my-0.5 [&_strong]:text-foreground [&_p]:text-muted-foreground [&_li]:text-muted-foreground">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {isProcessing && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    Agent is thinking...
                  </div>
                )}
              </div>
              {/* Input */}
              <div className="shrink-0 border-t border-border/30 p-3">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                    placeholder="Ask the AI agent..."
                    className="flex-1 bg-muted/30 border border-border/50 rounded-lg px-3 py-2 text-xs placeholder:text-muted-foreground/50 focus:outline-none focus:border-primary/50"
                  />
                  <Button size="sm" onClick={sendMessage} disabled={isProcessing || !chatInput.trim()}>
                    <Send className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right: Orchestration + Activity */}
        <div className="space-y-6">
          {/* Orchestration Visualization */}
          <Card className="border-border/50">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <Bot className="h-4 w-4 text-primary" />
                <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                  Agent Orchestration
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Orchestrator node */}
              <div className="flex flex-col items-center">
                <div className="p-3 rounded-full bg-primary/10 border-2 border-primary/30">
                  <Bot className="h-6 w-6 text-primary" />
                </div>
                <p className="text-xs font-semibold mt-1.5">Orchestrator</p>
                <p className="text-[9px] text-muted-foreground">Coordinates all agents</p>
                <div className="w-px h-5 bg-border/50 mt-2" />
                <ArrowDown className="h-3 w-3 text-muted-foreground -mt-1" />
              </div>

              {/* Specialist agents */}
              <div className="grid grid-cols-3 gap-2">
                {agents.map((agent) => (
                  <div
                    key={agent.name}
                    className={`flex flex-col items-center p-3 rounded-lg border-2 transition-all ${
                      agent.status === "working"
                        ? `${agent.borderColor} ${agent.bgColor} shadow-lg`
                        : agent.status === "done"
                        ? "border-emerald-500/30 bg-emerald-500/5"
                        : "border-border/30 bg-muted/5"
                    }`}
                  >
                    <div className={`p-2 rounded-lg ${agent.status === "working" ? agent.bgColor : "bg-muted/20"}`}>
                      {agent.status === "working" ? (
                        <Loader2 className={`h-4 w-4 ${agent.color} animate-spin`} />
                      ) : (
                        <agent.icon className={`h-4 w-4 ${agent.status === "idle" ? "text-muted-foreground" : agent.color}`} />
                      )}
                    </div>
                    <p className="text-[10px] font-semibold mt-1.5 text-center leading-tight">{agent.label}</p>
                    <p className="text-[8px] text-muted-foreground text-center mt-0.5">{agent.description}</p>
                    <div className="flex items-center gap-1 mt-1.5">
                      <span className={`w-1.5 h-1.5 rounded-full ${
                        agent.status === "working" ? "bg-blue-400 animate-pulse" :
                        agent.status === "done" ? "bg-emerald-400" :
                        agent.status === "error" ? "bg-red-400" :
                        "bg-muted-foreground/30"
                      }`} />
                      <span className="text-[8px] text-muted-foreground capitalize">{agent.status === "working" ? "Active" : agent.status === "done" ? "Done" : "Idle"}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Activity Feed */}
          <Card className="border-border/50">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                    Agent Activity
                  </CardTitle>
                </div>
                <span className="text-[10px] text-muted-foreground">{events.length} events</span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-[250px] overflow-y-auto space-y-0 pr-1">
                {events.length === 0 ? (
                  <p className="text-xs text-muted-foreground text-center py-8">No activity yet. Send a message to the agent to see events here.</p>
                ) : (
                  events.map((event, i) => (
                    <div key={i} className={`flex items-start gap-2 py-1.5 border-l-2 ${getEventBorderColor(event.event_type)} pl-3 ml-1 ${
                      event.event_type === "tool_call" || event.event_type === "tool_result" ? "ml-4" : ""
                    }`}>
                      {getEventIcon(event.event_type)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className={`text-[10px] font-semibold ${getAgentColor(event.agent)}`}>
                            {event.agent}
                          </span>
                          {event.elapsed != null && (
                            <span className="text-[9px] text-muted-foreground font-mono">{event.elapsed.toFixed(1)}s</span>
                          )}
                        </div>
                        <p className={`text-[10px] text-muted-foreground ${event.event_type === "tool_call" || event.event_type === "tool_result" ? "font-mono" : ""}`} style={{ overflowWrap: "anywhere" }}>
                          {event.detail}
                        </p>
                        <span className="text-[9px] text-muted-foreground/60">{event.time_str}</span>
                      </div>
                    </div>
                  ))
                )}
                <div ref={eventsEndRef} />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
