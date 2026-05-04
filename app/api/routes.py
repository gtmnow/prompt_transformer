from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import OperationalError, TimeoutError as SQLAlchemyTimeoutError
from sqlalchemy.orm import Session

from app.api.deps import require_service_auth
from app.db.session import get_db
from app.schemas.transform import (
    ExecuteChatRequest,
    ExecuteChatResponse,
    FinalResponseUsageRequest,
    FinalResponseUsageResponse,
    ConversationScoreResponse,
    GuideMeHelperRequest,
    GuideMeHelperResponse,
    ResolvedProfileResponse,
    TransformPromptRequest,
    TransformPromptResponse,
)
from app.services.profile_resolver import ProfileResolver
from app.services.conversation_scores import ConversationScoreService
from app.services.llm_types import NormalizedTokenUsage
from app.services.request_logger import RequestLogger
from app.services.transformer_engine import TransformerEngine
from app.services.token_usage import build_usage_entry

router = APIRouter(prefix="/api", tags=["prompt-transformer"])


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/transform_prompt", response_model=TransformPromptResponse)
def transform_prompt(
    payload: TransformPromptRequest,
    _: str = Depends(require_service_auth),
    db: Session = Depends(get_db),
) -> TransformPromptResponse:
    try:
        engine = TransformerEngine(db_session=db)
        return engine.transform(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    except SQLAlchemyTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection pool exhausted",
        ) from exc


@router.post("/chat/execute", response_model=ExecuteChatResponse)
def execute_chat(
    payload: ExecuteChatRequest,
    _: str = Depends(require_service_auth),
    db: Session = Depends(get_db),
) -> ExecuteChatResponse:
    try:
        engine = TransformerEngine(db_session=db)
        return engine.execute_chat(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    except SQLAlchemyTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection pool exhausted",
        ) from exc


@router.post("/guide_me/generate", response_model=GuideMeHelperResponse)
def generate_guide_me_helper(
    payload: GuideMeHelperRequest,
    _: str = Depends(require_service_auth),
    db: Session = Depends(get_db),
) -> GuideMeHelperResponse:
    try:
        engine = TransformerEngine(db_session=db)
        return engine.generate_guide_me_helper(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    except SQLAlchemyTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection pool exhausted",
        ) from exc


@router.get("/conversation_scores/{conversation_id}", response_model=ConversationScoreResponse)
def get_conversation_score(
    conversation_id: str,
    user_id_hash: str,
    _: str = Depends(require_service_auth),
    db: Session = Depends(get_db),
) -> ConversationScoreResponse:
    try:
        service = ConversationScoreService(db_session=db)
        return service.get_conversation_score(conversation_id=conversation_id, user_id_hash=user_id_hash)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    except SQLAlchemyTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection pool exhausted",
        ) from exc


@router.get("/profiles/resolve", response_model=ResolvedProfileResponse)
def resolve_profile(
    user_id_hash: str,
    summary_type: int | None = None,
    _: str = Depends(require_service_auth),
    db: Session = Depends(get_db),
) -> ResolvedProfileResponse:
    try:
        resolver = ProfileResolver(db_session=db)
        persona = resolver.resolve(user_id_hash=user_id_hash, summary_type=summary_type)
        return ResolvedProfileResponse(
            user_id_hash=user_id_hash,
            summary_type=summary_type,
            profile_version=persona.profile_version,
            persona_source=persona.source,
            prompt_enforcement_level=persona.prompt_enforcement_level,
            compliance_check_enabled=persona.compliance_check_enabled,
            pii_check_enabled=persona.pii_check_enabled,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    except SQLAlchemyTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection pool exhausted",
        ) from exc


@router.post("/request_usage/final_response", response_model=FinalResponseUsageResponse)
def record_final_response_usage(
    payload: FinalResponseUsageRequest,
    _: str = Depends(require_service_auth),
    db: Session = Depends(get_db),
) -> FinalResponseUsageResponse:
    try:
        request_logger = RequestLogger(db_session=db)
        usage_entry = build_usage_entry(
            category="final_response",
            purpose="final_response",
            provider=payload.provider,
            model=payload.model,
            usage=NormalizedTokenUsage(**payload.usage.model_dump()),
        )
        request_logger.set_final_response_usage(payload.request_log_id, usage_entry)
        return FinalResponseUsageResponse(
            request_log_id=payload.request_log_id,
            status="updated",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    except SQLAlchemyTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection pool exhausted",
        ) from exc
