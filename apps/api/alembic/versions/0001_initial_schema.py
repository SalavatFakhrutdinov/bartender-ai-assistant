"""Initial schema — all tables from blueprint v2.0.

Revision ID: 0001
Revises:
Create Date: 2026-05-24

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # =========================================================================
    # models — LLM registry
    # =========================================================================
    op.create_table(
        "models",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("tier", sa.String(20), nullable=False, server_default="free"),
        sa.Column("max_tokens", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # =========================================================================
    # users
    # =========================================================================
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("clerk_id", sa.String(255), unique=True, nullable=False),
        sa.Column("tier", sa.String(20), nullable=False, server_default="free"),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("launch_promo_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("preferences", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # =========================================================================
    # subscriptions
    # =========================================================================
    op.create_table(
        "subscriptions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stripe_sub_id", sa.String(255), unique=True, nullable=True),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("plan", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # =========================================================================
    # chat_sessions
    # =========================================================================
    op.create_table(
        "chat_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("first_message", sa.Text(), nullable=True),
        sa.Column(
            "model_used_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("models.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # =========================================================================
    # messages
    # =========================================================================
    op.create_table(
        "messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("command", sa.String(50), nullable=True),
        sa.Column("command_args", postgresql.JSONB(), nullable=True),
        sa.Column(
            "model_used_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("models.id"),
            nullable=True,
        ),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("token_count_input", sa.Integer(), nullable=True),
        sa.Column("token_count_output", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # =========================================================================
    # cocktails
    # =========================================================================
    op.create_table(
        "cocktails",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ingredients", postgresql.JSONB(), nullable=False),
        sa.Column("method", sa.Text(), nullable=True),
        sa.Column("glass", sa.String(100), nullable=True),
        sa.Column("garnish", sa.String(255), nullable=True),
        sa.Column("tasting_notes", postgresql.JSONB(), nullable=True),
        sa.Column("source", sa.String(50), nullable=False, server_default="generated"),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("taste_score", sa.Numeric(3, 2), nullable=True),
        sa.Column("feedback_count", sa.Integer(), default=0),
        sa.Column("is_deprecated", sa.Boolean(), default=False),
        sa.Column("is_promoted", sa.Boolean(), default=False),
        sa.Column("physical_validation_status", sa.String(20), nullable=True),
        sa.Column("qdrant_point_id", sa.String(255), nullable=True),
        sa.Column("neo4j_node_id", sa.String(255), nullable=True),
        sa.Column(
            "model_used_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("models.id"),
            nullable=True,
        ),
        sa.Column("generation_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # =========================================================================
    # cocktail_feedback
    # =========================================================================
    op.create_table(
        "cocktail_feedback",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "cocktail_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("cocktails.id"),
            nullable=True,
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column(
            "overall_rating",
            sa.Integer(),
            sa.CheckConstraint("overall_rating BETWEEN 1 AND 5"),
            nullable=True,
        ),
        sa.Column(
            "balance_rating",
            sa.Integer(),
            sa.CheckConstraint("balance_rating BETWEEN 1 AND 5"),
            nullable=True,
        ),
        sa.Column(
            "aroma_rating",
            sa.Integer(),
            sa.CheckConstraint("aroma_rating BETWEEN 1 AND 5"),
            nullable=True,
        ),
        sa.Column(
            "appearance_rating",
            sa.Integer(),
            sa.CheckConstraint("appearance_rating BETWEEN 1 AND 5"),
            nullable=True,
        ),
        sa.Column(
            "guest_reaction",
            sa.Integer(),
            sa.CheckConstraint("guest_reaction BETWEEN 1 AND 5"),
            nullable=True,
        ),
        sa.Column("would_repeat", sa.String(20), nullable=True),
        sa.Column("modification_note", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # =========================================================================
    # user_bar_context
    # =========================================================================
    op.create_table(
        "user_bar_context",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("concept_text", sa.Text(), nullable=True),
        sa.Column("inventory", postgresql.JSONB(), nullable=True),
        sa.Column("style_preferences", postgresql.JSONB(), nullable=True),
        sa.Column("target_price_range", sa.Numeric(5, 2), nullable=True),
        sa.Column("uploaded_docs", postgresql.JSONB(), nullable=True),
        sa.Column("qdrant_namespace", sa.String(100), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # =========================================================================
    # llm_usage
    # =========================================================================
    op.create_table(
        "llm_usage",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("chat_sessions.id"),
            nullable=True,
        ),
        sa.Column(
            "model_used_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("models.id"),
            nullable=False,
        ),
        sa.Column("tokens_input", sa.Integer(), nullable=False),
        sa.Column("tokens_output", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(8, 6), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("cached", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # =========================================================================
    # validation_failures
    # =========================================================================
    op.create_table(
        "validation_failures",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "cocktail_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("cocktails.id"),
            nullable=True,
        ),
        sa.Column("recipe_json", postgresql.JSONB(), nullable=False),
        sa.Column("issues", postgresql.JSONB(), nullable=False),
        sa.Column("regeneration_attempts", sa.Integer(), default=0),
        sa.Column("final_status", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # =========================================================================
    # ml_experiments
    # =========================================================================
    op.create_table(
        "ml_experiments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("experiment_name", sa.String(255), nullable=False),
        sa.Column("model_base", sa.String(100), nullable=False),
        sa.Column("training_data_period", postgresql.TSTZRANGE(), nullable=True),
        sa.Column("hyperparams", postgresql.JSONB(), nullable=True),
        sa.Column("eval_metrics", postgresql.JSONB(), nullable=True),
        sa.Column("ab_test_traffic_percent", sa.Integer(), nullable=True),
        sa.Column("ab_test_result", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("mlflow_run_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # =========================================================================
    # support_tickets
    # =========================================================================
    op.create_table(
        "support_tickets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("priority", sa.String(20), default="medium"),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), default="open"),
        sa.Column(
            "assigned_to", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # =========================================================================
    # quests
    # =========================================================================
    op.create_table(
        "quests",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("quest_type", sa.String(50), nullable=False),
        sa.Column("target_count", sa.Integer(), default=1),
        sa.Column("reward_days", sa.Integer(), default=7),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # =========================================================================
    # user_quest_progress
    # =========================================================================
    op.create_table(
        "user_quest_progress",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "quest_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("quests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("progress", sa.Integer(), default=0),
        sa.Column("completed", sa.Boolean(), default=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "quest_id", name="uq_user_quest"),
    )

    # =========================================================================
    # pending_cocktails
    # =========================================================================
    op.create_table(
        "pending_cocktails",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("raw_data", postgresql.JSONB(), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column(
            "quality_rating",
            sa.Integer(),
            sa.CheckConstraint("quality_rating BETWEEN 1 AND 5"),
            nullable=True,
        ),
        sa.Column("taste_score", sa.Numeric(3, 2), nullable=True),
        sa.Column(
            "approved_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # =========================================================================
    # Indexes
    # =========================================================================
    op.create_index("ix_users_clerk_id", "users", ["clerk_id"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"])
    op.create_index("ix_messages_session_id", "messages", ["session_id"])
    op.create_index("ix_cocktails_source", "cocktails", ["source"])
    op.create_index("ix_cocktails_taste_score", "cocktails", ["taste_score"])
    op.create_index("ix_cocktail_feedback_cocktail_id", "cocktail_feedback", ["cocktail_id"])
    op.create_index("ix_llm_usage_user_id", "llm_usage", ["user_id"])
    op.create_index("ix_support_tickets_user_id", "support_tickets", ["user_id"])
    op.create_index("ix_support_tickets_status", "support_tickets", ["status"])
    op.create_index("ix_pending_cocktails_status", "pending_cocktails", ["status"])


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("pending_cocktails")
    op.drop_table("user_quest_progress")
    op.drop_table("quests")
    op.drop_table("support_tickets")
    op.drop_table("ml_experiments")
    op.drop_table("validation_failures")
    op.drop_table("llm_usage")
    op.drop_table("user_bar_context")
    op.drop_table("cocktail_feedback")
    op.drop_table("cocktails")
    op.drop_table("messages")
    op.drop_table("chat_sessions")
    op.drop_table("subscriptions")
    op.drop_table("users")
    op.drop_table("models")
