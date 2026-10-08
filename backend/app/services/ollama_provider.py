import httpx
import logging
from typing import Dict, Any, Optional
from app.core.config import settings
from app.services.ai_provider import AIProvider

logger = logging.getLogger(__name__)

class AIServiceUnavailableException(Exception):
    """Exception raised when Ollama service is unreachable or errors out."""
    pass

class OllamaProvider(AIProvider):
    """
    Ollama API Provider for local LLM text & JSON generation.
    Connects to OLLAMA_BASE_URL and uses OLLAMA_MODEL.
    """

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None, timeout: Optional[int] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT

    def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[Dict[str, Any]] = None
    ) -> str:
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "format": "json"
        }

        logger.info(f"[OllamaProvider] Starting AI generation request using model '{self.model}' at {url}...")

        try:
            with httpx.Client(timeout=float(self.timeout)) as client:
                response = client.post(url, json=payload)
                
                if response.status_code != 200:
                    logger.error(f"[OllamaProvider] Ollama returned status {response.status_code}: {response.text}")
                    raise AIServiceUnavailableException(
                        f"Ollama returned HTTP status {response.status_code}. Make sure model '{self.model}' is pulled."
                    )

                result_json = response.json()
                content = result_json.get("message", {}).get("content", "")
                
                if not content:
                    logger.error("[OllamaProvider] Ollama returned empty message content.")
                    raise AIServiceUnavailableException("Ollama returned empty response content.")

                logger.info("[OllamaProvider] AI response received successfully.")
                return content

        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.NetworkError) as e:
            logger.error(f"[OllamaProvider] Failed to connect to Ollama at {self.base_url}: {str(e)}")
            raise AIServiceUnavailableException(
                "AI service is currently unavailable. Please make sure Ollama is running."
            )
        except Exception as e:
            if isinstance(e, AIServiceUnavailableException):
                raise e
            logger.error(f"[OllamaProvider] Unexpected error communicating with Ollama: {str(e)}")
            raise AIServiceUnavailableException(f"Error during AI generation: {str(e)}")
