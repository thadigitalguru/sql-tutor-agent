"""Optional OpenAI-compatible tutor. Falls back to templates when disabled."""

from __future__ import annotations

import json

import httpx

from app.agent.prompts import system_prompt
from app.config import settings
from app.domain import Evaluation, Exercise


class TutorClient:
    def feedback_for_evaluation(
        self,
        *,
        exercise: Exercise,
        query: str,
        evaluation: Evaluation,
        hint_text: str | None,
        fallback: str,
    ) -> str:
        if not settings.llm_enabled:
            return fallback
        payload = {
            "exercise_id": exercise.id,
            "title": exercise.title,
            "prompt": exercise.prompt,
            "primary_skill": exercise.primary_skill,
            "learner_sql": query,
            "evaluation": evaluation.model_dump(),
            "hint_text": hint_text,
            "instruction": (
                "Write concise tutor feedback. Do not include the full solution unless "
                "status is CORRECT or the provided hint_text already contains it. "
                "Follow the Feedback Format in the system prompt."
            ),
        }
        try:
            return self._complete(json.dumps(payload, default=str)) or fallback
        except (httpx.HTTPError, ValueError, KeyError):
            return fallback

    def _complete(self, user_content: str) -> str:
        url = settings.llm_base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": settings.llm_model,
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": system_prompt()},
                {"role": "user", "content": user_content},
            ],
        }
        with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
            response = client.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"].strip()
