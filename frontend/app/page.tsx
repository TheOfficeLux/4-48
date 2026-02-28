"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) router.replace("/dashboard");
  }, [router]);

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6 bg-gradient-to-b from-sky-100 to-mint-50">
      <div className="text-center max-w-md">
        <h1 className="text-4xl md:text-5xl font-bold text-sky-700 mb-2">
          Learning Buddy
        </h1>
        <p className="text-xl text-slate-600 mb-8">
          Your friendly helper for learning, just for you.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/login"
            className="btn-big bg-sky-500 text-white hover:bg-sky-600"
          >
            Sign in
          </Link>
          <Link
            href="/register"
            className="btn-big bg-white text-sky-600 border-2 border-sky-300 hover:bg-sky-50"
          >
            Create account
          </Link>
        </div>
      </div>
    </main>
  );
}
