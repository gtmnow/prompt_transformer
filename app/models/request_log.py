from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PromptTransformRequest(Base):
    __tablename__ = "prompt_transform_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    raw_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    transformed_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_provider: Mapped[str] = mapped_column(String(100), nullable=False)
    target_model: Mapped[str] = mapped_column(String(100), nullable=False)
    persona_source: Mapped[str] = mapped_column(String(100), nullable=False)
    used_fallback_model: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
