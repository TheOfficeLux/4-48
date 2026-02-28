"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

export default function Nav() {
  const pathname = usePathname();
  const router = useRouter();

  function signOut() {
    localStorage.removeItem("access_token");
    router.push("/");
    router.refresh();
  }

  return (
    <nav className="bg-white border-b border-sky-100 shadow-sm">
      <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link href="/dashboard" className="text-xl font-bold text-sky-600 hover:text-sky-700">
          Learning Buddy
        </Link>
        <button
          onClick={signOut}
          className="text-slate-600 hover:text-slate-800 font-medium px-4 py-2 rounded-xl hover:bg-slate-100 min-h-[44px]"
        >
          Sign out
        </button>
      </div>
    </nav>
  );
}
