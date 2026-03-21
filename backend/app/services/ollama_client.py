import httpx
import json
import re
from typing import List, Dict, Optional, AsyncIterator
from backend.app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def _strip_thinking(text: str) -> str:
    """
    Удаляет блоки <think>...</think> из ответов thinking-моделей
    (Qwen3, DeepSeek-R1 и др.).
    Применяется всегда — для обычных моделей просто нет таких тегов.
    """
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned.strip()


class OllamaClient:
    """
    Клиент для взаимодействия с Ollama API (локальный LLM).
    """

    def __init__(
            self,
            base_url: str = settings.OLLAMA_BASE_URL,
            model: str = settings.OLLAMA_MODEL,
            timeout: int = settings.OLLAMA_TIMEOUT
    ):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def generate(
            self,
            prompt: str,
            system_prompt: Optional[str] = None,
            temperature: float = 0.7,
            max_tokens: int = 500,
            stream: bool = False,
            disable_thinking: bool = False
    ) -> str:
        """
        Генерирует ответ от модели.

        Args:
            prompt: Пользовательский запрос
            system_prompt: Системный промпт (инструкции для модели)
            temperature: Температура генерации (0.0-1.0)
            max_tokens: Максимальная длина ответа
            stream: Включить потоковую передачу
            disable_thinking: Отключить thinking-режим (для Qwen3/DeepSeek-R1)
        """
        url = f"{self.base_url}/api/generate"

        # Qwen3/DeepSeek-R1: отключаем thinking ВСЕГДА через /no_think префикс.
        # think:false в payload не работает в ряде версий Ollama —
        # /no_think в тексте промпта — единственный надёжный способ.
        prompt = "/no_think\n" + prompt

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "think": False,          # top-level (для новых версий Ollama)
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stop": ["<|im_start|>", "<|im_end|>", "\nВопрос:", "\nUser:", "\nuser:", "Сколько я", "Какой у", "Трачу ли", "\nСледуй", "Следуй этому", "\nПример:", "\nШаблон:"],
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            logger.debug(f"Sending request to Ollama: {url}")

            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            if stream:
                # TODO: Реализовать стриминг если нужно
                pass
            else:
                result = response.json()
                raw = result.get("response", "") or result.get("thinking", "")
                cleaned = _strip_thinking(raw)
                return cleaned

        except httpx.HTTPError as e:
            logger.error(f"Ollama HTTP error: {e}")
            raise OllamaError(f"Failed to connect to Ollama: {str(e)}")
        except Exception as e:
            logger.error(f"Ollama unexpected error: {e}", exc_info=True)
            raise OllamaError(f"Unexpected error: {str(e)}")

    async def chat(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            max_tokens: int = 500,
            disable_thinking: bool = False
    ) -> str:
        """
        Отправляет чат-запрос с историей сообщений.

        Args:
            messages: Список сообщений [{"role": "user/assistant/system", "content": "..."}]
            temperature: Температура генерации
            max_tokens: Максимальная длина ответа
        """
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        # think: false — в КОРНЕ payload
        if disable_thinking:
            payload["think"] = False

        try:
            logger.debug(f"Sending chat request to Ollama with {len(messages)} messages")

            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            result = response.json()
            message = result.get("message", {})
            raw = message.get("content", "") or message.get("thinking", "")
            cleaned = _strip_thinking(raw)
            return cleaned

        except httpx.HTTPError as e:
            logger.error(f"Ollama chat HTTP error: {e}")
            raise OllamaError(f"Failed to connect to Ollama: {str(e)}")
        except Exception as e:
            logger.error(f"Ollama chat unexpected error: {e}", exc_info=True)
            raise OllamaError(f"Unexpected error: {str(e)}")

    async def check_health(self) -> bool:
        """Проверяет доступность Ollama"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False

    async def list_models(self) -> List[str]:
        """Возвращает список доступных моделей"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    async def close(self):
        """Закрывает HTTP клиент"""
        await self.client.aclose()


class OllamaError(Exception):
    """Ошибка при работе с Ollama"""
    pass


# Глобальный экземпляр клиента
ollama_client = OllamaClient()