from __future__ import annotations

from app.core.rules import get_rule_registry


class TaskInferenceService:
    def __init__(self) -> None:
        self.rules = get_rule_registry().task_rules

    def infer(self, raw_prompt: str) -> tuple[str, list[str]]:
        lowered = raw_prompt.lower()
        for task_name, config in self.rules.get("tasks", {}).items():
            keywords = config.get("keywords", [])
            phrases = config.get("phrases", [])
            if any(keyword in lowered for keyword in keywords):
                return task_name, [f"task:{task_name}:keyword"]
            if any(phrase in lowered for phrase in phrases):
                return task_name, [f"task:{task_name}:phrase"]
        return "unknown", ["task:unknown:fallback"]
