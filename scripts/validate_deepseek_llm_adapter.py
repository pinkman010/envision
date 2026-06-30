from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


class FakeCompletions:
    def __init__(self, responses: List[Any]) -> None:
        self.responses = responses
        self.calls: List[Dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if not self.responses:
            raise AssertionError("fake client exhausted; no network call is allowed")
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


class FakeClient:
    def __init__(self, completions: FakeCompletions) -> None:
        self.chat = SimpleNamespace(completions=completions)


def make_response(
    content: str,
    *,
    finish_reason: str = "stop",
    usage: Any = None,
    reasoning_content: str | None = None,
) -> Any:
    message = SimpleNamespace(content=content)
    if reasoning_content is not None:
        message.reasoning_content = reasoning_content
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message, finish_reason=finish_reason)],
        usage=usage,
    )


def main() -> int:
    errors: List[str] = []

    try:
        from src.utils import llm_utils

        llm_utils.LLM_THINKING_TYPE = "enabled"
        llm_utils.LLM_REASONING_EFFORT = "max"
        llm_utils.LLM_RESPONSE_FORMAT = "json_object"
        llm_utils.LLM_MAX_RETRIES = 2
        llm_utils.LLM_RETRY_DELAY = 0

        usage = SimpleNamespace(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            prompt_cache_hit_tokens=7,
            prompt_cache_miss_tokens=3,
            completion_tokens_details=SimpleNamespace(reasoning_tokens=2),
        )
        completions = FakeCompletions([make_response('{"ok": true}', usage=usage)])
        llm_utils._client = FakeClient(completions)

        metadata_result = llm_utils.call_llm_with_metadata(
            messages=[{"role": "user", "content": "return json"}],
            temperature=0.7,
            max_tokens=128,
            timeout=30,
        )
        params = completions.calls[0]

        if "temperature" in params:
            errors.append("thinking enabled should not send temperature")
        if params.get("reasoning_effort") != "max":
            errors.append("reasoning_effort=max was not sent")
        if params.get("extra_body", {}).get("thinking", {}).get("type") != "enabled":
            errors.append("extra_body.thinking.type=enabled was not sent")
        if params.get("response_format", {}).get("type") != "json_object":
            errors.append("response_format=json_object was not sent")
        if metadata_result.get("content") != '{"ok": true}':
            errors.append("call_llm_with_metadata did not return expected content")
        metadata = metadata_result.get("metadata", {})
        if metadata.get("finish_reason") != "stop":
            errors.append("finish_reason was not preserved in metadata")
        usage_result = metadata.get("usage", {})
        if usage_result.get("prompt_cache_hit_tokens") != 7:
            errors.append("prompt_cache_hit_tokens was not preserved")
        details = usage_result.get("completion_tokens_details", {})
        if details.get("reasoning_tokens") != 2:
            errors.append("reasoning_tokens was not preserved")

        completions = FakeCompletions([make_response('{"string": true}')])
        llm_utils._client = FakeClient(completions)
        string_result = llm_utils.call_llm(
            messages=[{"role": "user", "content": "return json"}],
            temperature=0.7,
            max_tokens=128,
            timeout=30,
        )
        if string_result != '{"string": true}':
            errors.append("call_llm should keep returning a content string")

        completions = FakeCompletions(
            [
                make_response('{"too_long": true}', finish_reason="length"),
                make_response('{"retried": true}', finish_reason="stop"),
            ]
        )
        llm_utils._client = FakeClient(completions)
        retry_result = llm_utils.call_llm_with_metadata(
            messages=[{"role": "user", "content": "return json"}],
            max_tokens=128,
            timeout=30,
        )
        if retry_result.get("content") != '{"retried": true}':
            errors.append("finish_reason=length did not retry to a valid response")
        if len(completions.calls) != 2:
            errors.append("finish_reason=length should trigger exactly one retry in this scenario")

    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    result = {"status": "ok" if not errors else "failed", "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
