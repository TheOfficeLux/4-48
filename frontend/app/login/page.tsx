"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { access_token } = await login(email, password);
      localStorage.setItem("access_token", access_token);
      router.push("/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6 bg-gradient-to-b from-sky-100 to-mint-50">
      <div className="card-soft w-full max-w-md">
        <h1 className="text-3xl font-bold text-sky-700 mb-6 text-center">
          Welcome back
        </h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block text-lg font-medium text-slate-700">
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input-big"
            placeholder="you@example.com"
            required
            autoComplete="email"
          />
          <label className="block text-lg font-medium text-slate-700">
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input-big"
            placeholder="••••••••"
            required
            autoComplete="current-password"
          />
          {error && (
            <p className="text-red-600 text-sm font-medium" role="alert">
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={loading}
            className="btn-big w-full bg-sky-500 text-white hover:bg-sky-600 disabled:opacity-50"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <p className="mt-6 text-center text-slate-600">
          No account?{" "}
          <Link href="/register" className="text-sky-600 font-semibold hover:underline">
            Create one
          </Link>
        </p>
      </div>
    </main>
  );
}
