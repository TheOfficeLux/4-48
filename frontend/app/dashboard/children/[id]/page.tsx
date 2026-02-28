"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getChild } from "@/lib/api";
import Nav from "@/components/Nav";

type Profile = {
  child: { child_id: string; full_name: string; date_of_birth: string; primary_language: string };
  neuro_profile: { diagnoses: string[]; attention_span_mins: number; preferred_modalities: string[]; communication_style: string; hyperfocus_topics: string[] } | null;
  disabilities: { disability_type: string; severity: string }[];
};

export default function ChildProfilePage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!localStorage.getItem("access_token")) {
      router.replace("/login");
      return;
    }
    getChild(id)
      .then(setProfile)
      .catch(() => setProfile(null))
      .finally(() => setLoading(false));
  }, [id, router]);

  if (loading || !profile) {
    return (
      <>
        <Nav />
        <main className="max-w-4xl mx-auto p-6">
          {loading ? <p className="text-slate-500">Loading…</p> : <p className="text-red-600">Could not load profile.</p>}
        </main>
      </>
    );
  }

  const { child, neuro_profile, disabilities } = profile;

  return (
    <>
      <Nav />
      <main className="max-w-4xl mx-auto p-6">
        <Link href="/dashboard" className="text-sky-600 font-medium hover:underline mb-4 inline-block">
          ← Back to learners
        </Link>
        <h1 className="text-3xl font-bold text-sky-700 mb-1">{child.full_name}</h1>
        <p className="text-slate-600 mb-6">Born {child.date_of_birth} · Language: {child.primary_language}</p>

        <div className="grid gap-6 md:grid-cols-2 mb-8">
          <Link
            href={`/dashboard/children/${id}/learn`}
            className="card-soft block text-center hover:border-sky-300 transition group"
          >
            <span className="text-4xl mb-2 block">📚</span>
            <span className="text-xl font-semibold text-sky-700 group-hover:text-sky-800">Start learning</span>
            <p className="text-slate-500 mt-1">Ask questions and get friendly answers</p>
          </Link>
          <Link
            href={`/dashboard/children/${id}/progress`}
            className="card-soft block text-center hover:border-sky-300 transition group"
          >
            <span className="text-4xl mb-2 block">📊</span>
            <span className="text-xl font-semibold text-sky-700 group-hover:text-sky-800">See progress</span>
            <p className="text-slate-500 mt-1">Mastery, timeline and reports</p>
          </Link>
        </div>

        <div className="card-soft">
          <h2 className="text-xl font-semibold text-slate-800 mb-3">Profile summary</h2>
          {neuro_profile && (
            <div className="mb-4">
              <p className="text-slate-600">
                <strong>Attention span:</strong> {neuro_profile.attention_span_mins} min
                {neuro_profile.diagnoses?.length ? ` · Diagnoses: ${neuro_profile.diagnoses.join(", ")}` : ""}
              </p>
              <p className="text-slate-600">
                <strong>Likes:</strong> {neuro_profile.preferred_modalities?.join(", ") || "—"}
                {neuro_profile.hyperfocus_topics?.length ? ` · Loves: ${neuro_profile.hyperfocus_topics.join(", ")}` : ""}
              </p>
            </div>
          )}
          {disabilities.length > 0 && (
            <p className="text-slate-600">
              <strong>Accommodations:</strong> {disabilities.map((d) => `${d.disability_type} (${d.severity})`).join(", ")}
            </p>
          )}
          {!neuro_profile && disabilities.length === 0 && (
            <p className="text-slate-500">No neuro profile or disabilities set. Use the API or admin to add them for personalised learning.</p>
          )}
        </div>
      </main>
    </>
  );
}
