"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { register as apiRegister } from "@/lib/api";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { access_token } = await apiRegister(email, password, fullName);
      localStorage.setItem("access_token", access_token);
      router.push("/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign up failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6 bg-gradient-to-b from-sky-100 to-mint-50">
      <div className="card-soft w-full max-w-md">
        <h1 className="text-3xl font-bold text-sky-700 mb-6 text-center">
          Create your account
        </h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block text-lg font-medium text-slate-700">
            Your name
          </label>
          <input
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="input-big"
            placeholder="Caregiver or teacher name"
            required
            autoComplete="name"
          />
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
            placeholder="At least 8 characters"
            required
            minLength={8}
            autoComplete="new-password"
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
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>
        <p className="mt-6 text-center text-slate-600">
          Already have an account?{" "}
          <Link href="/login" className="text-sky-600 font-semibold hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </main>
  );
}
