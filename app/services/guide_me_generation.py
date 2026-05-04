from __future__ import annotations

import json

from app.schemas.transform import GuideMeHelperKind
from app.services.llm_gateway import LlmGatewayService
from app.services.llm_types import TransformerLlmRequest
from app.services.runtime_llm import RuntimeLlmConfig


class GuideMeGenerationService:
    def __init__(self) -> None:
        self.gateway = LlmGatewayService()

    def generate(
        self,
        *,
        helper_kind: GuideMeHelperKind,
        prompt: str,
        runtime_config: RuntimeLlmConfig,
        max_output_tokens: int,
    ) -> dict:
        request = TransformerLlmRequest(
            provider=runtime_config.provider,  # type: ignore[arg-type]
            model=runtime_config.model,
            base_url=_resolve_base_url(runtime_config.endpoint_url, runtime_config.provider),
            api_key=runtime_config.api_key,
            system_prompt=(
                "Return only valid JSON that strictly follows the user's instructions. "
                "Do not add markdown fences, commentary, or extra keys."
            ),
            user_prompt=prompt,
            max_output_tokens=max_output_tokens,
            temperature=0.0,
            expected_output="json",
        )
        response, error = self.gateway.invoke(request)
        if error is not None:
            raise ValueError(f"Guide Me helper request failed: {error.message}")
        if response is None:
            raise ValueError("Guide Me helper request returned no response.")
        try:
            payload = json.loads(response.output_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Guide Me helper returned invalid JSON for {helper_kind}.") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"Guide Me helper returned a non-object payload for {helper_kind}.")
        return payload


def _resolve_base_url(endpoint_url: str | None, provider: str) -> str:
    normalized = (endpoint_url or "").strip()
    if normalized:
        return normalized
    defaults = {
        "openai": "https://api.openai.com/v1",
        "xai": "https://api.x.ai/v1",
        "anthropic": "https://api.anthropic.com/v1",
        "azure_openai": "https://api.openai.com/v1",
    }
    return defaults.get(provider.strip().casefold(), "https://api.openai.com/v1")
