"use client";

import { useState } from "react";
import { askAssistant } from "@/lib/apiClient";
import type { DecisionResponse } from "@/types/api";

interface ChatMessage {
  role: "user" | "ai";
  html: string;
  tag?: string;
}

interface TraceStep {
  icon: string;
  name: string;
  text: string;
}

const PRESETS = [
  "Should I leave for work now?",
  "Is it safe to jog outside this evening?",
  "Will there be flooding near my area today?",
];

function buildTraceSteps(res: DecisionResponse): TraceStep[] {
  const env = res.environment as Record<string, any>;
  return [
    {
      icon: "🧭",
      name: "Planner Agent",
      text: `Parsed intent: <b>${res.intent.replace(/_/g, " ")}</b>. Dispatching parallel data-gathering agents.`,
    },
    {
      icon: "🚦",
      name: "Traffic Agent",
      text: `Current conditions: <b>${res.traffic.level}</b>, ~${res.traffic.avg_delay_min} min average delay. (source: ${res.traffic.source})`,
    },
    {
      icon: "🌤️",
      name: "Environment Agent",
      text: `AQI / weather snapshot: <b>${JSON.stringify(env)}</b>`,
    },
    {
      icon: "🔮",
      name: "Prediction Agent",
      text: `Flood risk trending <b>${res.prediction.risk}</b> (confidence ${(res.prediction.confidence * 100).toFixed(0)}%). ${res.prediction.rationale}`,
    },
    {
      icon: "📊",
      name: "Risk Score Agent",
      text: `Weighted score → AQI ${res.risk.components.aqi_risk} · Traffic ${res.risk.components.traffic_risk} · Flood ${res.risk.components.flood_risk} → composite <b>${res.risk.composite}</b>`,
    },
    {
      icon: "✅",
      name: "Recommendation Agent",
      text: "Synthesizing final, explainable recommendation for the user.",
    },
  ];
}

