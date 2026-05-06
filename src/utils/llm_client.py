import os
import requests
from typing import Dict, List, Optional


class LLMClient:
    """Abstract LLM client supporting OpenRouter (Llama 3.3 70B)"""

    def __init__(self):
        # self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.provider = os.getenv("LLM_PROVIDER", "openrouter")
        self.model = os.getenv("LLM_MODEL", "llama-3.3-70b-instruct")
        # self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.base_url = "https://api.deepseek.com"
        self.site_url = "https://resfit.app"
        self.app_name = "ResFit-WorkoutEngine"

    def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1000
    ) -> Dict:
        """
        Generate a response from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt override
            temperature: Sampling temperature
            max_tokens: Max tokens to generate

        Returns:
            Dict with 'content', 'citations', 'model', 'created'
        """
        if not self.api_key:
            return {
                "error": "No LLM API key configured",
                "status_code": 500
            }

        if system_prompt:
            final_messages = [{"role": "system", "content": system_prompt}] + messages
        else:
            final_messages = messages

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name
        }

        payload = {
            "model": self.model,
            "messages": final_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code != 200:
                return {
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }

            result = response.json()

            content = result["choices"][0]["message"]["content"]
            return {
                "content": content,
                "model": result.get("model"),
                "created": result.get("created"),
                "citations": result.get("citations", [])
            }

        except Exception as e:
            return {
                "error": str(e),
                "status_code": 500
            }

    def generate_with_context(
        self,
        user_prompt: str,
        context: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1000
    ) -> Dict:
        """
        Convenience method: Generate response with context provided as system message.

        Args:
            user_prompt: User's question/query
            context: Context/background info to include
            system_prompt: Optional override for system instructions
            temperature: Sampling temperature
            max_tokens: Max tokens to generate

        Returns:
            Dict with response content and metadata
        """
        if system_prompt:
            full_system = f"{system_prompt}\n\nProvided Context:\n{context}"
        else:
            full_system = f"You are a research assistant. Use the provided context to answer.\n\nProvided Context:\n{context}"

        messages = [{"role": "user", "content": user_prompt}]
        return self.generate(messages, full_system, temperature, max_tokens)