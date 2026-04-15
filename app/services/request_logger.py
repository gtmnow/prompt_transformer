from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.request_log import PromptTransformRequest


class RequestLogger:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.settings = get_settings()

    def log(self, payload: dict) -> None:
        if not self.settings.enable_request_logging:
            return
        self.db_session.add(PromptTransformRequest(**payload))
        self.db_session.commit()
