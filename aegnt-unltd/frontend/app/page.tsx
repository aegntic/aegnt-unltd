"use client";

import { useState } from "react";

interface Response {
  id: string;
  content: string;
  system: "cortex" | "deep";
  latency_ms: number;
  reasoning_trace?: string;
}

const suggestions = [
  { label: "Connect to GitHub repo", icon: "⇪" },
  { label: "Open local file", icon: "◈" },
  { label: "Search the web", icon: "◎" },
  { label: "Create a new project", icon: "◇" },
];

export default function Home() {
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [responses, setResponses] = useState<Response[]>([]);

  const handleSubmit = async () => {
    if (!input.trim()) return;

    setIsThinking(true);
    const inputText = input;
    setInput("");

    try {
      const res = await fetch("http://localhost:8000/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input: inputText }),
      });

      const data = await res.json();

      setResponses((prev) => [
        {
          id: Date.now().toString(),
          content: data.content,
          system: data.system === "cortex" ? "cortex" : "deep",
          latency_ms: data.latency_ms,
          reasoning_trace: data.reasoning_trace,
        },
        ...prev,
      ]);
    } catch (err) {
      const isStrategy =
        inputText.toLowerCase().includes("plan") ||
        inputText.toLowerCase().includes("strategy") ||
        inputText.toLowerCase().includes("build") ||
        inputText.toLowerCase().includes("create");

      setResponses((prev) => [
        {
          id: Date.now().toString(),
          content: isStrategy
            ? `[DEEP] Strategic analysis for: ${inputText}\n\nAnalyzing your request... This requires multi-step reasoning.`
            : `[CORTEX] Quick response: ${inputText}`,
          system: isStrategy ? "deep" : "cortex",
          latency_ms: isStrategy ? 450 : 45,
          reasoning_trace: isStrategy
            ? "1. Intent classified as Strategy\n2. Retrieving knowledge\n3. Generating plan"
            : undefined,
        },
        ...prev,
      ]);
    }

    setIsThinking(false);
  };

  const handleSuggestion = (suggestion: string) => {
    setInput(suggestion);
  };

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <span className="logo-text">◈ AEGNT-UNLTD</span>
        </div>
        <div className="status-badge">
          <span className="status-dot" />
          <span>Local Mode</span>
        </div>
      </header>

      <main className="main">
        <div className="input-panel">
          <div className="input-section">
            <div className="input-label">Directive</div>
            <textarea
              className="input-field"
              rows={4}
              placeholder="What would you like me to help with?"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && e.metaKey) {
                  handleSubmit();
                }
              }}
            />
          </div>

          <div className="input-section">
            <button
              className="send-btn"
              onClick={handleSubmit}
              disabled={isThinking}
            >
              {isThinking ? "◌ Processing..." : "Send Directive ⌘↵"}
            </button>
          </div>

          <div className="response-area">
            {responses.map((resp) => (
              <div
                key={resp.id}
                className={`response-block ${resp.system === "deep" ? "deep" : ""}`}
              >
                <div className="response-header">
                  <span className={`response-system ${resp.system}`}>
                    {resp.system === "cortex" ? "◉ CORTEX" : "◎ DEEP MIND"}
                  </span>
                  <span className="response-latency">{resp.latency_ms}ms</span>
                </div>
                <div className="response-content">{resp.content}</div>
                {resp.reasoning_trace && (
                  <div className="reasoning-trace">
                    <pre>{resp.reasoning_trace}</pre>
                  </div>
                )}
              </div>
            ))}

            {responses.length === 0 && (
              <div className="suggestions">
                <div className="suggestions-label">Get started</div>
                <div className="suggestions-list">
                  {suggestions.map((s, i) => (
                    <button
                      key={i}
                      className="suggestion-btn"
                      onClick={() => handleSuggestion(s.label)}
                    >
                      <span className="suggestion-icon">{s.icon}</span>
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
