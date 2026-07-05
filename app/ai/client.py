"""AI client abstraction — supports Anthropic, OpenAI, and Google Gemini."""

import logging
from typing import Any

from config.settings import (
    AI_PROVIDER,
    ANTHROPIC_API_KEY,
    OPENAI_API_KEY,
    GOOGLE_API_KEY,
)

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified interface for LLM calls."""

    def __init__(self):
        self.provider = AI_PROVIDER
        self._anthropic = None
        self._openai = None
        self._google = None

        if self.provider == "anthropic" and ANTHROPIC_API_KEY:
            import anthropic
            self._anthropic = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            logger.info("Using Anthropic Claude")
        elif self.provider == "openai" and OPENAI_API_KEY:
            import openai
            self._openai = openai.OpenAI(api_key=OPENAI_API_KEY)
            logger.info("Using OpenAI")
        elif self.provider == "google" and GOOGLE_API_KEY:
            from google import genai
            self._google = genai.Client(api_key=GOOGLE_API_KEY)
            logger.info("Using Google Gemini")
        else:
            logger.warning(f"No API key configured for provider '{self.provider}'")

    def _check_configured(self):
        if self.provider == "anthropic" and not self._anthropic:
            raise RuntimeError("Anthropic not configured. Set ANTHROPIC_API_KEY.")
        if self.provider == "openai" and not self._openai:
            raise RuntimeError("OpenAI not configured. Set OPENAI_API_KEY.")
        if self.provider == "google" and not self._google:
            raise RuntimeError("Google AI not configured. Set GOOGLE_API_KEY.")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Generate a response from the LLM."""
        self._check_configured()

        if self.provider == "anthropic":
            return self._anthropic_generate(system_prompt, user_prompt, max_tokens, temperature)
        elif self.provider == "openai":
            return self._openai_generate(system_prompt, user_prompt, max_tokens, temperature)
        else:
            return self._google_generate(system_prompt, user_prompt, max_tokens, temperature)

    def _anthropic_generate(
        self, system: str, user: str, max_tokens: int, temperature: float
    ) -> str:
        msg = self._anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text

    def _openai_generate(
        self, system: str, user: str, max_tokens: int, temperature: float
    ) -> str:
        response = self._openai.chat.completions.create(
            model="gpt-4o",
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""

    def _google_generate(
        self, system: str, user: str, max_tokens: int, temperature: float
    ) -> str:
        from google.genai import types
        response = self._google.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
            contents=user,
        )
        return response.text or ""

    def generate_with_images(
        self,
        system_prompt: str,
        user_prompt: str,
        image_paths: list[str],
        max_tokens: int = 4096,
    ) -> str:
        """Generate with image inputs (for handwritten/OCR tasks)."""
        self._check_configured()

        if self.provider == "anthropic":
            return self._anthropic_generate_with_images(
                system_prompt, user_prompt, image_paths, max_tokens
            )
        elif self.provider == "openai":
            return self._openai_generate_with_images(
                system_prompt, user_prompt, image_paths, max_tokens
            )
        else:
            return self._google_generate_with_images(
                system_prompt, user_prompt, image_paths, max_tokens
            )

    def _anthropic_generate_with_images(
        self, system: str, user: str, image_paths: list[str], max_tokens: int
    ) -> str:
        import base64

        content = []
        content.append({"type": "text", "text": user})

        for path in image_paths:
            with open(path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            ext = path.rsplit(".", 1)[-1].lower()
            media_type = f"image/{'png' if ext == 'png' else 'jpeg' if ext in ('jpg', 'jpeg') else 'webp'}"
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": img_data,
                },
            })

        msg = self._anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            system=system,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": content}],
        )
        return msg.content[0].text

    def _openai_generate_with_images(
        self, system: str, user: str, image_paths: list[str], max_tokens: int
    ) -> str:
        import base64

        content = [{"type": "text", "text": user}]
        for path in image_paths:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            })

        response = self._openai.chat.completions.create(
            model="gpt-4o",
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
        )
        return response.choices[0].message.content or ""

    def _google_generate_with_images(
        self, system: str, user: str, image_paths: list[str], max_tokens: int
    ) -> str:
        import base64
        from google.genai import types

        parts = [types.Part.from_text(text=user)]
        for path in image_paths:
            with open(path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            ext = path.rsplit(".", 1)[-1].lower()
            mime = f"image/{'png' if ext == 'png' else 'jpeg' if ext in ('jpg', 'jpeg') else 'webp'}"
            parts.append(types.Part.from_bytes(data=img_data, mime_type=mime))

        response = self._google.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_tokens,
            ),
            contents=types.Content(parts=parts, role="user"),
        )
        return response.text or ""
