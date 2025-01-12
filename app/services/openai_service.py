from openai import AsyncOpenAI
import logging
import os

class OpenAIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def rewrite_text_chunk(self, text: str, style: str = "scholar") -> str:
        if not text.strip():
            return text
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are a writing assistant specialized in {style} style."},
                    {"role": "user", "content": f"Rewrite the following text in {style} style:\n\n{text}"}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error in OpenAI API call: {e}")
            raise
