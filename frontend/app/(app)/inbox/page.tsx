"use client";

import { useState } from "react";
import Link from "next/link";
import useSWR from "swr";
import { toast } from "sonner";

import Badge, { BadgeTone } from "@/components/Badge";
import Button from "@/components/Button";
import Spinner from "@/components/Spinner";
import { api } from "@/lib/api";
import type { EmailOut, StatsSummary, SyncResponse } from "@/lib/types";

const urgencyTone = (u: string | null): BadgeTone => {
  if (u === "critical") return "red";
  if (u === "high") return "yellow";
  if (u === "medium") return "blue";
  return "default";
};

export default function InboxPage() {
  const { data, isLoading, mutate } = useSWR<EmailOut[]>("/api/emails");
  const { data: stats, mutate: mutateStats } = useSWR<StatsSummary>("/api/stats/summary");
  const [syncing, setSyncing] = useState(false);

  const sync = async () => {
    setSyncing(true);
    try {
      const r = await api.post<SyncResponse>("/api/emails/sync");
      toast.success(`Synced ${r.created} new (skipped ${r.skipped})`);
      await Promise.all([mutate(), mutateStats()]);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "sync failed");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">Inbox</h2>
        <Button onClick={sync} disabled={syncing}>
          {syncing ? "Syncing…" : "Sync now"}
        </Button>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <Stat label="Last 7d" value={stats.emails_last_7d} />
          <Stat label="Drafts pending" value={stats.drafts_pending} />
          <Stat label="Sent (7d)" value={stats.drafts_sent_last_7d} />
          <Stat label="Follow-ups" value={stats.followups_scheduled} />
        </div>
      )}

      {isLoading ? (
        <Spinner />
      ) : (
        <div className="divide-y divide-neutral-200 bg-white rounded-md border border-neutral-200">
          {(data ?? []).map((e) => (
            <Link
              key={e.id}
              href={`/inbox/${e.id}`}
              className="flex items-start gap-3 p-4 hover:bg-neutral-50"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <span className="text-sm font-medium truncate">{e.sender}</span>
                  {e.category && <Badge>{e.category}</Badge>}
                  {e.urgency && <Badge tone={urgencyTone(e.urgency)}>{e.urgency}</Badge>}
                </div>
                <div className="text-sm text-neutral-700 truncate">
                  {e.subject ?? "(no subject)"}
                </div>
                <div className="text-xs text-neutral-500 mt-1 line-clamp-1">
                  {e.body_plain ?? ""}
                </div>
              </div>
              <div className="text-xs text-neutral-500 shrink-0">
                {e.received_at ? new Date(e.received_at).toLocaleDateString() : ""}
              </div>
            </Link>
          ))}
          {data?.length === 0 && (
            <div className="p-8 text-center text-neutral-500 text-sm">
              No emails yet — click &quot;Sync now&quot; to pull from Gmail.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white border border-neutral-200 rounded-md p-3">
      <div className="text-xs text-neutral-500">{label}</div>
      <div className="text-2xl font-semibold mt-1">{value}</div>
    </div>
  );
}
