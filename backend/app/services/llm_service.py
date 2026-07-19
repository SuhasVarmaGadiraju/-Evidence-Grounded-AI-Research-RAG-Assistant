import time
import uuid
import logging
from typing import Dict, Any, Optional
from flask import current_app
from app.services.nvidia_client import (
    NVIDIAClient,
    LLMServiceError,
    LLMAuthenticationError,
    LLMTimeoutError
)

logger = logging.getLogger("rag_backend.services.llm_service")

class LLMService:
    """
    Production LLM Service managing request validation, execution tracking, and metadata parsing.
    
    Delegates HTTP transport strictly to NVIDIAClient.
    Prepares system for multi-provider extensibility (OpenAI, Anthropic, Gemini, Ollama).
    """

    def __init__(self, client: Optional[NVIDIAClient] = None):
        self.client = client or NVIDIAClient()

    def health_check(self) -> Dict[str, Any]:
        """
        Runs local configuration health check without invoking remote API.
        
        Returns:
            dict: Service configuration status.
        """
        api_key_set = bool(
            self.client.api_key
            and self.client.api_key.strip()
            and self.client.api_key.strip() != "your_nvidia_api_key_here"
        )

        return {
            "provider": "NVIDIA",
            "configured": api_key_set,
            "model": self.client.model,
            "service_status": "healthy" if api_key_set else "unconfigured"
        }

    def generate(self, prompt: str, request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Submits rendered prompt to NVIDIA LLM service and returns structured response payload.
        
        Args:
            prompt (str): Rendered prompt string from PromptBuilderService.
            request_id (str, optional): Unique request tracker ID. If omitted, generates new UUID.

        Returns:
            dict: Structured response payload with answer text, request_id, tokens, model, and metrics.
        """
        req_id = request_id or uuid.uuid4().hex
        clean_prompt = (prompt or "").strip()

        if not clean_prompt:
            raise LLMServiceError("Cannot generate response: prompt string is empty.")

        # Read generation parameters from Flask app config or defaults
        if current_app:
            temperature = float(current_app.config.get("LLM_TEMPERATURE", 0.2))
            top_p = float(current_app.config.get("LLM_TOP_P", 0.7))
            max_tokens = int(current_app.config.get("LLM_MAX_TOKENS", 1024))
        else:
            import os
            temperature = float(os.getenv("LLM_TEMPERATURE", 0.2))
            top_p = float(os.getenv("LLM_TOP_P", 0.7))
            max_tokens = int(os.getenv("LLM_MAX_TOKENS", 1024))

        payload = {
            "model": self.client.model,
            "messages": [
                {
                    "role": "user",
                    "content": clean_prompt
                }
            ],
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens
        }

        start_time = time.time()

        # Delegate HTTP transport to NVIDIAClient
        data, status_code, retries = self.client.post_chat_completion(payload)

        elapsed_time = time.time() - start_time

        # Parse choices & response content
        choices = data.get("choices", [])
        if not choices:
            raise LLMServiceError("NVIDIA API response contained empty choice array.")

        first_choice = choices[0]
        message_obj = first_choice.get("message", {})
        answer_text = (message_obj.get("content") or "").strip()
        finish_reason = first_choice.get("finish_reason", "stop")

        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

        # Privacy-Safe Logging (including request_id, model, latency, retries, status, tokens)
        # NEVER logging prompt text, user query, or API key
        logger.info(
            f"LLM Generation Succeeded | "
            f"ReqID: {req_id} | "
            f"Model: {self.client.model} | "
            f"Status: {status_code} | "
            f"Latency: {elapsed_time:.4f}s | "
            f"Retries: {retries} | "
            f"FinishReason: {finish_reason} | "
            f"PromptTokens: {prompt_tokens} | "
            f"CompletionTokens: {completion_tokens} | "
            f"TotalTokens: {total_tokens}"
        )

        return {
            "request_id": req_id,
            "answer": answer_text,
            "model": self.client.model,
            "latency": elapsed_time,
            "retry_count": retries,
            "finish_reason": finish_reason,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "usage": usage,
            "status_code": status_code
        }
