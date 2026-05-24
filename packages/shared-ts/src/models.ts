/** TypeScript interfaces for database entities (frontend use, API contracts). */

export interface User {
  id: string;
  email: string;
  name?: string;
  clerk_id: string;
  tier: "free" | "paid_monthly" | "paid_annual" | "team";
  trial_ends_at?: string;
  launch_promo_ends_at?: string;
  preferences: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Model {
  id: string;
  name: string;
  provider: string;
  tier: "free" | "paid" | "fallback";
  max_tokens?: number;
  is_active: boolean;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface ChatSession {
  id: string;
  user_id: string;
  title?: string;
  first_message?: string;
  model_used_id?: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  command?: string;
  command_args?: Record<string, unknown>;
  model_used_id?: string;
  latency_ms?: number;
  token_count_input?: number;
  token_count_output?: number;
  created_at: string;
}

export interface Cocktail {
  id: string;
  name: string;
  description?: string;
  ingredients: Array<{
    name: string;
    quantity: number;
    unit: string;
    estimated_cost_usd?: number;
  }>;
  method?: string;
  glass?: string;
  garnish?: string;
  tasting_notes?: {
    aroma: string;
    palate: string;
    finish: string;
  };
  source: "iba" | "generated" | "user" | "community" | "curated";
  taste_score?: number;
  feedback_count: number;
  is_deprecated: boolean;
  is_promoted: boolean;
  model_used_id?: string;
  created_at: string;
}

export interface Quest {
  id: string;
  name: string;
  description?: string;
  quest_type: "feedback" | "validation" | "tagging" | "onboarding";
  target_count: number;
  reward_days: number;
  is_active: boolean;
}

export interface SupportTicket {
  id: string;
  user_id?: string;
  category: string;
  priority: string;
  subject?: string;
  body: string;
  status: string;
  created_at: string;
}
