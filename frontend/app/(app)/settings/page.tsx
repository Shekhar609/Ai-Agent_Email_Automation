"use client";

import { useEffect, useState } from "react";
import useSWR from "swr";
import { toast } from "sonner";

import Button from "@/components/Button";
import Spinner from "@/components/Spinner";
import { api } from "@/lib/api";
import type { UserOut } from "@/lib/types";

export default function SettingsPage() {
  const { data, mutate } = useSWR<UserOut>("/api/users/me");
  const [enabled, setEnabled] = useState(false);
  const [threshold, setThreshold] = useState(0.85);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (data) {
      setEnabled(data.auto_send_enabled);
      setThreshold(data.auto_send_threshold);
    }
  }, [data]);

  if (!data) return <Spinner />;

  const save = async () => {
    setSaving(true);
    try {
      await api.put<UserOut>("/api/users/me/settings", {
        auto_send_enabled: enabled,
        auto_send_threshold: threshold,
      });
      toast.success("Settings saved");
      await mutate();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-xl">
      <h2 className="text-xl font-semibold mb-6">Settings</h2>
      <div className="bg-white border border-neutral-200 rounded-md p-5 space-y-4">
        <div>
          <div className="text-sm font-medium mb-1">Account</div>
          <div className="text-sm text-neutral-600">{data.email}</div>
        </div>
        <div className="border-t border-neutral-200 pt-4">
          <label className="flex items-center justify-between mb-3 cursor-pointer">
            <div>
              <div className="text-sm font-medium">
                Auto-send high-confidence drafts
              </div>
              <div className="text-xs text-neutral-500">
                Skip approval for drafts above the threshold below.
              </div>
            </div>
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="h-4 w-4"
            />
          </label>
          <label className="block">
            <div className="text-sm font-medium mb-1">
              Confidence threshold: {(threshold * 100).toFixed(0)}%
            </div>
            <input
              type="range"
              min="0.5"
              max="1.0"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              disabled={!enabled}
              className="w-full"
            />
          </label>
        </div>
        <div className="border-t border-neutral-200 pt-4">
          <Button onClick={save} disabled={saving}>
            {saving ? "Saving…" : "Save"}
          </Button>
        </div>
      </div>
    </div>
  );
}
