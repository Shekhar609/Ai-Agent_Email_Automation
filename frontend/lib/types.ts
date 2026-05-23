export type UserOut = {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_admin: boolean;
  auto_send_enabled: boolean;
  auto_send_threshold: number;
  created_at: string;
};

export type EmailOut = {
  id: string;
  message_id: string;
  thread_id: string | null;
  sender: string;
  recipient: string;
  subject: string | null;
  body_plain: string | null;
  received_at: string | null;
  category: string | null;
  intent: string | null;
  urgency: string | null;
  created_at: string;
};

export type DraftOut = {
  id: string;
  user_id: string;
  email_id: string;
  subject: string | null;
  body: string;
  tone: string | null;
  status: string;
  confidence_score: number | null;
  approved: boolean;
  sent: boolean;
  created_at: string;
};

export type FollowUpOut = {
  id: string;
  user_id: string;
  email_id: string | null;
  thread_id: string | null;
  scheduled_for: string;
  reason: string | null;
  status: string;
  draft_id: string | null;
  error: string | null;
  created_at: string;
  completed_at: string | null;
};

export type ActivityLogOut = {
  id: string;
  user_id: string;
  email_id: string | null;
  draft_id: string | null;
  category: string | null;
  approval_status: string | null;
  sent: boolean;
  error: string | null;
  payload: Record<string, unknown> | null;
  created_at: string;
};

export type StatsSummary = {
  emails_last_7d: number;
  emails_total: number;
  drafts_pending: number;
  drafts_sent_last_7d: number;
  followups_scheduled: number;
  categories: Record<string, number>;
};

export type SyncResponse = {
  fetched: number;
  created: number;
  skipped: number;
};

export type RunWorkflowResponse = {
  thread_id: string;
  category: string | null;
  is_spam: boolean;
  draft_id: string | null;
  confidence_score: number | null;
  status: string;
};
