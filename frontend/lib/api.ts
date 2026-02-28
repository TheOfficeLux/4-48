const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export async function api<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(Array.isArray(err.detail) ? err.detail[0]?.msg : err.detail || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// Auth
export function register(email: string, password: string, fullName: string) {
  return api<{ access_token: string; refresh_token: string }>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
}

export function login(email: string, password: string) {
  return api<{ access_token: string; refresh_token: string }>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

// Children
export function createChild(body: { full_name: string; date_of_birth: string; primary_language?: string }) {
  return api<{ child_id: string }>("/api/children", {
    method: "POST",
    body: JSON.stringify({ ...body, primary_language: body.primary_language || "en" }),
  });
}

export function getChild(childId: string) {
  return api<{
    child: { child_id: string; full_name: string; date_of_birth: string; primary_language: string; grade_level: string | null };
    neuro_profile: { diagnoses: string[]; attention_span_mins: number; preferred_modalities: string[]; communication_style: string; sensory_thresholds: Record<string, number>; hyperfocus_topics: string[]; frustration_threshold: number } | null;
    disabilities: { disability_id: string; disability_type: string; severity: string; accommodations: Record<string, unknown> }[];
  }>(`/api/children/${childId}`);
}

export function upsertNeuro(childId: string, body: {
  diagnoses: string[];
  attention_span_mins: number;
  preferred_modalities: string[];
  communication_style: string;
  sensory_thresholds: Record<string, number>;
  hyperfocus_topics: string[];
  frustration_threshold: number;
}) {
  return api(`/api/children/${childId}/neuro`, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export function addDisability(childId: string, body: { disability_type: string; severity?: string; accommodations?: Record<string, unknown> }) {
  return api<{ disability_id: string }>(`/api/children/${childId}/disabilities`, {
    method: "POST",
    body: JSON.stringify({ ...body, severity: body.severity || "MODERATE" }),
  });
}

export function removeDisability(childId: string, disabilityType: string) {
  return api(`/api/children/${childId}/disabilities/${disabilityType}`, { method: "DELETE" });
}

// Sessions
export function startSession(childId: string) {
  return api<{ session_id: string; ui_directives: Record<string, unknown>; session_constraints: Record<string, unknown> }>("/api/sessions/start", {
    method: "POST",
    body: JSON.stringify({ child_id: childId }),
  });
}

export function endSession(sessionId: string) {
  return api<{
    session_id: string;
    total_interactions: number;
    avg_response_time_ms: number | null;
    frustration_events: number;
    hyperfocus_flag: boolean;
    session_quality: number | null;
    topics_covered: string[] | null;
  }>(`/api/sessions/${sessionId}/end`, {
    method: "POST",
  });
}

export function getSession(sessionId: string) {
  return api<{ session_id: string; total_interactions: number; ended_at: string | null }>(`/api/sessions/${sessionId}`);
}

// Learn
export function getUsage() {
  return api<{
    date: string;
    llm_requests: number;
    llm_daily_limit: number;
    embed_requests: number;
    embed_daily_limit: number;
  }>("/api/learn/usage");
}

export function ask(childId: string, sessionId: string, inputText: string) {
  return api<{
    interaction_id: string;
    response_text: string;
    ui_directives: Record<string, unknown>;
    session_constraints: Record<string, unknown>;
    chunks_used: { topic: string; difficulty_level: number; format_type: string }[];
    response_time_ms: number;
  }>("/api/learn/ask", {
    method: "POST",
    body: JSON.stringify({ child_id: childId, session_id: sessionId, input_text: inputText, input_type: "TEXT" }),
  });
}

export function sendSignal(childId: string, sessionId: string, signalType: string, value: number) {
  return api<{ state: { cognitive_load: number; mood_score: number; readiness_score: number } }>("/api/learn/signal", {
    method: "POST",
    body: JSON.stringify({ child_id: childId, session_id: sessionId, signal_type: signalType, value }),
  });
}

export function sendFeedback(
  interactionId: string,
  childId: string,
  topic: string,
  rating: number,
  childReaction: string,
  engagementScore?: number
) {
  return api<{ topic: string; mastery_level: number; next_review_days: number | null }>("/api/learn/feedback", {
    method: "POST",
    body: JSON.stringify({
      interaction_id: interactionId,
      child_id: childId,
      topic,
      rating,
      child_reaction: childReaction,
      engagement_score: engagementScore ?? 0.5,
    }),
  });
}

// Progress
export function getProgress(childId: string) {
  return api<{
    child_id: string;
    mastery_records: { topic: string; mastery_level: number; next_review_due: string | null; review_count: number }[];
    total_sessions: number;
    total_interactions: number;
  }>(`/api/progress/${childId}`);
}

export function getMastery(childId: string) {
  return api<{ topic: string; mastery_level: number; stability: number; next_review_due: string | null; review_count: number }[]>(
    `/api/progress/${childId}/mastery`
  );
}

export function getTimeline(childId: string, days = 30) {
  return api<{ child_id: string; days: number; timeline: { date: string; interactions: number; avg_engagement: number | null }[] }>(
    `/api/progress/${childId}/timeline?days=${days}`
  );
}

export function getReport(childId: string) {
  return api<{
    child_id: string;
    period_days: number;
    total_sessions: number;
    total_interactions: number;
    mastery_summary: { topic: string; mastery_level: number; review_count: number }[];
    generated_at: string;
  }>(`/api/progress/${childId}/report`);
}

export function getReviewQueue(childId: string) {
  return api<{ child_id: string; due_topics: { topic: string; next_review_due: string; mastery_level: number }[] }>(
    `/api/progress/${childId}/review-queue`
  );
}
