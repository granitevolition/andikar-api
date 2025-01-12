from openai import AsyncOpenAI
from app.core.config import settings
import asyncio
from typing import List
import logging

class OpenAIService:
    def __init__(self):
        self._api_keys = settings.OPENAI_API_KEYS.copy()
        self._current_key_index = 0

    def _get_next_api_key(self) -> str:
        key = self._api_keys[self._current_key_index]
        self._current_key_index = (self._current_key_index + 1) % len(self._api_keys)
        return key

    async def rewrite_text(self, text: str, temperature: float = 1.0) -> str:
        client = AsyncOpenAI(api_key=self._get_next_api_key())
        try:
            response = await client.chat.completions.create(
                model=settings.GPT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a writing assistant."},
                    {"role": "user", "content": f"Rewrite as a scholar:\n\n{text}"}
                ],
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error in OpenAI API call: {e}")
            raise

    async def rewrite_text_chunk(
            self,
            text: str,
            style: str = "scholar",
            temperature: float = 1.0
    ) -> str:
        if not text.strip():
            return text

        client = AsyncOpenAI(api_key=self._get_next_api_key())
        try:
            response = await client.chat.completions.create(
                model=settings.GPT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a writing assistant."},
                    {"role": "user", "content": f"Rewrite in {style} style:\n\n{text}"}
                ],
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error in OpenAI API call: {e}")
            raise

    async def process_text_batch(
            self,
            texts: List[str],
            style: str = "scholar"
    ) -> List[str]:
        results = await asyncio.gather(*[
            self.rewrite_text_chunk(text, style)
            for text in texts
        ])
        return results