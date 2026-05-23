"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import useSWR from "swr";
import { toast } from "sonner";

import Badge from "@/components/Badge";
import Button from "@/components/Button";
import Spinner from "@/components/Spinner";
import { api } from "@/lib/api";
import type { EmailOut, RunWorkflowResponse } from "@/lib/types";

export default function EmailDetail() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { data: email } = useSWR<EmailOut>(`/api/emails/${id}`);
  const [running, setRunning] = useState(false);

  if (!email) return <Spinner />;

  const runWorkflow = async () => {
    setRunning(true);
    try {
      const r = await api.post<RunWorkflowResponse>("/api/workflow/run", {
        email_id: email.id,
      });
      toast.success(`Workflow: ${r.status}`);
      if (r.draft_id) router.push(`/drafts/${r.draft_id}`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "workflow failed");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="max-w-3xl">
      <div className="flex items-start justify-between mb-4 gap-4">
        <div className="min-w-0">
          <h2 className="text-xl font-semibold break-words">
            {email.subject ?? "(no subject)"}
          </h2>
          <div className="text-sm text-neutral-600 mt-1">
            From {email.sender} → {email.recipient}
          </div>
          {email.received_at && (
            <div className="text-xs text-neutral-500 mt-1">
              {new Date(email.received_at).toLocaleString()}
            </div>
          )}
        </div>
        <Button onClick={runWorkflow} disabled={running}>
          {running ? "Running…" : "Run agent"}
        </Button>
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        {email.category && <Badge>{email.category}</Badge>}
        {email.urgency && <Badge tone="yellow">{email.urgency}</Badge>}
      </div>

      {email.intent && (
        <div className="mb-4 p-3 bg-sky-50 border border-sky-200 rounded-md text-sm">
          <span className="font-medium text-sky-900">Intent:</span>{" "}
          <span className="text-sky-800">{email.intent}</span>
        </div>
      )}

      <pre className="whitespace-pre-wrap text-sm bg-white border border-neutral-200 rounded-md p-4">
        {email.body_plain ?? "(no plain body)"}
      </pre>
    </div>
  );
}
