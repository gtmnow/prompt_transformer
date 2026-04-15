from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class TargetLLM(BaseModel):
    provider: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)


class TransformPromptRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=255)
    user_id: str = Field(min_length=1, max_length=255)
    raw_prompt: str = Field(min_length=1)
    target_llm: TargetLLM
    summary_type: Optional[int] = Field(default=None)

    @field_validator("summary_type")
    @classmethod
    def validate_summary_type(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return value
        if 1 <= value <= 9:
            return value
        raise ValueError("summary_type must be between 1 and 9")


class TransformMetadata(BaseModel):
    persona_source: Literal["summary_override", "db_profile", "generic_default"]
    rules_applied: list[str]
    profile_version: str
    requested_model: str
    resolved_model: str
    used_fallback_model: bool


class TransformPromptResponse(BaseModel):
    session_id: str
    user_id: str
    transformed_prompt: str
    task_type: str
    metadata: TransformMetadata
