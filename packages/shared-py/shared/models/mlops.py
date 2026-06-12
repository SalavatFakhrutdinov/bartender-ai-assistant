"""MLOps and validation models."""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, TSTZRANGE
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base, TimestampMixin, UUIDMixin


class MLExperiment(Base, UUIDMixin, TimestampMixin):
    """Fine-tuning experiment tracking."""

    __tablename__ = "ml_experiments"

    experiment_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_base: Mapped[str] = mapped_column(String(100), nullable=False)
    training_data_period: Mapped[dict | None] = mapped_column(TSTZRANGE)
    hyperparams: Mapped[dict | None] = mapped_column(JSONB)
    eval_metrics: Mapped[dict | None] = mapped_column(JSONB)
    ab_test_traffic_percent: Mapped[int | None] = mapped_column(Integer)
    ab_test_result: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str | None] = mapped_column(String(50))
    mlflow_run_id: Mapped[str | None] = mapped_column(String(100))


class ValidationFailure(Base, UUIDMixin, TimestampMixin):
    """Record of physical validation failures for MLOps analysis."""

    __tablename__ = "validation_failures"

    cocktail_id: Mapped[str | None] = mapped_column(ForeignKey("cocktails.id"))
    recipe_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    issues: Mapped[list] = mapped_column(JSONB, nullable=False)
    regeneration_attempts: Mapped[int] = mapped_column(Integer, default=0)
    final_status: Mapped[str | None] = mapped_column(String(20))
