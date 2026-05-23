"use client";

import Link from "next/link";
import useSWR from "swr";

import Badge from "@/components/Badge";
import Spinner from "@/components/Spinner";
import type { DraftOut } from "@/lib/types";

export default function DraftsPage() {
  const { data, isLoading } = useSWR<DraftOut[]>(
    "/api/drafts?status=pending_approval",
  );

  return (
    <div>
      <h2 className="text-xl font-semibold mb-6">Pending drafts</h2>
      {isLoading ? (
        <Spinner />
      ) : (
        <div className="space-y-3">
          {(data ?? []).map((d) => (
            <Link
              key={d.id}
              href={`/drafts/${d.id}`}
              className="block bg-white border border-neutral-200 rounded-md p-4 hover:bg-neutral-50"
            >
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <div className="font-medium text-sm">
                  {d.subject ?? "(no subject)"}
                </div>
                {d.tone && <Badge tone="purple">{d.tone}</Badge>}
                {d.confidence_score !== null && (
                  <Badge tone={d.confidence_score >= 0.8 ? "green" : "yellow"}>
                    {(d.confidence_score * 100).toFixed(0)}%
                  </Badge>
                )}
              </div>
              <div className="text-xs text-neutral-500 line-clamp-2">
                {d.body.slice(0, 200)}
              </div>
            </Link>
          ))}
          {data?.length === 0 && (
            <div className="text-center text-neutral-500 text-sm py-8">
              No pending drafts.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
