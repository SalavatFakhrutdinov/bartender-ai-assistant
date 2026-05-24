/** Mirror of Python event schemas for TypeScript consumers (frontend, webhooks). */

export interface EventMeta {
  event_id: string;
  correlation_id: string;
  timestamp: string;
  source: string;
  version: string;
}

export interface Event {
  meta: EventMeta;
}

// Ticket events
export interface TicketCreated extends Event {
  ticket_id: string;
  title: string;
  description: string;
  acceptance_criteria: string[];
  tags: string[];
  complexity: "S" | "M" | "L" | "XL";
  assigned_to_skill: string;
  estimated_hours?: number;
}

export interface TicketUpdated extends Event {
  ticket_id: string;
  updates: Record<string, unknown>;
  reason?: string;
}

export interface TicketClosed extends Event {
  ticket_id: string;
  resolution: "merged" | "cancelled" | "abandoned";
  final_sha?: string;
}

// Code events
export interface CodePushed extends Event {
  ticket_id: string;
  branch: string;
  commit_sha: string;
  commit_message: string;
  files_changed: string[];
  diff_lines: number;
}

export interface DevReadyForQA extends Event {
  ticket_id: string;
  branch: string;
  commit_sha: string;
  ci_status: "passed" | "failed" | "skipped";
  test_count: number;
  coverage_percent: number;
}

// QA events
export interface QATestSummary extends Event {
  ticket_id: string;
  branch: string;
  commit_sha: string;
  overall_status: "passed" | "failed" | "warning";
  unit_tests: Record<string, unknown>;
  integration_tests: Record<string, unknown>;
  security_scan: Record<string, unknown>;
  coverage_delta: number;
  total_coverage: number;
  blockers: string[];
  warnings: string[];
  duration_seconds: number;
}

// Release events
export interface ReleaseApproved extends Event {
  ticket_id: string;
  approved_by: string;
  risk_level: "low" | "medium" | "high";
  notes?: string;
}

export interface ReleaseRejected extends Event {
  ticket_id: string;
  rejected_by: string;
  reason: string;
  action_items: string[];
  route_to: "analyst" | "developer";
}

// Human input
export interface HumanCommand extends Event {
  user_id: string;
  username?: string;
  command: string;
  args: string;
  chat_id: string;
  thread_id?: string;
}

// Agent telemetry
export interface AgentHeartbeat extends Event {
  agent_id: string;
  agent_type: string;
  skills: Array<{ name: string; proficiency: number }>;
  current_load: number;
  max_concurrent: number;
  status: "healthy" | "busy" | "degraded" | "unhealthy";
  version: string;
}

// Support
export interface SupportTicketCreated extends Event {
  ticket_id: string;
  user_id: string;
  category: "billing" | "technical" | "feature_request" | "bug";
  priority: "low" | "medium" | "high" | "urgent";
  subject?: string;
  body: string;
  user_tier: string;
  user_context: Record<string, unknown>;
}

// NATS subjects
export const NATS_SUBJECTS = {
  TICKETS_CREATED: "tickets.created",
  TICKETS_UPDATED: "tickets.updated",
  TICKETS_CLOSED: "tickets.closed",
  CODE_PUSH: "code.push",
  DEV_READY_FOR_QA: "dev.ready_for_qa",
  QA_TEST_SUMMARY: "qa.test_summary",
  QA_BLOCKER: "qa.blocker",
  UAT_READY: "uat.ready",
  UAT_FEEDBACK: "uat.feedback",
  RELEASE_APPROVED: "release.approved",
  RELEASE_REJECTED: "release.rejected",
  HUMAN_MESSAGE: "human.message",
  HUMAN_COMMAND: "human.command",
  AGENT_HEARTBEAT: "agent.heartbeat",
  AGENT_TASK_ASSIGNED: "agent.task_assigned",
  AGENT_ERROR: "agent.error",
  MEMORY_EPISODE: "memory.episode",
  SUPPORT_TICKET_CREATED: "support.ticket_created",
  CLARIFICATION_NEEDED: "clarification.needed",
} as const;
