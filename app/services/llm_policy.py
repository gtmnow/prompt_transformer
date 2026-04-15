from __future__ import annotations

from dataclasses import dataclass

from app.core.rules import get_rule_registry


@dataclass(frozen=True)
class ResolvedLLMPolicy:
    provider: str
    requested_model: str
    resolved_model: str
    used_fallback_model: bool
    policy: dict


class LLMPolicyService:
    def __init__(self) -> None:
        self.rules = get_rule_registry().llm_policies

    def resolve(self, provider: str, model: str) -> ResolvedLLMPolicy:
        providers = self.rules.get("providers", {})
        provider_config = providers.get(provider, {})
        model_policies = provider_config.get("models", {})
        default_model = provider_config.get("default_model", self.rules["default"]["resolved_model"])

        if model in model_policies:
            return ResolvedLLMPolicy(
                provider=provider,
                requested_model=model,
                resolved_model=model,
                used_fallback_model=False,
                policy=model_policies[model],
            )

        if default_model in model_policies:
            resolved_model = default_model
            policy = model_policies[default_model]
        else:
            resolved_model = self.rules["default"]["resolved_model"]
            policy = self.rules["default"]["policy"]

        return ResolvedLLMPolicy(
            provider=provider,
            requested_model=model,
            resolved_model=resolved_model,
            used_fallback_model=True,
            policy=policy,
        )
