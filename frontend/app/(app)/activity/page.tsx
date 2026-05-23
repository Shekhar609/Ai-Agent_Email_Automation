"use client";

import useSWR from "swr";

import Badge, { BadgeTone } from "@/components/Badge";
import Spinner from "@/components/Spinner";
import type { ActivityLogOut } from "@/lib/types";

const approvalTone = (s: string | null): BadgeTone => {
  if (s === "approved" || s === "auto_approved") return "green";
  if (s === "rejected") return "red";
  return "yellow";
};

export default function ActivityPage() {
  const { data, isLoading } = useSWR<ActivityLogOut[]>("/api/activity-logs");

  return (
    <div>
      <h2 className="text-xl font-semibold mb-6">Activity log</h2>
      {isLoading ? (
        <Spinner />
      ) : (
        <div className="bg-white border border-neutral-200 rounded-md divide-y divide-neutral-200">
          {(data ?? []).map((a) => (
            <div key={a.id} className="p-4">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                {a.category && <Badge>{a.category}</Badge>}
                {a.approval_status && (
                  <Badge tone={approvalTone(a.approval_status)}>
                    {a.approval_status}
                  </Badge>
                )}
                {a.sent && <Badge tone="green">sent</Badge>}
                {a.error && <Badge tone="red">error</Badge>}
                <span className="text-xs text-neutral-500 ml-auto">
                  {new Date(a.created_at).toLocaleString()}
                </span>
              </div>
              {a.error && <div className="text-xs text-red-700">{a.error}</div>}
              {a.payload && (
                <pre className="text-xs text-neutral-600 mt-1 overflow-x-auto">
                  {JSON.stringify(a.payload, null, 2)}
                </pre>
              )}
            </div>
          ))}
          {data?.length === 0 && (
            <div className="text-center text-neutral-500 text-sm py-8">
              No activity yet.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
