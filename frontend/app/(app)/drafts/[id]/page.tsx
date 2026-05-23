"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import useSWR from "swr";
import { toast } from "sonner";

import Badge from "@/components/Badge";
import Button from "@/components/Button";
import Spinner from "@/components/Spinner";
import { api } from "@/lib/api";
import type { DraftOut } from "@/lib/types";

export default function DraftDetail() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { data, mutate } = useSWR<DraftOut>(`/api/drafts/${id}`);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [saving, setSaving] = useState(false);
  const [acting, setActing] = useState(false);

  useEffect(() => {
    if (data) {
      setSubject(data.subject ?? "");
      setBody(data.body);
    }
  }, [data]);

  if (!data) return <Spinner />;

  const isPending = data.status === "pending_approval";

  const save = async () => {
    setSaving(true);
    try {
      await api.put(`/api/drafts/${id}`, { subject, body });
      toast.success("Draft saved");
      await mutate();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "save failed");
    } finally {
      setSaving(false);
    }
  };

  const approve = async () => {
    setActing(true);
    try {
      if (subject !== (data.subject ?? "") || body !== data.body) {
        await api.put(`/api/drafts/${id}`, { subject, body });
      }
      const r = await api.post<{ status: string; sent_message_id: string | null }>(
        `/api/drafts/${id}/approve`,
      );
      toast.success(`Sent (${r.status})`);
      router.push("/sent");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "approve failed");
    } finally {
      setActing(false);
    }
  };

  const reject = async () => {
    const reason = window.prompt("Reason (optional)") ?? null;
    setActing(true);
    try {
      await api.post(`/api/drafts/${id}/reject`, { reason });
      toast.success("Rejected");
      router.push("/drafts");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "reject failed");
    } finally {
      setActing(false);
    }
  };

  return (
    <div className="max-w-3xl">
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <h2 className="text-xl font-semibold">Draft</h2>
        <Badge tone={isPending ? "yellow" : data.sent ? "green" : "default"}>
          {data.status}
        </Badge>
        {data.confidence_score !== null && (
          <Badge tone={data.confidence_score >= 0.8 ? "green" : "yellow"}>
            confidence {(data.confidence_score * 100).toFixed(0)}%
          </Badge>
        )}
        {data.tone && <Badge tone="purple">{data.tone}</Badge>}
      </div>

      <div className="space-y-3 bg-white p-4 rounded-md border border-neutral-200 mb-4">
        <label className="block">
          <span className="text-xs text-neutral-600 font-medium">Subject</span>
          <input
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            disabled={!isPending}
            className="mt-1 w-full px-3 py-2 border border-neutral-200 rounded-md text-sm disabled:bg-neutral-50"
          />
        </label>
        <label className="block">
          <span className="text-xs text-neutral-600 font-medium">Body</span>
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            disabled={!isPending}
            rows={14}
            className="mt-1 w-full px-3 py-2 border border-neutral-200 rounded-md text-sm font-mono disabled:bg-neutral-50"
          />
        </label>
      </div>

      {isPending && (
        <div className="flex gap-2">
          <Button onClick={approve} disabled={acting}>
            {acting ? "Working…" : "Approve & send"}
          </Button>
          <Button onClick={save} disabled={saving} variant="secondary">
            {saving ? "Saving…" : "Save"}
          </Button>
          <Button onClick={reject} disabled={acting} variant="danger">
            Reject
          </Button>
        </div>
      )}
    </div>
  );
}
