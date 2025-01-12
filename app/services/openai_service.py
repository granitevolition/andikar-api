from openai import AsyncOpenAI
import logging

class OpenAIService:
    def __init__(self):
        self.api_key = "your-api-key"  # We'll configure this properly later
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def rewrite_text_chunk(self, text: str, style: str = "scholar") -> str:
        if not text.strip():
            return text

        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a writing assistant."},
                    {"role": "user", "content": f"Rewrite in {style} style:\n\n{text}"}
                ],
                temperature=1.0
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error in OpenAI API call: {e}")
            raise
