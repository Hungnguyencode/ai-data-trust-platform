from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.assistant.llm_provider import (
    DEFAULT_GEMINI_MODEL,
    DisabledLLMProvider,
    GeminiLLMProvider,
    LLMProviderConfig,
    _build_gemini_client,
    build_llm_provider,
    generate_llm_text,
    load_llm_config,
)


def test_disabled_provider_is_default():
    config = load_llm_config(
        {}
    )

    assert (
        config.provider
        == "disabled"
    )

    assert config.model is None
    assert config.api_key is None

    assert (
        config.timeout_seconds
        == 30.0
    )


def test_gemini_config_is_loaded():
    config = load_llm_config(
        {
            "LLM_PROVIDER": "gemini",
            "GEMINI_MODEL": (
                "gemini-test-model"
            ),
            "GEMINI_API_KEY": (
                "fake-key"
            ),
            "LLM_TIMEOUT_SECONDS": (
                "12"
            ),
        }
    )

    assert config.provider == "gemini"

    assert (
        config.model
        == "gemini-test-model"
    )

    assert (
        config.api_key
        == "fake-key"
    )

    assert (
        config.timeout_seconds
        == 12.0
    )


def test_gemini_default_model():
    config = load_llm_config(
        {
            "LLM_PROVIDER": "gemini",
        }
    )

    assert (
        config.model
        == DEFAULT_GEMINI_MODEL
    )


def test_invalid_provider_is_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "Unsupported LLM_PROVIDER"
        ),
    ):
        load_llm_config(
            {
                "LLM_PROVIDER": (
                    "magic"
                )
            }
        )


@pytest.mark.parametrize(
    "timeout",
    [
        "0",
        "-1",
        "bad",
    ],
)
def test_invalid_timeout_is_rejected(
    timeout,
):
    with pytest.raises(
        ValueError,
        match=(
            "LLM_TIMEOUT_SECONDS"
        ),
    ):
        load_llm_config(
            {
                "LLM_TIMEOUT_SECONDS": (
                    timeout
                )
            }
        )


def test_disabled_provider_returns_fallback():
    config = LLMProviderConfig(
        provider="disabled",
        model=None,
        api_key=None,
        timeout_seconds=30.0,
    )

    result = generate_llm_text(
        "Explain this dataset.",
        config=config,
    )

    assert result.used_llm is False
    assert result.text is None

    assert (
        result.fallback_reason
        == "provider_disabled"
    )


def test_missing_gemini_key_returns_fallback():
    config = LLMProviderConfig(
        provider="gemini",
        model="gemini-test-model",
        api_key=None,
        timeout_seconds=30.0,
    )

    result = generate_llm_text(
        "Explain this dataset.",
        config=config,
    )

    assert result.used_llm is False
    assert result.text is None

    assert (
        result.fallback_reason
        == "missing_api_key"
    )


def test_gemini_client_converts_timeout_to_ms(
    monkeypatch,
):
    captured = {}

    def fake_client(
        *,
        api_key,
        http_options,
    ):
        captured[
            "api_key"
        ] = api_key

        captured[
            "timeout"
        ] = http_options.timeout

        return SimpleNamespace()

    monkeypatch.setattr(
        "google.genai.Client",
        fake_client,
    )

    config = LLMProviderConfig(
        provider="gemini",
        model="gemini-test-model",
        api_key="fake-key",
        timeout_seconds=12.5,
    )

    _build_gemini_client(
        config
    )

    assert (
        captured["api_key"]
        == "fake-key"
    )

    assert (
        captured["timeout"]
        == 12500
    )


def test_provider_factory_builds_disabled():
    config = LLMProviderConfig(
        provider="disabled",
        model=None,
        api_key=None,
        timeout_seconds=30.0,
    )

    provider = build_llm_provider(
        config
    )

    assert isinstance(
        provider,
        DisabledLLMProvider,
    )


def test_provider_factory_builds_gemini():
    fake_client = SimpleNamespace()

    config = LLMProviderConfig(
        provider="gemini",
        model="gemini-test-model",
        api_key="fake-key",
        timeout_seconds=30.0,
    )

    provider = build_llm_provider(
        config,
        client=fake_client,
    )

    assert isinstance(
        provider,
        GeminiLLMProvider,
    )

    assert (
        provider.client
        is fake_client
    )


def test_provider_factory_rejects_unsupported():
    config = LLMProviderConfig(
        provider="magic",
        model=None,
        api_key=None,
        timeout_seconds=30.0,
    )

    with pytest.raises(
        ValueError,
        match=(
            "Unsupported LLM provider"
        ),
    ):
        build_llm_provider(
            config
        )


def test_gemini_success():
    class FakeModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            assert (
                model
                == "gemini-test-model"
            )

            assert (
                contents
                == "Grounded evidence."
            )

            return SimpleNamespace(
                text=(
                    "Grounded LLM answer."
                )
            )

    fake_client = SimpleNamespace(
        models=FakeModels()
    )

    config = LLMProviderConfig(
        provider="gemini",
        model="gemini-test-model",
        api_key="fake-key",
        timeout_seconds=30.0,
    )

    result = generate_llm_text(
        "Grounded evidence.",
        config=config,
        client=fake_client,
    )

    assert result.used_llm is True

    assert (
        result.text
        == "Grounded LLM answer."
    )

    assert (
        result.fallback_reason
        is None
    )


def test_empty_response_returns_fallback():
    class FakeModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            return SimpleNamespace(
                text="   "
            )

    fake_client = SimpleNamespace(
        models=FakeModels()
    )

    config = LLMProviderConfig(
        provider="gemini",
        model="gemini-test-model",
        api_key="fake-key",
        timeout_seconds=30.0,
    )

    result = generate_llm_text(
        "Grounded evidence.",
        config=config,
        client=fake_client,
    )

    assert result.used_llm is False

    assert (
        result.fallback_reason
        == "empty_response"
    )


def test_provider_exception_is_safe():
    class FakeModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            raise RuntimeError(
                "provider failed"
            )

    fake_client = SimpleNamespace(
        models=FakeModels()
    )

    config = LLMProviderConfig(
        provider="gemini",
        model="gemini-test-model",
        api_key="fake-key",
        timeout_seconds=30.0,
    )

    result = generate_llm_text(
        "Grounded evidence.",
        config=config,
        client=fake_client,
    )

    assert result.used_llm is False
    assert result.text is None

    assert (
        result.fallback_reason
        == "provider_error"
    )

    assert (
        result.error_type
        == "RuntimeError"
    )


@pytest.mark.parametrize(
    "prompt",
    [
        "",
        "   ",
        None,
    ],
)
def test_invalid_prompt_is_rejected(
    prompt,
):
    with pytest.raises(
        ValueError,
        match=(
            "prompt must be a "
            "non-empty string"
        ),
    ):
        generate_llm_text(
            prompt
        )