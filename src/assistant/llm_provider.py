from __future__ import annotations

import os
import time
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any, Protocol

SUPPORTED_LLM_PROVIDERS = {
    "disabled",
    "gemini",
}

DEFAULT_GEMINI_MODEL = (
    "gemini-3-flash-preview"
)

DEFAULT_TIMEOUT_SECONDS = 30.0
GEMINI_MAX_ATTEMPTS = 3
GEMINI_RETRY_BACKOFF_SECONDS = 1.0

TRANSIENT_GEMINI_ERROR_CODES = {
    503,
    504,
}

TRANSIENT_GEMINI_ERROR_STATUSES = {
    "UNAVAILABLE",
    "DEADLINE_EXCEEDED",
}


def _is_transient_gemini_error(
    exc: Exception,
) -> bool:
    code = getattr(
        exc,
        "code",
        None,
    )

    try:
        normalized_code = int(code)
    except (TypeError, ValueError):
        normalized_code = None

    if (
        normalized_code
        in TRANSIENT_GEMINI_ERROR_CODES
    ):
        return True

    status = str(
        getattr(
            exc,
            "status",
            "",
        )
        or ""
    ).strip().upper()

    return (
        status
        in TRANSIENT_GEMINI_ERROR_STATUSES
    )


@dataclass(
    frozen=True
)
class LLMProviderConfig:
    provider: str
    model: str | None
    api_key: str | None
    timeout_seconds: float


@dataclass(
    frozen=True
)
class LLMGenerationResult:
    provider: str
    model: str | None
    used_llm: bool
    text: str | None
    fallback_reason: str | None = None
    error_type: str | None = None

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return asdict(self)


def load_llm_config(
    env: Mapping[str, str] | None = None,
) -> LLMProviderConfig:
    source = (
        os.environ
        if env is None
        else env
    )

    provider = str(
        source.get(
            "LLM_PROVIDER",
            "disabled",
        )
        or "disabled"
    ).strip().lower()

    if (
        provider
        not in SUPPORTED_LLM_PROVIDERS
    ):
        raise ValueError(
            "Unsupported LLM_PROVIDER: "
            f"{provider}"
        )

    raw_timeout = str(
        source.get(
            "LLM_TIMEOUT_SECONDS",
            DEFAULT_TIMEOUT_SECONDS,
        )
    ).strip()

    try:
        timeout_seconds = float(
            raw_timeout
        )
    except ValueError as exc:
        raise ValueError(
            "LLM_TIMEOUT_SECONDS must "
            "be a positive number."
        ) from exc

    if timeout_seconds <= 0:
        raise ValueError(
            "LLM_TIMEOUT_SECONDS must "
            "be a positive number."
        )

    if provider == "disabled":
        return LLMProviderConfig(
            provider="disabled",
            model=None,
            api_key=None,
            timeout_seconds=(
                timeout_seconds
            ),
        )

    model = str(
        source.get(
            "GEMINI_MODEL",
            DEFAULT_GEMINI_MODEL,
        )
        or DEFAULT_GEMINI_MODEL
    ).strip()

    if not model:
        model = DEFAULT_GEMINI_MODEL

    api_key_value = source.get(
        "GEMINI_API_KEY"
    )

    api_key = (
        str(api_key_value).strip()
        if api_key_value
        else None
    )

    return LLMProviderConfig(
        provider="gemini",
        model=model,
        api_key=api_key,
        timeout_seconds=timeout_seconds,
    )


class LLMProvider(Protocol):
    def generate(
        self,
        prompt: str,
    ) -> LLMGenerationResult:
        ...


def _build_gemini_client(
    config: LLMProviderConfig,
):
    from google import genai
    from google.genai import types

    timeout_ms = int(
        config.timeout_seconds
        * 1000
    )

    return genai.Client(
        api_key=config.api_key,
        http_options=types.HttpOptions(
            timeout=timeout_ms,
        ),
    )


@dataclass(
    frozen=True
)
class DisabledLLMProvider:
    config: LLMProviderConfig

    def generate(
        self,
        prompt: str,
    ) -> LLMGenerationResult:
        del prompt

        return LLMGenerationResult(
            provider="disabled",
            model=None,
            used_llm=False,
            text=None,
            fallback_reason=(
                "provider_disabled"
            ),
        )


@dataclass(
    frozen=True
)
class GeminiLLMProvider:
    config: LLMProviderConfig
    client: Any | None = None

    def generate(
        self,
        prompt: str,
    ) -> LLMGenerationResult:
        if (
            not self.config.api_key
            and self.client is None
        ):
            return LLMGenerationResult(
                provider="gemini",
                model=self.config.model,
                used_llm=False,
                text=None,
                fallback_reason=(
                    "missing_api_key"
                ),
            )

        try:
            active_client = (
                self.client
                if self.client is not None
                else _build_gemini_client(
                    self.config
                )
            )

        except Exception as exc:
            return LLMGenerationResult(
                provider="gemini",
                model=self.config.model,
                used_llm=False,
                text=None,
                fallback_reason=(
                    "provider_error"
                ),
                error_type=(
                    type(exc).__name__
                ),
            )

        for attempt in range(
            1,
            GEMINI_MAX_ATTEMPTS + 1,
        ):
            try:
                response = (
                    active_client
                    .models
                    .generate_content(
                        model=self.config.model,
                        contents=prompt,
                    )
                )

                break

            except Exception as exc:
                should_retry = (
                    _is_transient_gemini_error(
                        exc
                    )
                    and attempt
                    < GEMINI_MAX_ATTEMPTS
                )

                if not should_retry:
                    return LLMGenerationResult(
                        provider="gemini",
                        model=self.config.model,
                        used_llm=False,
                        text=None,
                        fallback_reason=(
                            "provider_error"
                        ),
                        error_type=(
                            type(exc).__name__
                        ),
                    )

                delay_seconds = (
                    GEMINI_RETRY_BACKOFF_SECONDS
                    * (
                        2
                        ** (attempt - 1)
                    )
                )

                time.sleep(
                    delay_seconds
                )

        response_text = getattr(
            response,
            "text",
            None,
        )

        if response_text is None:
            return LLMGenerationResult(
                provider="gemini",
                model=self.config.model,
                used_llm=False,
                text=None,
                fallback_reason=(
                    "empty_response"
                ),
            )

        normalized_text = str(
            response_text
        ).strip()

        if not normalized_text:
            return LLMGenerationResult(
                provider="gemini",
                model=self.config.model,
                used_llm=False,
                text=None,
                fallback_reason=(
                    "empty_response"
                ),
            )

        return LLMGenerationResult(
            provider="gemini",
            model=self.config.model,
            used_llm=True,
            text=normalized_text,
        )


def build_llm_provider(
    config: LLMProviderConfig,
    *,
    client: Any | None = None,
) -> LLMProvider:
    if config.provider == "disabled":
        return DisabledLLMProvider(
            config=config
        )

    if config.provider == "gemini":
        return GeminiLLMProvider(
            config=config,
            client=client,
        )

    raise ValueError(
        "Unsupported LLM provider: "
        f"{config.provider}"
    )


def generate_llm_text(
    prompt: str,
    *,
    config: LLMProviderConfig | None = None,
    client: Any | None = None,
) -> LLMGenerationResult:
    if (
        not isinstance(prompt, str)
        or not prompt.strip()
    ):
        raise ValueError(
            "prompt must be a "
            "non-empty string."
        )

    resolved_config = (
        config
        if config is not None
        else load_llm_config()
    )

    provider = build_llm_provider(
        resolved_config,
        client=client,
    )

    return provider.generate(
        prompt
    )