export function AssistantView() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "ai",
      tag: "Recommendation Agent",
      html:
        'Hi, I\'m your UrbanPulse decision assistant. Ask me things like <i>"Should I leave for work now?"</i> or <i>"Is it safe to walk to the market?"</i> — I\'ll pull live traffic, weather, AQI and risk data before answering.',
    },
  ]);
  const [input, setInput] = useState("");
  const [traceSteps, setTraceSteps] = useState<TraceStep[]>([]);
  const [decision, setDecision] = useState<DecisionResponse | null>(null);
  const [isThinking, setIsThinking] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function sendQuestion(question: string) {
    if (!question.trim() || isThinking) return;
    setMessages((prev) => [...prev, { role: "user", html: question }]);
    setInput("");
    setIsThinking(true);
    setErrorMsg(null);
    setTraceSteps([]);
    setDecision(null);

    try {
      const res = await askAssistant({ question, session_id: "web-session" });
      const steps = buildTraceSteps(res);
      steps.forEach((step, i) => {
        setTimeout(() => setTraceSteps((prev) => [...prev, step]), i * 380);
      });
      setTimeout(() => {
        setDecision(res);
        setMessages((prev) => [
          ...prev,
          {
            role: "ai",
            tag:
              res.intent === "flood_risk"
                ? "Prediction + Recommendation Agent"
                : res.intent === "outdoor_safety"
                ? "Environment + Recommendation Agent"
                : "Recommendation Agent",
            html: `<b>${res.recommendation.verdict}</b><br/><br/>${res.recommendation.reason}<br/><br/><span style="color:var(--muted); font-size:12px;">Explainability: this combines live Traffic, Environment and Prediction agent outputs, weighted by the Risk Score Agent — nothing is a black box.</span>`,
          },
        ]);
      }, steps.length * 380 + 300);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "The assistant is unavailable right now.");
    } finally {
      setIsThinking(false);
    }
  }

  const riskColor = decision
    ? decision.risk.composite > 65
      ? "var(--red)"
      : decision.risk.composite > 35
      ? "var(--amber)"
      : "var(--pulse)"
    : "var(--pulse)";

  return (
    <section className="animate-fadeIn">
      <div className="section-title">
        Ask the AI Decision Assistant <div className="line" />
      </div>
      <div className="grid min-h-[520px] grid-cols-1 gap-4 lg:h-[calc(100vh-230px)] lg:grid-cols-[1.6fr_1fr]">
        <div className="flex flex-col overflow-hidden rounded-panel border border-border bg-panel">
          <div className="flex flex-1 flex-col gap-3.5 overflow-y-auto p-5">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`max-w-[78%] rounded-2xl px-4 py-3 text-[13.5px] leading-relaxed ${
                  m.role === "user"
                    ? "self-end rounded-br-[4px] bg-pulse font-medium text-[#04140F]"
                    : "self-start rounded-bl-[4px] border border-border bg-panel2"
                }`}
              >
                {m.tag && (
                  <div className="mb-1.5 font-mono text-[10px] uppercase tracking-wide text-pulse">{m.tag}</div>
                )}
                <span dangerouslySetInnerHTML={{ __html: m.html }} />
              </div>
            ))}
            {isThinking && <div className="text-xs text-muted">Assistant is reasoning through live signals…</div>}
            {errorMsg && <div className="text-xs text-red">{errorMsg}</div>}
          </div>
          <div className="flex flex-wrap gap-2 px-5 pb-3.5">
            {PRESETS.map((p) => (
              <button
                key={p}
                onClick={() => sendQuestion(p)}
                className="rounded-full border border-border bg-panel2 px-3 py-1.5 text-xs text-muted hover:border-pulse hover:text-text"
              >
                {p}
              </button>
            ))}
          </div>
          <div className="flex gap-2.5 border-t border-border p-4">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendQuestion(input)}
              placeholder="Ask a question about the city right now…"
              className="flex-1 rounded-[10px] border border-border bg-panel2 px-3.5 py-3 text-[13.5px] outline-none focus:border-pulse"
            />
            <button
              onClick={() => sendQuestion(input)}
              className="rounded-[10px] bg-pulse px-4.5 font-bold text-[13px] text-[#04140F]"
            >
              Ask →
            </button>
          </div>
        </div>

        <div className="overflow-y-auto rounded-panel border border-border bg-panel p-4.5">
          <h3 className="mb-4 font-display text-sm font-semibold">🧠 Multi-Agent Reasoning</h3>
          {traceSteps.length === 0 && !decision && (
            <div className="text-[13px] text-muted">
              Ask a question to see the Planner → Traffic → Environment → Prediction → Risk Score →
              Recommendation agent pipeline reason through it in real time, with a transparent risk score.
            </div>
          )}
          {traceSteps.map((step, i) => (
            <div key={i} className="mb-3.5 flex animate-fadeIn gap-2.5">
              <div className="flex h-6.5 w-6.5 flex-shrink-0 items-center justify-center rounded-[7px] border border-border bg-panel2 text-[13px]">
                {step.icon}
              </div>
              <div className="text-[12.5px]">
                <b className="block text-[12.5px]">{step.name}</b>
                <span
                  className="leading-snug text-muted"
                  dangerouslySetInnerHTML={{ __html: step.text }}
                />
              </div>
            </div>
          ))}
          {decision && (
            <div className="mt-1.5 text-center">
              <div className="font-mono text-[11.5px] uppercase tracking-wide text-muted">
                Composite Decision Risk
              </div>
              <div className="font-display text-[38px] font-bold" style={{ color: riskColor }}>
                {decision.risk.composite}
              </div>
              <div className="my-2.5 h-2 overflow-hidden rounded-md bg-panel2">
                <div
                  className="h-full rounded-md transition-all duration-500"
                  style={{ width: `${decision.risk.composite}%`, background: riskColor }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
