import time
import logging
import requests
from typing import Dict, Any, Tuple, Optional
from flask import current_app

logger = logging.getLogger("rag_backend.services.nvidia_client")

class LLMServiceError(Exception):
    """Base exception for LLM service failures."""
    pass

class LLMAuthenticationError(LLMServiceError):
    """Raised when NVIDIA API key is missing, invalid, or unauthorized."""
    pass

class LLMTimeoutError(LLMServiceError):
    """Raised when NVIDIA API request times out."""
    pass

# Thread-safe persistent HTTP session for TCP connection reuse & connection pooling
_http_session: Optional[requests.Session] = None

def get_http_session() -> requests.Session:
    """Returns or creates singleton requests.Session for HTTP connection pooling."""
    global _http_session
    if _http_session is None:
        _http_session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20)
        _http_session.mount("https://", adapter)
        _http_session.mount("http://", adapter)
    return _http_session

class NVIDIAClient:
    """
    Dedicated HTTP Client responsible strictly for network communication with NVIDIA API endpoint.
    
    Handles headers, HTTP POST transport, persistent connection reuse, split timeouts,
    status code mapping, and authentication safety.
    Strictly skips retries on 400, 401, 403, 404 client/authentication failures.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        connect_timeout: Optional[int] = None,
        read_timeout: Optional[int] = None
    ):
        if current_app:
            self.api_key = api_key or current_app.config.get("NVIDIA_API_KEY")
            self.base_url = base_url or current_app.config.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
            self.model = model or current_app.config.get("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct")
            self.connect_timeout = connect_timeout or int(current_app.config.get("LLM_CONNECT_TIMEOUT", 10))
            self.read_timeout = read_timeout or int(current_app.config.get("LLM_READ_TIMEOUT", current_app.config.get("LLM_TIMEOUT", 60)))
        else:
            import os
            self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
            self.base_url = base_url or os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
            self.model = model or os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct")
            self.connect_timeout = connect_timeout or int(os.getenv("LLM_CONNECT_TIMEOUT", 10))
            self.read_timeout = read_timeout or int(os.getenv("LLM_READ_TIMEOUT", os.getenv("LLM_TIMEOUT", 60)))

        if self.base_url and self.base_url.endswith("/"):
            self.base_url = self.base_url.rstrip("/")

        self.session = get_http_session()

    def post_chat_completion(self, payload: Dict[str, Any], max_retries: int = 3) -> Tuple[Dict[str, Any], int, int]:
        """
        Executes HTTP POST request to NVIDIA /chat/completions endpoint using persistent session.
        
        Returns:
            Tuple[dict, int, int]: (response_json_dict, status_code, total_retries_performed)
        """
        if not self.api_key or not self.api_key.strip() or self.api_key.strip() == "your_nvidia_api_key_here":
            raise LLMAuthenticationError("NVIDIA_API_KEY is missing or unconfigured in environment.")

        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        endpoint_url = f"{self.base_url}/chat/completions"
        timeout_tuple = (self.connect_timeout, self.read_timeout)

        last_error = None
        status_code = 500

        for attempt in range(1, max_retries + 1):
            try:
                response = self.session.post(
                    endpoint_url,
                    headers=headers,
                    json=payload,
                    timeout=timeout_tuple
                )

                status_code = response.status_code

                if response.status_code == 200:
                    try:
                        data = response.json()
                        return data, 200, (attempt - 1)
                    except Exception as pe:
                        raise LLMServiceError(f"Malformed JSON response from NVIDIA API: {str(pe)}")

                # CRITICAL SECURITY RULE: NEVER retry on authentication / authorization failure (401, 403) or client error (400, 404)
                if response.status_code in (401, 403):
                    logger.error(f"NVIDIA API authentication failure (HTTP {response.status_code}). Halting without retry.")
                    raise LLMAuthenticationError(f"NVIDIA API authentication/authorization failed (HTTP {response.status_code}).")
                elif response.status_code == 400:
                    logger.error("NVIDIA API bad request payload (HTTP 400). Halting without retry.")
                    raise LLMServiceError("NVIDIA API bad request payload (HTTP 400).")
                elif response.status_code == 404:
                    logger.error(f"NVIDIA API endpoint or model '{self.model}' not found (HTTP 404). Halting without retry.")
                    raise LLMServiceError(f"NVIDIA API endpoint or model '{self.model}' not found (HTTP 404).")

                # Transient errors retryable: 429, 408, 500, 502, 503, 504
                if response.status_code == 408:
                    last_error = LLMTimeoutError("NVIDIA API request timeout (HTTP 408).")
                elif response.status_code == 429:
                    logger.warning(f"NVIDIA API rate limit (429) on attempt {attempt}/{max_retries}.")
                    last_error = LLMServiceError("NVIDIA API rate limit exceeded (HTTP 429).")
                elif response.status_code in (500, 502, 503, 504):
                    logger.warning(f"NVIDIA API server error (HTTP {response.status_code}) on attempt {attempt}/{max_retries}.")
                    last_error = LLMServiceError(f"NVIDIA API server error (HTTP {response.status_code}).")
                else:
                    raise LLMServiceError(f"NVIDIA API request failed with HTTP {response.status_code}.")

            except requests.exceptions.Timeout as te:
                logger.warning(f"NVIDIA API timeout on attempt {attempt}/{max_retries}: {str(te)}")
                last_error = LLMTimeoutError(f"NVIDIA API connection timed out (connect={self.connect_timeout}s, read={self.read_timeout}s).")

            except requests.exceptions.RequestException as re:
                logger.warning(f"NVIDIA API network error on attempt {attempt}/{max_retries}: {str(re)}")
                last_error = LLMServiceError(f"NVIDIA API network error: {str(re)}")

            # Exponential backoff sleep before retry (1s, 2s)
            if attempt < max_retries:
                backoff_delay = 1.0 * (2 ** (attempt - 1))
                time.sleep(backoff_delay)

        if last_error:
            raise last_error
        raise LLMServiceError("NVIDIA API call failed after max retries.")
