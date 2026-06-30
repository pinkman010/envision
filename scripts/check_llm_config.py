from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import settings


def main() -> int:
    effective_thinking_type = "disabled" if settings.LLM_THINKING_DISABLED else settings.LLM_THINKING_TYPE
    result = {
        "status": "ok",
        "llm_config_present": True,
        "api_key_present": bool(settings.LLM_API_KEY),
        "api_key_length": len(settings.LLM_API_KEY or ""),
        "base_url": settings.LLM_BASE_URL,
        "model": settings.LLM_MODEL,
        "thinking_type": settings.LLM_THINKING_TYPE,
        "effective_thinking_type": effective_thinking_type,
        "reasoning_effort": settings.LLM_REASONING_EFFORT,
        "response_format": settings.LLM_RESPONSE_FORMAT or None,
        "temperature_will_be_sent": effective_thinking_type != "enabled",
        "notes": [
            "api key value is intentionally not printed",
            "thinking enabled means temperature/top_p/presence_penalty/frequency_penalty are not sent",
        ],
        "errors": [],
    }

    if not result["api_key_present"]:
        result["status"] = "failed"
        result["errors"].append("LLM_API_KEY is missing")
    if settings.LLM_BASE_URL.rstrip("/") != "https://api.deepseek.com":
        result["errors"].append("LLM_BASE_URL is not https://api.deepseek.com")
    if settings.LLM_MODEL != "deepseek-v4-flash":
        result["errors"].append("LLM_MODEL is not deepseek-v4-flash")
    if result["errors"]:
        result["status"] = "failed"

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
