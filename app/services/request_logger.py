from sqlalchemy.orm import Session

from app.models.request_log import PromptTransformRequest
from app.services.token_usage import merge_usage, replace_category_usage


class RequestLogger:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def log(self, payload: dict) -> PromptTransformRequest:
        request_row = PromptTransformRequest(**payload)
        self.db_session.add(request_row)
        self.db_session.commit()
        self.db_session.refresh(request_row)
        return request_row

    def append_usage(self, request_log_id: int, usage_entry: dict | None) -> PromptTransformRequest:
        request_row = self._get_required_row(request_log_id)
        request_row.token_usage_json = merge_usage(request_row.token_usage_json, usage_entry)
        self.db_session.add(request_row)
        self.db_session.commit()
        self.db_session.refresh(request_row)
        return request_row

    def set_final_response_usage(self, request_log_id: int, usage_entry: dict | None) -> PromptTransformRequest:
        request_row = self._get_required_row(request_log_id)
        request_row.token_usage_json = replace_category_usage(
            request_row.token_usage_json,
            "final_response",
            usage_entry,
        )
        self.db_session.add(request_row)
        self.db_session.commit()
        self.db_session.refresh(request_row)
        return request_row

    def _get_required_row(self, request_log_id: int) -> PromptTransformRequest:
        request_row = self.db_session.get(PromptTransformRequest, request_log_id)
        if request_row is None:
            raise ValueError(f"Prompt transform request {request_log_id} was not found.")
        return request_row
