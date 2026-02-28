"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import Nav from "@/components/Nav";

type Child = { child_id: string; full_name: string; date_of_birth: string };

export default function DashboardPage() {
  const [children, setChildren] = useState<Child[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [name, setName] = useState("");
  const [dob, setDob] = useState("");
  const [addError, setAddError] = useState("");
  const [adding, setAdding] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.replace("/login");
      return;
    }
    loadChildren();
  }, [router]);

  async function loadChildren() {
    setLoading(true);
    try {
      const list = await api<Child[]>("/api/children");
      setChildren(Array.isArray(list) ? list : []);
    } catch {
      setChildren([]);
    } finally {
      setLoading(false);
    }
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setAddError("");
    setAdding(true);
    try {
      const { createChild } = await import("@/lib/api");
      await createChild({ full_name: name, date_of_birth: dob });
      await loadChildren();
      setName("");
      setDob("");
      setShowAdd(false);
    } catch (err) {
      setAddError(err instanceof Error ? err.message : "Could not add child");
    } finally {
      setAdding(false);
    }
  }

  if (typeof window !== "undefined" && !localStorage.getItem("access_token")) {
    return null;
  }

  return (
    <>
      <Nav />
      <main className="max-w-4xl mx-auto p-6">
        <h1 className="text-3xl font-bold text-sky-700 mb-2">My learners</h1>
        <p className="text-slate-600 mb-6">Pick a learner to start a session or see progress.</p>

        {loading ? (
          <p className="text-slate-500">Loading…</p>
        ) : (
          <ul className="space-y-3">
            {children.map((c) => (
              <li key={c.child_id}>
                <Link
                  href={`/dashboard/children/${c.child_id}`}
                  className="card-soft block hover:border-sky-300 transition"
                >
                  <span className="text-xl font-semibold text-slate-800">{c.full_name}</span>
                  <span className="text-slate-500 ml-2">Born {c.date_of_birth}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}

        {showAdd ? (
          <div className="card-soft mt-6">
            <h2 className="text-xl font-semibold text-sky-700 mb-4">Add a learner</h2>
            <form onSubmit={handleAdd} className="space-y-4">
              <label className="block text-lg font-medium text-slate-700">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input-big"
                placeholder="Child's name"
                required
              />
              <label className="block text-lg font-medium text-slate-700">Date of birth</label>
              <input
                type="date"
                value={dob}
                onChange={(e) => setDob(e.target.value)}
                className="input-big"
                required
              />
              {addError && <p className="text-red-600 text-sm">{addError}</p>}
              <div className="flex gap-3">
                <button type="submit" disabled={adding} className="btn-big bg-sky-500 text-white hover:bg-sky-600 disabled:opacity-50">
                  {adding ? "Adding…" : "Add"}
                </button>
                <button
                  type="button"
                  onClick={() => { setShowAdd(false); setAddError(""); }}
                  className="btn-big bg-slate-100 text-slate-700 hover:bg-slate-200"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        ) : (
          <button
            onClick={() => setShowAdd(true)}
            className="btn-big mt-6 bg-mint-200 text-slate-800 hover:bg-mint-300 border-2 border-mint-300"
          >
            + Add a learner
          </button>
        )}
      </main>
    </>
  );
}
