"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { startSession, ask, sendSignal, endSession } from "@/lib/api";
import Nav from "@/components/Nav";

type Message = { role: "user" | "assistant"; text: string; interactionId?: string; topic?: string };

export default function LearnPage() {
  const params = useParams();
  const router = useRouter();
  const childId = params.id as string;
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [starting, setStarting] = useState(true);
  const [uiDirectives, setUiDirectives] = useState<Record<string, unknown>>({});
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!localStorage.getItem("access_token")) {
      router.replace("/login");
      return;
    }
    startSession(childId)
      .then((res) => {
        setSessionId(res.session_id);
        setUiDirectives(res.ui_directives || {});
      })
      .catch(() => setSessionId(""))
      .finally(() => setStarting(false));
  }, [childId, router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!sessionId || !input.trim() || loading) return;
    const text = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text }]);
    setLoading(true);
    try {
      const res = await ask(childId, sessionId, text);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: res.response_text,
          interactionId: res.interaction_id,
          topic: res.chunks_used?.[0]?.topic,
        },
      ]);
      if (Object.keys(res.ui_directives || {}).length) setUiDirectives((prev) => ({ ...prev, ...res.ui_directives }));
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Sorry, something went wrong. Try again or ask your grown-up for help." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function sendReaction(signalType: string, value: number) {
    if (!sessionId) return;
    try {
      await sendSignal(childId, sessionId, signalType, value);
    } catch {
      // ignore
    }
  }

  async function handleEndSession() {
    if (!sessionId) return;
    try {
      await endSession(sessionId);
    } catch {
      // ignore
    }
    router.push(`/dashboard/children/${childId}`);
  }

  if (starting) {
    return (
      <>
        <Nav />
        <main className="max-w-2xl mx-auto p-6 flex items-center justify-center min-h-[60vh]">
          <p className="text-slate-500 text-lg">Starting your learning session…</p>
        </main>
      </>
    );
  }

  if (!sessionId) {
    return (
      <>
        <Nav />
        <main className="max-w-2xl mx-auto p-6">
          <p className="text-red-600">Could not start session. Check you’re signed in and try again.</p>
          <Link href={`/dashboard/children/${childId}`} className="btn-big mt-4 inline-block bg-sky-500 text-white">
            Back to profile
          </Link>
        </main>
      </>
    );
  }

  return (
    <>
      <Nav />
      <main className="max-w-2xl mx-auto p-4 pb-32 flex flex-col min-h-screen">
        <div className="flex items-center justify-between mb-4">
          <Link href={`/dashboard/children/${childId}`} className="text-sky-600 font-medium hover:underline">
            ← Back
          </Link>
          <button
            onClick={handleEndSession}
            className="px-4 py-2 rounded-xl bg-slate-100 text-slate-700 hover:bg-slate-200 font-medium min-h-[44px]"
          >
            End session
          </button>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto">
          <div className="card-soft bg-mint-50 border-mint-200">
            <p className="text-slate-700">
              <strong>Hi!</strong> Ask me anything you’re learning. I’ll keep my answers short and friendly.
            </p>
          </div>
          {messages.map((m, i) => (
            <div
              key={i}
              className={`card-soft max-w-[90%] ${m.role === "user" ? "ml-0 mr-auto bg-sky-100 border-sky-200" : "mr-0 ml-auto bg-white"}`}
            >
              <p className="text-lg whitespace-pre-wrap">{m.text}</p>
              {m.role === "assistant" && (
                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="text-sm text-slate-500">How was that?</span>
                  <button
                    type="button"
                    onClick={() => sendReaction("EMOJI_REACTION", 1)}
                    className="px-3 py-1.5 rounded-xl bg-mint-100 hover:bg-mint-200 text-slate-700 font-medium min-h-[40px]"
                  >
                    Good
                  </button>
                  <button
                    type="button"
                    onClick={() => sendReaction("HINT_REQUESTED", 0.5)}
                    className="px-3 py-1.5 rounded-xl bg-peach-100 hover:bg-peach-200 text-slate-700 font-medium min-h-[40px]"
                  >
                    Need help
                  </button>
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="card-soft mr-0 ml-auto bg-white w-fit">
              <span className="text-slate-500">Thinking…</span>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={handleSend} className="fixed bottom-0 left-0 right-0 p-4 bg-sky-50 border-t border-sky-100">
          <div className="max-w-2xl mx-auto flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question…"
              className="input-big flex-1"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="btn-big bg-sky-500 text-white hover:bg-sky-600 disabled:opacity-50 shrink-0"
            >
              Send
            </button>
          </div>
        </form>
      </main>
    </>
  );
}
