"use client";

import useSWR from "swr";

import Badge from "@/components/Badge";
import Spinner from "@/components/Spinner";
import type { DraftOut } from "@/lib/types";

export default function SentPage() {
  const { data, isLoading } = useSWR<DraftOut[]>("/api/drafts?status=sent");

  return (
    <div>
      <h2 className="text-xl font-semibold mb-6">Sent</h2>
      {isLoading ? (
        <Spinner />
      ) : (
        <div className="space-y-3">
          {(data ?? []).map((d) => (
            <div
              key={d.id}
              className="bg-white border border-neutral-200 rounded-md p-4"
            >
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <div className="font-medium text-sm">
                  {d.subject ?? "(no subject)"}
                </div>
                <Badge tone="green">sent</Badge>
                {d.tone && <Badge tone="purple">{d.tone}</Badge>}
              </div>
              <div className="text-xs text-neutral-500 mt-1">
                {new Date(d.created_at).toLocaleString()}
              </div>
              <pre className="text-sm text-neutral-700 mt-2 line-clamp-4 whitespace-pre-wrap">
                {d.body}
              </pre>
            </div>
          ))}
          {data?.length === 0 && (
            <div className="text-center text-neutral-500 text-sm py-8">
              Nothing sent yet.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
