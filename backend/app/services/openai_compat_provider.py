import logging
from typing import Dict, Any, Optional, Tuple

import httpx

from app.core.config import settings
from app.services.ai_provider import AIProvider
from app.services.ollama_provider import AIServiceUnavailableException

logger = logging.getLogger(__name__)

# Known hosted providers with permanent (rate-limited, non-expiring) free
# tiers, exposed through OpenAI-compatible /chat/completions endpoints.
# AI_API_BASE_URL / AI_API_MODEL in .env override these defaults, so a model
# retirement or URL change is a two-line config fix, never a code change.
PRESETS: Dict[str, Tuple[str, str]] = {
    "groq": ("https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai", "gemini-2.0-flash"),
    # Generic escape hatch: any OpenAI-compatible host (OpenRouter, Cerebras,
    # Mistral, a self-hosted vLLM, ...). Requires explicit base URL + model.
    "openai_compat": ("", ""),
}


class OpenAICompatProvider(AIProvider):
    """
    Hosted LLM provider speaking the OpenAI chat-completions dialect.
    Drop-in alternative to the local OllamaProvider: same system/user prompt
    in, same raw JSON string out, same AIServiceUnavailableException on
    failure, so every caller and error path behaves identically.
    """

    def __init__(
        self,
        provider_type: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        ptype = (provider_type or settings.AI_PROVIDER_TYPE).lower()
        preset_url, preset_model = PRESETS.get(ptype, ("", ""))

        self.provider_type = ptype
        self.base_url = (base_url or settings.AI_API_BASE_URL or preset_url).rstrip("/")
        self.api_key = api_key or settings.AI_API_KEY
        self.model = model or settings.AI_API_MODEL or preset_model
        self.timeout = timeout or settings.OLLAMA_TIMEOUT

        if not self.base_url or not self.model:
            raise AIServiceUnavailableException(
                f"AI provider '{ptype}' needs AI_API_BASE_URL and AI_API_MODEL set in backend/.env."
            )

    def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[Dict[str, Any]] = None
    ) -> str:
        if not self.api_key:
            raise AIServiceUnavailableException(
                f"AI provider '{self.provider_type}' is selected but AI_API_KEY is not set in backend/.env. "
                "Create a free key (e.g. console.groq.com or aistudio.google.com) and restart."
            )

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            # All call sites expect a raw JSON object string (same contract as
            # Ollama's format:"json"). Both prompt sets mention "JSON", which
            # OpenAI-dialect JSON mode requires.
            "response_format": {"type": "json_object"},
            "stream": False,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}

        logger.info(
            f"[OpenAICompatProvider:{self.provider_type}] Requesting model '{self.model}' at {self.base_url}..."
        )

        try:
            with httpx.Client(timeout=float(self.timeout)) as client:
                response = client.post(url, json=payload, headers=headers)

                if response.status_code == 429:
                    raise AIServiceUnavailableException(
                        "The AI provider's free-tier rate limit was hit. Wait a minute and try again."
                    )
                if response.status_code in (401, 403):
                    raise AIServiceUnavailableException(
                        f"The AI provider rejected the API key (HTTP {response.status_code}). "
                        "Check AI_API_KEY in backend/.env."
                    )
                if response.status_code != 200:
                    # Never echo response bodies to callers - they can contain
                    # provider internals. Log them, return a generic message.
                    logger.error(
                        f"[OpenAICompatProvider:{self.provider_type}] HTTP {response.status_code}: {response.text[:500]}"
                    )
                    raise AIServiceUnavailableException(
                        f"AI provider returned HTTP {response.status_code}. "
                        f"Check that model '{self.model}' is still available."
                    )

                data = response.json()
                choices = data.get("choices") or []
                content = (choices[0].get("message") or {}).get("content", "") if choices else ""

                if not content:
                    logger.error(f"[OpenAICompatProvider:{self.provider_type}] Empty completion content: {str(data)[:500]}")
                    raise AIServiceUnavailableException("AI provider returned an empty response.")

                logger.info(f"[OpenAICompatProvider:{self.provider_type}] AI response received successfully.")
                return content

        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.NetworkError) as e:
            logger.error(f"[OpenAICompatProvider:{self.provider_type}] Network error reaching {self.base_url}: {e}")
            raise AIServiceUnavailableException(
                "AI service is currently unreachable. Check your internet connection."
            )
        except AIServiceUnavailableException:
            raise
        except Exception as e:
            logger.error(f"[OpenAICompatProvider:{self.provider_type}] Unexpected error: {e}")
            raise AIServiceUnavailableException(f"Error during AI generation: {e}")
