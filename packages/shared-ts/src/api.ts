/** API endpoint types and request/response shapes. */

export interface HealthResponse {
  status: "ok" | "degraded" | "unhealthy";
  timestamp: string;
  version: string;
  checks: Record<string, string | boolean>;
  uptime_seconds: number;
}

export interface CreateChatSessionRequest {
  user_id: string;
  first_message?: string;
}

export interface SendMessageRequest {
  session_id: string;
  content: string;
  command?: string;
  command_args?: Record<string, unknown>;
}

export interface CreateSupportTicketRequest {
  category: "billing" | "technical" | "feature_request" | "bug";
  subject?: string;
  body: string;
}

export interface RateLimitInfo {
  tier: string;
  requests_remaining: number;
  reset_at: string;
}

export interface ApiError {
  error: string;
  code: string;
  details?: Record<string, unknown>;
}
