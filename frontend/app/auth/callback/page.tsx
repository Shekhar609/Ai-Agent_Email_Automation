"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";

import { setToken } from "@/lib/auth";

function CallbackInner() {
  const router = useRouter();
  const sp = useSearchParams();

  useEffect(() => {
    const token = sp.get("token");
    const email = sp.get("email");
    if (token) {
      setToken(token);
      toast.success(`Signed in${email ? ` as ${email}` : ""}`);
      router.replace("/inbox");
    } else {
      toast.error("Sign-in failed");
      router.replace("/login");
    }
  }, [sp, router]);

  return (
    <div className="min-h-screen flex items-center justify-center text-neutral-600 text-sm">
      Completing sign-in…
    </div>
  );
}

export default function AuthCallback() {
  return (
    <Suspense fallback={null}>
      <CallbackInner />
    </Suspense>
  );
}
