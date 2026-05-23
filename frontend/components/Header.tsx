"use client";

import useSWR from "swr";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";

import { clearToken } from "@/lib/auth";
import type { UserOut } from "@/lib/types";

export default function Header() {
  const router = useRouter();
  const { data: user } = useSWR<UserOut>("/api/users/me");

  const handleLogout = () => {
    clearToken();
    router.replace("/login");
  };

  return (
    <header className="border-b border-neutral-200 bg-white px-6 py-3 flex items-center justify-between">
      <div className="text-sm text-neutral-600">{user?.email ?? "…"}</div>
      <button
        onClick={handleLogout}
        className="text-sm text-neutral-600 hover:text-neutral-900 inline-flex items-center gap-1"
      >
        <LogOut size={14} />
        Sign out
      </button>
    </header>
  );
}
