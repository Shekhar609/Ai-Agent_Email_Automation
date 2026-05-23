"use client";

import { useState } from "react";
import { toast } from "sonner";

import Button from "@/components/Button";
import { api } from "@/lib/api";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);
    try {
      const r = await api.get<{ authorize_url: string; state: string }>(
        "/api/auth/google/login",
      );
      window.location.href = r.authorize_url;
    } catch (e) {
      const message = e instanceof Error ? e.message : "unknown error";
      toast.error(`Could not start sign-in: ${message}`);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-50 p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-sm p-8 border border-neutral-200">
        <h1 className="text-2xl font-semibold mb-2">Email Automation</h1>
        <p className="text-neutral-600 mb-6 text-sm">
          Sign in with your Google account to let the agent read, classify, and reply
          to your emails on your behalf.
        </p>
        <Button onClick={handleLogin} disabled={loading} className="w-full justify-center">
          {loading ? "Loading…" : "Sign in with Google"}
        </Button>
      </div>
    </div>
  );
}
