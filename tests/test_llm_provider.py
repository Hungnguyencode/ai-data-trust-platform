from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.assistant.llm_provider import (
    DEFAULT_GEMINI_MODEL,
    DisabledLLMProvider,
    GeminiLLMProvider,
    LLMConfigurationError,
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


def test_ollama_config_is_loaded():
    config = load_llm_config(
        {
            "LLM_PROVIDER": "ollama",
            "OLLAMA_MODEL": (
                "ollama-test-model"
            ),
            "OLLAMA_BASE_URL": (
                "http://127.0.0.1:11434"
            ),
            "LLM_TIMEOUT_SECONDS": (
                "45"
            ),
        }
    )

    assert config.provider == "ollama"

    assert (
        config.model
        == "ollama-test-model"
    )

    assert config.api_key is None

    assert (
        config.base_url
        == "http://127.0.0.1:11434"
    )

    assert (
        config.timeout_seconds
        == 45.0
    )


def test_ollama_requires_model():
    with pytest.raises(
        LLMConfigurationError,
        match="OLLAMA_MODEL",
    ):
        load_llm_config(
            {
                "LLM_PROVIDER": "ollama",
            }
        )


def test_invalid_provider_is_rejected():
    with pytest.raises(
        LLMConfigurationError,
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
        LLMConfigurationError,
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


def test_ollama_success():
    captured = {}

    class FakeResponse:
        def raise_for_status(
            self,
        ):
            return None

        def json(
            self,
        ):
            return {
                "response": (
                    "Grounded local answer."
                )
            }

    class FakeClient:
        def post(
            self,
            url,
            *,
            json,
            timeout,
        ):
            captured["url"] = url
            captured["json"] = json
            captured["timeout"] = timeout

            return FakeResponse()

    fake_client = FakeClient()

    config = LLMProviderConfig(
        provider="ollama",
        model="ollama-test-model",
        api_key=None,
        timeout_seconds=45.0,
        base_url=(
            "http://127.0.0.1:11434"
        ),
    )

    result = generate_llm_text(
        "Grounded evidence.",
        config=config,
        client=fake_client,
    )

    assert (
        captured["url"]
        == (
            "http://127.0.0.1:11434"
            "/api/generate"
        )
    )

    assert captured["json"] == {
        "model": "ollama-test-model",
        "prompt": "Grounded evidence.",
        "stream": False,
    }

    assert captured["timeout"] == 45.0

    assert result.provider == "ollama"

    assert (
        result.model
        == "ollama-test-model"
    )

    assert result.used_llm is True

    assert (
        result.text
        == "Grounded local answer."
    )

    assert result.fallback_reason is None
    assert result.error_type is None


def test_ollama_provider_error_returns_fallback():
    class FakeClient:
        def post(
            self,
            url,
            *,
            json,
            timeout,
        ):
            del url
            del json
            del timeout

            raise RuntimeError(
                "ollama unavailable"
            )

    config = LLMProviderConfig(
        provider="ollama",
        model="ollama-test-model",
        api_key=None,
        timeout_seconds=30.0,
        base_url=(
            "http://127.0.0.1:11434"
        ),
    )

    result = generate_llm_text(
        "Grounded evidence.",
        config=config,
        client=FakeClient(),
    )

    assert result.provider == "ollama"

    assert (
        result.model
        == "ollama-test-model"
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


def test_ollama_empty_response_returns_fallback():
    class FakeResponse:
        def raise_for_status(
            self,
        ):
            return None

        def json(
            self,
        ):
            return {
                "response": "   "
            }

    class FakeClient:
        def post(
            self,
            url,
            *,
            json,
            timeout,
        ):
            del url
            del json
            del timeout

            return FakeResponse()

    config = LLMProviderConfig(
        provider="ollama",
        model="ollama-test-model",
        api_key=None,
        timeout_seconds=30.0,
        base_url=(
            "http://127.0.0.1:11434"
        ),
    )

    result = generate_llm_text(
        "Grounded evidence.",
        config=config,
        client=FakeClient(),
    )

    assert result.provider == "ollama"

    assert (
        result.model
        == "ollama-test-model"
    )

    assert result.used_llm is False
    assert result.text is None

    assert (
        result.fallback_reason
        == "empty_response"
    )

    assert result.error_type is None


def test_ollama_retries_transient_503(
    monkeypatch,
):
    class FakeErrorResponse:
        status_code = 503

    class FakeHttpError(Exception):
        def __init__(self):
            super().__init__(
                "Ollama temporarily unavailable"
            )
            self.response = (
                FakeErrorResponse()
            )

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "response": (
                    "Recovered local answer."
                )
            }

    class FakeClient:
        def __init__(self):
            self.calls = 0

        def post(
            self,
            url,
            *,
            json,
            timeout,
        ):
            self.calls += 1

            if self.calls == 1:
                raise FakeHttpError()

            return FakeResponse()

    sleep_calls = []

    monkeypatch.setattr(
        "src.assistant.llm_provider.time.sleep",
        lambda seconds: (
            sleep_calls.append(seconds)
        ),
    )

    fake_client = FakeClient()

    config = LLMProviderConfig(
        provider="ollama",
        model="ollama-test-model",
        api_key=None,
        timeout_seconds=45.0,
        base_url=(
            "http://127.0.0.1:11434"
        ),
    )

    result = generate_llm_text(
        "Grounded evidence.",
        config=config,
        client=fake_client,
    )

    assert fake_client.calls == 2
    assert sleep_calls == [1.0]

    assert result.provider == "ollama"
    assert result.model == (
        "ollama-test-model"
    )
    assert result.used_llm is True
    assert result.text == (
        "Recovered local answer."
    )
    assert result.fallback_reason is None
    assert result.error_type is None


def test_ollama_transient_503_exhausts_retries(
    monkeypatch,
):
    class FakeErrorResponse:
        status_code = 503

    class FakeHttpError(Exception):
        def __init__(self):
            super().__init__(
                "Ollama temporarily unavailable"
            )
            self.response = (
                FakeErrorResponse()
            )

    class FakeClient:
        def __init__(self):
            self.calls = 0

        def post(
            self,
            url,
            *,
            json,
            timeout,
        ):
            self.calls += 1
            raise FakeHttpError()

    sleep_calls = []

    monkeypatch.setattr(
        "src.assistant.llm_provider.time.sleep",
        lambda seconds: (
            sleep_calls.append(seconds)
        ),
    )

    fake_client = FakeClient()

    config = LLMProviderConfig(
        provider="ollama",
        model="ollama-test-model",
        api_key=None,
        timeout_seconds=45.0,
        base_url=(
            "http://127.0.0.1:11434"
        ),
    )

    result = generate_llm_text(
        "Grounded evidence.",
        config=config,
        client=fake_client,
    )

    assert fake_client.calls == 3
    assert sleep_calls == [
        1.0,
        2.0,
    ]

    assert result.provider == "ollama"
    assert result.model == (
        "ollama-test-model"
    )
    assert result.used_llm is False
    assert result.text is None
    assert (
        result.fallback_reason
        == "provider_error"
    )
    assert (
        result.error_type
        == "FakeHttpError"
    )


def test_ollama_does_not_retry_non_transient_401(
    monkeypatch,
):
    class FakeErrorResponse:
        status_code = 401

    class FakeHttpError(Exception):
        def __init__(self):
            super().__init__(
                "Ollama request rejected"
            )
            self.response = (
                FakeErrorResponse()
            )

    class FakeClient:
        def __init__(self):
            self.calls = 0

        def post(
            self,
            url,
            *,
            json,
            timeout,
        ):
            self.calls += 1
            raise FakeHttpError()

    sleep_calls = []

    monkeypatch.setattr(
        "src.assistant.llm_provider.time.sleep",
        lambda seconds: (
            sleep_calls.append(seconds)
        ),
    )

    fake_client = FakeClient()

    config = LLMProviderConfig(
        provider="ollama",
        model="ollama-test-model",
        api_key=None,
        timeout_seconds=45.0,
        base_url=(
            "http://127.0.0.1:11434"
        ),
    )

    result = generate_llm_text(
        "Grounded evidence.",
        config=config,
        client=fake_client,
    )

    assert fake_client.calls == 1
    assert sleep_calls == []

    assert result.provider == "ollama"
    assert result.model == (
        "ollama-test-model"
    )
    assert result.used_llm is False
    assert result.text is None
    assert (
        result.fallback_reason
        == "provider_error"
    )
    assert (
        result.error_type
        == "FakeHttpError"
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


def test_gemini_retries_503_then_succeeds(
    monkeypatch,
):
    sleep_calls = []

    class FakeProviderError(Exception):
        def __init__(
            self,
            *,
            code,
            status,
        ):
            super().__init__(status)
            self.code = code
            self.status = status

    class FakeModels:
        def __init__(self):
            self.calls = 0

        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            self.calls += 1

            if self.calls == 1:
                raise FakeProviderError(
                    code=503,
                    status="UNAVAILABLE",
                )

            return SimpleNamespace(
                text=(
                    "Recovered after retry."
                )
            )

    models = FakeModels()

    fake_client = SimpleNamespace(
        models=models
    )

    monkeypatch.setattr(
        "src.assistant.llm_provider.time.sleep",
        lambda seconds: sleep_calls.append(
            seconds
        ),
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

    assert models.calls == 2
    assert sleep_calls == [1.0]

    assert result.used_llm is True

    assert (
        result.text
        == "Recovered after retry."
    )

    assert result.fallback_reason is None


def test_gemini_retries_504_with_backoff_then_succeeds(
    monkeypatch,
):
    sleep_calls = []

    class FakeProviderError(Exception):
        def __init__(
            self,
            *,
            code,
            status,
        ):
            super().__init__(status)
            self.code = code
            self.status = status

    class FakeModels:
        def __init__(self):
            self.calls = 0

        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            self.calls += 1

            if self.calls <= 2:
                raise FakeProviderError(
                    code=504,
                    status=(
                        "DEADLINE_EXCEEDED"
                    ),
                )

            return SimpleNamespace(
                text=(
                    "Recovered on third attempt."
                )
            )

    models = FakeModels()

    fake_client = SimpleNamespace(
        models=models
    )

    monkeypatch.setattr(
        "src.assistant.llm_provider.time.sleep",
        lambda seconds: sleep_calls.append(
            seconds
        ),
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

    assert models.calls == 3

    assert sleep_calls == [
        1.0,
        2.0,
    ]

    assert result.used_llm is True

    assert (
        result.text
        == "Recovered on third attempt."
    )

    assert result.fallback_reason is None


def test_gemini_does_not_retry_non_transient_error(
    monkeypatch,
):
    sleep_calls = []

    class FakeProviderError(Exception):
        def __init__(
            self,
            *,
            code,
            status,
        ):
            super().__init__(status)
            self.code = code
            self.status = status

    class FakeModels:
        def __init__(self):
            self.calls = 0

        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            self.calls += 1

            raise FakeProviderError(
                code=401,
                status="UNAUTHENTICATED",
            )

    models = FakeModels()

    fake_client = SimpleNamespace(
        models=models
    )

    monkeypatch.setattr(
        "src.assistant.llm_provider.time.sleep",
        lambda seconds: sleep_calls.append(
            seconds
        ),
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

    assert models.calls == 1
    assert sleep_calls == []

    assert result.used_llm is False
    assert result.text is None

    assert (
        result.fallback_reason
        == "provider_error"
    )

    assert (
        result.error_type
        == "FakeProviderError"
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
