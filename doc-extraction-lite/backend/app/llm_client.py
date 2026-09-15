import os
import openai
from openai import OpenAI
from typing import Optional

class LLMClientError(Exception):
    pass

class LLMClient:
    def __init__(self):
        self.base_url = os.getenv("MODEL_BASE_URL")
        self.api_key = os.getenv("MODEL_API_KEY")
        self.model_name = os.getenv("MODEL_NAME")
        self.timeout = int(os.getenv("MODEL_TIMEOUT", 120))

        if not self.base_url or not self.model_name:
            raise LLMClientError("MODEL_BASE_URL and MODEL_NAME must be set in environment variables.")

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key if self.api_key else "sk-no-key-required", # Some local models don't need a key
            timeout=self.timeout
        )

    async def chat_completion(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            return response.choices[0].message.content
        except openai.APIStatusError as e:
            raise LLMClientError(f"LLM API error: {e.status_code} - {e.response}")
        except openai.APITimeoutError:
            raise LLMClientError(f"LLM API request timed out after {self.timeout} seconds.")
        except openai.APIConnectionError as e:
            raise LLMClientError(f"LLM API connection error: {e}")
        except Exception as e:
            raise LLMClientError(f"An unexpected error occurred during LLM call: {e}")
