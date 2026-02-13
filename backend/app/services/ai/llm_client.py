import json

import httpx

from app.core.config import settings


class LLMClient:
    @staticmethod
    def _clean_key(value: str | None) -> str:
        key = (value or "").strip()
        if not key or key.lower() in {"replace_me", "none", "null"}:
            return ""
        return key

    async def _call_perplexity(self, key: str, system_prompt: str, user_prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.perplexity_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 400,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        try:
            return data["choices"][0]["message"]["content"]
        except Exception:
            return json.dumps(data)

    async def _call_openai(self, key: str, system_prompt: str, user_prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.openai_model,
            "input": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/responses",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        # Responses API returns output[] content parts; extract text.
        try:
            return data["output"][0]["content"][0]["text"]
        except Exception:
            return json.dumps(data)

    async def nl_to_json(self, system_prompt: str, user_prompt: str) -> str:
        """
        Returns raw model text (expected to be JSON).
        Provider order:
        1) Perplexity (PERPLEXITY_API_KEY or pplx-* OPENAI_API_KEY)
        2) OpenAI Responses API
        """
        perplexity_key = self._clean_key(settings.perplexity_api_key)
        openai_key = self._clean_key(settings.openai_api_key)

        # Compatibility convenience: if user pastes a Perplexity key into OPENAI_API_KEY.
        if not perplexity_key and openai_key.startswith("pplx-"):
            perplexity_key = openai_key
            openai_key = ""

        if perplexity_key:
            return await self._call_perplexity(perplexity_key, system_prompt, user_prompt)
        if openai_key:
            return await self._call_openai(openai_key, system_prompt, user_prompt)
        raise RuntimeError("No LLM API key configured (PERPLEXITY_API_KEY / OPENAI_API_KEY)")
