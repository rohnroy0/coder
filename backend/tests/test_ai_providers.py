"""
tests/test_ai_providers.py
==========================
Provider selection (AI_PROVIDER_TYPE) and the hosted OpenAI-compatible
provider used for Groq / Gemini free tiers.
"""
import pytest

from app.core.config import settings
from app.services.ai_provider import build_default_provider, MockAIProvider
from app.services.ollama_provider import OllamaProvider, AIServiceUnavailableException
from app.services import openai_compat_provider
from app.services.openai_compat_provider import OpenAICompatProvider


# ─── Factory selection ────────────────────────────────────────────────────────

class TestProviderFactory:
    def test_default_is_ollama(self, monkeypatch):
        monkeypatch.setattr(settings, "AI_PROVIDER_TYPE", "ollama")
        assert isinstance(build_default_provider(), OllamaProvider)

    def test_mock_selected(self, monkeypatch):
        monkeypatch.setattr(settings, "AI_PROVIDER_TYPE", "mock")
        assert isinstance(build_default_provider(), MockAIProvider)

    def test_groq_uses_preset_url_and_model(self, monkeypatch):
        monkeypatch.setattr(settings, "AI_PROVIDER_TYPE", "groq")
        monkeypatch.setattr(settings, "AI_API_KEY", "k")
        monkeypatch.setattr(settings, "AI_API_BASE_URL", "")
        monkeypatch.setattr(settings, "AI_API_MODEL", "")
        provider = build_default_provider()
        assert isinstance(provider, OpenAICompatProvider)
        assert provider.base_url == "https://api.groq.com/openai/v1"
        assert provider.model  # preset model filled in

    def test_env_overrides_preset(self, monkeypatch):
        monkeypatch.setattr(settings, "AI_PROVIDER_TYPE", "gemini")
        monkeypatch.setattr(settings, "AI_API_KEY", "k")
        monkeypatch.setattr(settings, "AI_API_BASE_URL", "https://example.com/v1/")
        monkeypatch.setattr(settings, "AI_API_MODEL", "custom-model")
        provider = build_default_provider()
        assert provider.base_url == "https://example.com/v1"  # trailing slash stripped
        assert provider.model == "custom-model"

    def test_openai_compat_requires_explicit_url_and_model(self, monkeypatch):
        monkeypatch.setattr(settings, "AI_PROVIDER_TYPE", "openai_compat")
        monkeypatch.setattr(settings, "AI_API_BASE_URL", "")
        monkeypatch.setattr(settings, "AI_API_MODEL", "")
        with pytest.raises(AIServiceUnavailableException):
            build_default_provider()


# ─── Hosted provider behavior (HTTP stubbed) ─────────────────────────────────

class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text

    def json(self):
        return self._payload


class FakeClient:
    """Stands in for httpx.Client; returns a canned response."""
    response = FakeResponse()
    last_request = None

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def post(self, url, json=None, headers=None):
        FakeClient.last_request = {"url": url, "json": json, "headers": headers}
        return FakeClient.response


@pytest.fixture
def provider():
    return OpenAICompatProvider(
        provider_type="groq", base_url="https://api.groq.com/openai/v1",
        api_key="test-key", model="test-model",
    )


@pytest.fixture
def fake_http(monkeypatch):
    monkeypatch.setattr(openai_compat_provider.httpx, "Client", FakeClient)
    return FakeClient


class TestOpenAICompatProvider:
    def test_success_returns_message_content(self, provider, fake_http):
        fake_http.response = FakeResponse(200, {
            "choices": [{"message": {"content": '{"ok": true}'}}]
        })
        out = provider.generate_structured_response("sys", "user")
        assert out == '{"ok": true}'
        req = fake_http.last_request
        assert req["url"] == "https://api.groq.com/openai/v1/chat/completions"
        assert req["headers"]["Authorization"] == "Bearer test-key"
        assert req["json"]["response_format"] == {"type": "json_object"}
        assert req["json"]["messages"][0] == {"role": "system", "content": "sys"}

    def test_missing_api_key_raises_before_any_request(self, fake_http):
        p = OpenAICompatProvider(provider_type="groq", base_url="https://x", api_key="", model="m")
        fake_http.last_request = None
        with pytest.raises(AIServiceUnavailableException, match="AI_API_KEY"):
            p.generate_structured_response("sys", "user")
        assert fake_http.last_request is None

    def test_rate_limit_maps_to_clear_message(self, provider, fake_http):
        fake_http.response = FakeResponse(429)
        with pytest.raises(AIServiceUnavailableException, match="rate limit"):
            provider.generate_structured_response("sys", "user")

    def test_rejected_key_maps_to_clear_message(self, provider, fake_http):
        fake_http.response = FakeResponse(401)
        with pytest.raises(AIServiceUnavailableException, match="AI_API_KEY"):
            provider.generate_structured_response("sys", "user")

    def test_server_error_does_not_leak_body(self, provider, fake_http):
        fake_http.response = FakeResponse(500, text="internal secret trace")
        with pytest.raises(AIServiceUnavailableException) as exc:
            provider.generate_structured_response("sys", "user")
        assert "internal secret trace" not in str(exc.value)

    def test_empty_content_raises(self, provider, fake_http):
        fake_http.response = FakeResponse(200, {"choices": [{"message": {"content": ""}}]})
        with pytest.raises(AIServiceUnavailableException, match="empty"):
            provider.generate_structured_response("sys", "user")
