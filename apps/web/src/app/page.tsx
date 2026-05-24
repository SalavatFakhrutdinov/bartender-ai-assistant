"use client";

import { useState } from "react";

export default function Home() {
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([
    { role: "assistant", content: "🍸 Welcome to Bartender AI! I'm your personal cocktail assistant. Try typing a flavor profile or ask for a recipe." },
  ]);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    setMessages((prev) => [...prev, { role: "user", content: input }]);
    // Stub: echo back for Phase 0
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "🤖 This is a Phase 0 stub. Full chat integration coming in Phase 1!" },
      ]);
    }, 500);
    setInput("");
  };

  return (
    <main className="flex h-screen flex-col bg-gray-50">
      {/* Header */}
      <header className="border-b bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold">🍸 Bartender AI Assistant</h1>
          <div className="flex gap-2">
            <span className="rounded-full bg-green-100 px-3 py-1 text-sm text-green-800">
              Phase 0
            </span>
          </div>
        </div>
      </header>

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-3xl space-y-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-white text-gray-900 shadow-sm"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Input area */}
      <div className="border-t bg-white p-4">
        <div className="mx-auto flex max-w-3xl gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Describe a cocktail you'd like..."
            className="flex-1 rounded-lg border border-gray-300 px-4 py-3 focus:border-blue-500 focus:outline-none"
          />
          <button
            onClick={handleSend}
            className="rounded-lg bg-blue-600 px-6 py-3 font-medium text-white hover:bg-blue-700"
          >
            Send
          </button>
        </div>
      </div>
    </main>
  );
}
