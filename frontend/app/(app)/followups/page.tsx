"use client";

import useSWR from "swr";
import { toast } from "sonner";

import Badge, { BadgeTone } from "@/components/Badge";
import Button from "@/components/Button";
import Spinner from "@/components/Spinner";
import { api } from "@/lib/api";
import type { FollowUpOut } from "@/lib/types";

const tone = (s: string): BadgeTone => {
  if (s === "completed") return "green";
  if (s === "failed") return "red";
  if (s === "cancelled") return "default";
  if (s === "processing") return "blue";
  return "yellow";
};

export default function FollowUpsPage() {
  const { data, isLoading, mutate } = useSWR<FollowUpOut[]>("/api/followups");

  const cancel = async (id: string) => {
    try {
      await api.delete(`/api/followups/${id}`);
      toast.success("Cancelled");
      await mutate();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "cancel failed");
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold mb-6">Follow-ups</h2>
      {isLoading ? (
        <Spinner />
      ) : (
        <div className="space-y-3">
          {(data ?? []).map((f) => (
            <div
              key={f.id}
              className="bg-white border border-neutral-200 rounded-md p-4 flex items-start gap-3"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <Badge tone={tone(f.status)}>{f.status}</Badge>
                  <span className="text-sm text-neutral-600">
                    {new Date(f.scheduled_for).toLocaleString()}
                  </span>
                </div>
                <div className="text-sm text-neutral-700">
                  {f.reason ?? "(no reason)"}
                </div>
                {f.error && (
                  <div className="text-xs text-red-700 mt-1">{f.error}</div>
                )}
              </div>
              {f.status === "pending" && (
                <Button variant="ghost" onClick={() => cancel(f.id)}>
                  Cancel
                </Button>
              )}
            </div>
          ))}
          {data?.length === 0 && (
            <div className="text-center text-neutral-500 text-sm py-8">
              No follow-ups scheduled.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
