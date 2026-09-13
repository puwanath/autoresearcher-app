"""openai>=3 talks through the vendored `httpx2`, so we inject a MockTransport instead of using respx."""

import json

import httpx2
import pytest
from openai import DefaultAsyncHttpxClient
from pydantic import BaseModel, Field

from app.config import Settings
from app.llm.client import LLMClient, LLMError


class Out(BaseModel):
    n: int = Field(ge=1)


def _ok(content: str, finish="stop") -> httpx2.Response:
    return httpx2.Response(
        200,
        json={
            "id": "x",
            "object": "chat.completion",
            "created": 0,
            "model": "m",
            "choices": [{"index": 0, "finish_reason": finish, "message": {"role": "assistant", "content": content}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        },
    )


class Mock:
    """Sequence of responses (or exceptions); records request bodies."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests: list[dict] = []

    def client(self) -> LLMClient:
        def handler(request: httpx2.Request) -> httpx2.Response:
            self.requests.append(json.loads(request.content))
            r = self.responses.pop(0)
            if isinstance(r, Exception):
                raise r
            return r

        http = DefaultAsyncHttpxClient(transport=httpx2.MockTransport(handler))
        settings = Settings(vllm_endpoint="http://vllm.test/v1", vllm_timeout=5, _env_file=None)
        return LLMClient(settings, http_client=http)


@pytest.mark.asyncio
async def test_chat_strips_think_and_disables_thinking():
    m = Mock(_ok("<think>hmm</think>hello"))
    assert await m.client().chat([{"role": "user", "content": "hi"}]) == "hello"
    assert m.requests[0]["chat_template_kwargs"] == {"enable_thinking": False}


@pytest.mark.asyncio
async def test_chat_json_retries_on_validation_error():
    m = Mock(_ok('{"n": 0}'), _ok('{"n": 3}'))
    out = await m.client().chat_json([{"role": "user", "content": "go"}], Out)
    assert out.n == 3 and len(m.requests) == 2
    assert m.requests[1]["response_format"]["type"] == "json_schema"
    assert "invalid" in m.requests[1]["messages"][-1]["content"]


@pytest.mark.asyncio
async def test_chat_json_gives_up():
    m = Mock(_ok('{"n": 0}'), _ok('{"n": 0}'), _ok('{"n": 0}'))
    with pytest.raises(LLMError):
        await m.client().chat_json([{"role": "user", "content": "go"}], Out)


@pytest.mark.asyncio
async def test_transport_errors_are_retried():
    m = Mock(httpx2.ConnectError("down"), _ok("back"))
    assert await m.client().chat([{"role": "user", "content": "hi"}]) == "back"
    assert len(m.requests) == 2


@pytest.mark.asyncio
async def test_chat_json_truncation_retries_with_bigger_budget():
    m = Mock(_ok('{"n": ', finish="length"), _ok('{"n": 7}'))
    out = await m.client().chat_json([{"role": "user", "content": "go"}], Out, max_tokens=1000)
    assert out.n == 7
    assert m.requests[0]["max_tokens"] == 1000 and m.requests[1]["max_tokens"] == 2000
    assert "cut off" in m.requests[1]["messages"][-1]["content"]
    assert m.requests[1]["messages"][0]["content"] == "go"  # truncated prefix is not echoed back
