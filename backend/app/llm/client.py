"""Thin async client for the vLLM endpoint (OpenAI-compatible).

Design notes
- Qwen3 emits `reasoning_content` and burns the token budget when thinking is enabled, so thinking
  is off by default and toggled per call (`think=True` for analysis-heavy prompts).
- `chat_json` uses vLLM guided decoding (`response_format=json_schema`) so the output always parses;
  a Pydantic validation failure (rare: semantic constraints) is fed back to the model once.
- Transport errors are retried with exponential backoff (PRD risk: vLLM downtime).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, TypeVar

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    InternalServerError,
    RateLimitError,
)
from pydantic import BaseModel, ValidationError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import Settings, get_settings

log = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

_THINK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL)
_RETRYABLE = (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError)


class LLMError(RuntimeError):
    pass


def _strip_think(text: str | None) -> str:
    return _THINK_RE.sub("", text or "").strip()


class LLMClient:
    def __init__(self, settings: Settings | None = None, http_client: Any = None):
        self.settings = settings or get_settings()
        self._client = AsyncOpenAI(
            base_url=self.settings.vllm_endpoint,
            api_key=self.settings.vllm_api_key,
            timeout=self.settings.vllm_timeout,
            max_retries=0,  # tenacity handles retries so we control logging/backoff
            http_client=http_client,  # injectable for tests
        )
        self.model = self.settings.vllm_model

    # ---- low level -------------------------------------------------------

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(4),
        before_sleep=before_sleep_log(log, logging.WARNING),
        reraise=True,
    )
    async def _create(self, **kwargs: Any):
        return await self._client.chat.completions.create(model=self.model, **kwargs)

    def _base_kwargs(self, *, temperature: float | None, max_tokens: int | None, think: bool | None):
        s = self.settings
        enable_thinking = s.vllm_enable_thinking if think is None else think
        return {
            "temperature": s.vllm_temperature if temperature is None else temperature,
            "max_tokens": max_tokens or s.vllm_max_tokens,
            "top_p": s.vllm_top_p,
            "extra_body": {"chat_template_kwargs": {"enable_thinking": enable_thinking}},
        }

    # ---- public ----------------------------------------------------------

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        think: bool | None = None,
    ) -> str:
        try:
            resp = await self._create(
                messages=messages, **self._base_kwargs(temperature=temperature, max_tokens=max_tokens, think=think)
            )
        except APIStatusError as e:
            raise LLMError(f"vLLM request failed: {e.status_code} {e.message}") from e
        choice = resp.choices[0]
        if choice.finish_reason == "length":
            log.warning("LLM output truncated at max_tokens=%s", max_tokens or self.settings.vllm_max_tokens)
        return _strip_think(choice.message.content)

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        schema: type[T],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        think: bool | None = None,
    ) -> T:
        json_schema = schema.model_json_schema()
        kwargs = self._base_kwargs(temperature=temperature, max_tokens=max_tokens, think=think)
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": schema.__name__, "schema": json_schema},
        }
        convo = list(messages)
        last_err: Exception | None = None
        budget = kwargs["max_tokens"]
        for attempt in range(3):
            kwargs["max_tokens"] = budget
            try:
                resp = await self._create(messages=convo, **kwargs)
            except APIStatusError as e:
                raise LLMError(f"vLLM request failed: {e.status_code} {e.message}") from e
            choice = resp.choices[0]
            raw = _strip_think(choice.message.content)
            if choice.finish_reason == "length":
                # Output hit the token budget (typical on long listing pages): widen the budget and ask for
                # a shorter answer instead of feeding back an unparseable prefix.
                last_err = LLMError(f"output truncated at max_tokens={budget}")
                log.warning("LLM JSON truncated for %s (attempt %d, max_tokens=%d)", schema.__name__, attempt, budget)
                budget = min(budget * 2, 32000)
                convo = list(messages) + [
                    {
                        "role": "user",
                        "content": "Your previous answer was cut off because it was too long. Answer again with "
                        "compact JSON (no indentation) and keep only the most important items (max 20 per list).",
                    }
                ]
                continue
            try:
                return schema.model_validate_json(raw)
            except (ValidationError, json.JSONDecodeError) as e:
                last_err = e
                log.warning("LLM JSON invalid for %s (attempt %d): %s", schema.__name__, attempt + 1, e)
                convo = convo + [
                    {"role": "assistant", "content": raw},
                    {"role": "user", "content": f"Your JSON was invalid: {e}\nReturn corrected JSON only."},
                ]
        raise LLMError(f"Could not obtain valid {schema.__name__} from LLM: {last_err}")

    async def healthcheck(self) -> dict[str, Any]:
        models = await self._client.models.list()
        return {"endpoint": self.settings.vllm_endpoint, "models": [m.id for m in models.data]}


_llm: LLMClient | None = None


def get_llm() -> LLMClient:
    global _llm
    if _llm is None:
        _llm = LLMClient()
    return _llm
