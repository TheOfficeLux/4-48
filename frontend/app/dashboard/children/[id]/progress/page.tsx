"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getProgress, getTimeline, getReport, getReviewQueue } from "@/lib/api";
import Nav from "@/components/Nav";

export default function ProgressPage() {
  const params = useParams();
  const router = useRouter();
  const childId = params.id as string;
  const [progress, setProgress] = useState<{
    total_sessions: number;
    total_interactions: number;
    mastery_records: { topic: string; mastery_level: number; next_review_due: string | null; review_count: number }[];
  } | null>(null);
  const [timeline, setTimeline] = useState<{ date: string; interactions: number; avg_engagement: number | null }[]>([]);
  const [report, setReport] = useState<{
    total_sessions: number;
    total_interactions: number;
    mastery_summary: { topic: string; mastery_level: number; review_count: number }[];
    generated_at: string;
  } | null>(null);
  const [reviewQueue, setReviewQueue] = useState<{ topic: string; next_review_due: string; mastery_level: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"overview" | "mastery" | "timeline" | "report" | "review">("overview");

  useEffect(() => {
    if (!localStorage.getItem("access_token")) {
      router.replace("/login");
      return;
    }
    Promise.all([
      getProgress(childId),
      getTimeline(childId, 30),
      getReport(childId),
      getReviewQueue(childId),
    ])
      .then(([p, t, r, q]) => {
        setProgress(p);
        setTimeline(t.timeline || []);
        setReport(r);
        setReviewQueue(q.due_topics || []);
      })
      .catch(() => setProgress(null))
      .finally(() => setLoading(false));
  }, [childId, router]);

  if (loading) {
    return (
      <>
        <Nav />
        <main className="max-w-4xl mx-auto p-6">
          <p className="text-slate-500">Loading progress…</p>
        </main>
      </>
    );
  }

  return (
    <>
      <Nav />
      <main className="max-w-4xl mx-auto p-6">
        <Link href={`/dashboard/children/${childId}`} className="text-sky-600 font-medium hover:underline mb-4 inline-block">
          ← Back to profile
        </Link>
        <h1 className="text-3xl font-bold text-sky-700 mb-6">Progress</h1>

        <div className="flex flex-wrap gap-2 mb-6">
          {(["overview", "mastery", "timeline", "report", "review"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`min-h-[44px] px-4 py-2 rounded-xl font-medium capitalize ${
                tab === t ? "bg-sky-500 text-white" : "bg-sky-100 text-sky-700 hover:bg-sky-200"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        {tab === "overview" && progress && (
          <div className="card-soft space-y-4">
            <h2 className="text-xl font-semibold text-slate-800">Overview</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-sky-50 rounded-2xl p-4">
                <p className="text-3xl font-bold text-sky-600">{progress.total_sessions}</p>
                <p className="text-slate-600">Sessions</p>
              </div>
              <div className="bg-mint-50 rounded-2xl p-4">
                <p className="text-3xl font-bold text-mint-600">{progress.total_interactions}</p>
                <p className="text-slate-600">Questions asked</p>
              </div>
            </div>
            {progress.mastery_records.length > 0 && (
              <>
                <h3 className="font-semibold text-slate-700">Topics</h3>
                <ul className="space-y-2">
                  {progress.mastery_records.slice(0, 10).map((r) => (
                    <li key={r.topic} className="flex justify-between items-center">
                      <span>{r.topic}</span>
                      <span className="font-medium">{Math.round(r.mastery_level * 100)}%</span>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}

        {tab === "mastery" && progress && (
          <div className="card-soft">
            <h2 className="text-xl font-semibold text-slate-800 mb-4">Mastery by topic</h2>
            <ul className="space-y-3">
              {progress.mastery_records.length === 0 ? (
                <li className="text-slate-500">No mastery data yet. Start learning to see progress.</li>
              ) : (
                progress.mastery_records.map((r) => (
                  <li key={r.topic} className="flex items-center gap-4">
                    <span className="font-medium text-slate-800 flex-1">{r.topic}</span>
                    <div className="w-32 h-4 bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-sky-500 rounded-full"
                        style={{ width: `${Math.round(r.mastery_level * 100)}%` }}
                      />
                    </div>
                    <span className="text-slate-600 w-12">{Math.round(r.mastery_level * 100)}%</span>
                  </li>
                ))
              )}
            </ul>
          </div>
        )}

        {tab === "timeline" && (
          <div className="card-soft">
            <h2 className="text-xl font-semibold text-slate-800 mb-4">Last 30 days</h2>
            {timeline.length === 0 ? (
              <p className="text-slate-500">No activity in this period.</p>
            ) : (
              <ul className="space-y-2">
                {timeline.map((d) => (
                  <li key={d.date} className="flex justify-between">
                    <span>{d.date}</span>
                    <span>{d.interactions} interactions</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {tab === "report" && report && (
          <div className="card-soft space-y-4">
            <h2 className="text-xl font-semibold text-slate-800">Caregiver report</h2>
            <p className="text-slate-600">Generated {new Date(report.generated_at).toLocaleString()}</p>
            <p>
              <strong>{report.total_sessions}</strong> sessions · <strong>{report.total_interactions}</strong> interactions
            </p>
            <h3 className="font-semibold">Mastery summary</h3>
            <ul className="space-y-1">
              {report.mastery_summary.map((m) => (
                <li key={m.topic}>
                  {m.topic}: {Math.round(m.mastery_level * 100)}% ({m.review_count} reviews)
                </li>
              ))}
            </ul>
          </div>
        )}

        {tab === "review" && (
          <div className="card-soft">
            <h2 className="text-xl font-semibold text-slate-800 mb-4">Due for review</h2>
            {reviewQueue.length === 0 ? (
              <p className="text-mint-600 font-medium">All caught up! No topics due for review right now.</p>
            ) : (
              <ul className="space-y-2">
                {reviewQueue.map((r) => (
                  <li key={r.topic} className="flex justify-between items-center">
                    <span className="font-medium">{r.topic}</span>
                    <span className="text-slate-500">Due {r.next_review_due}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </main>
    </>
  );
}
