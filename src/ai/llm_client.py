"""Universal Multi-Provider LLM Client for NetGent.

Connects to Google Gemini, OpenAI, Anthropic Claude, or local Ollama endpoints
to automatically synthesize valid network recipes (YAML) and theoretical answers
from natural-language lab assignments and topology requirements.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx

from src.core.config import PROJECT_ROOT
from src.core.recipe_runner import RecipeValidationError, validate_recipe

logger = logging.getLogger("llm_client")

# Load recipe schema for prompt context
SCHEMA_FILE = PROJECT_ROOT / "schemas" / "recipe_schema.json"
RECIPE_SCHEMA_TEXT = ""
if SCHEMA_FILE.exists():
    try:
        RECIPE_SCHEMA_TEXT = SCHEMA_FILE.read_text(encoding="utf-8")
    except Exception:
        pass

SYSTEM_PROMPT = f"""You are NetGent AI, an expert Cisco Certified Network Associate (CCNA) instructor and network automation architect.
You design and configure network topologies for Cisco Packet Tracer.

Given a networking assignment, exam problem, or laboratory specification:
1. If the user asks theoretical/analytical questions, answer them thoroughly, professionally, and clearly (in the same language as the prompt, e.g. Indonesian or English).
2. Synthesize a complete, syntactically valid topology recipe conforming strictly to the NetGent recipe specification.

CRITICAL NETGENT RECIPE RULES:
- Devices:
  - id: Short unique identifier (e.g. 'R1', 'SW1', 'PC1', 'PC2', 'SERVER', 'PRINTER1').
  - type: 'router_2911', 'switch_2960', 'pc', 'server', 'printer'.
  - position: Normalized canvas coordinates x: [0.10 to 0.90], y: [0.10 to 0.90]. (Place routers top ~0.20, switches middle ~0.45, PCs/servers bottom ~0.75).
- Connections:
  - cable_type: 'copper_straight_through' (PC/Server to Switch, Switch to Router) or 'copper_cross_over' (Switch to Switch, PC to PC).
  - from_port / to_port: Exact Cisco port strings:
    - Routers: 'GigabitEthernet0/0', 'GigabitEthernet0/1', 'GigabitEthernet0/2'.
    - 2960 Switches: 'FastEthernet0/1' through 'FastEthernet0/24', and 'GigabitEthernet0/1', 'GigabitEthernet0/2'.
    - PCs / Servers / Printers: 'FastEthernet0'.
- Configurations:
  - IOS Devices (Routers/Switches): type 'ios', commands list of strings. Routers MUST have 'no shutdown' on used interfaces.
  - PCs/Servers/Printers: type 'pc', 'ip_address', 'subnet_mask', optional 'default_gateway'.
- Verifications:
  - List of tests: 'source' (e.g. 'PC1'), 'target_ip' (e.g. '192.168.1.20'), 'ping_count' (default 4).

RESPONSE FORMAT:
You MUST respond with a single valid JSON object containing exactly two keys:
{{
  "academic_answers": "Formatted Markdown text containing explanations and answers to assignment questions.",
  "recipe": {{
    "name": "Short Descriptive Title",
    "description": "Brief description of the topology",
    "devices": [...],
    "connections": [...],
    "configurations": {{...}},
    "verifications": [...]
  }}
}}
Do NOT wrap the JSON inside markdown blocks or text before/after. Return raw JSON only.
"""


class LLMClient:
    """Multi-provider client for Google Gemini, OpenAI, Claude, and Ollama."""

    def __init__(
        self,
        provider: str = "gemini",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        """Initialize LLM provider settings.

        Args:
            provider: 'gemini', 'openai', 'anthropic', or 'ollama' / 'openai_compatible'.
            api_key: API key. If omitted, checks environment variables (GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY).
            model: Specific model name. Defaults to recommended per provider.
            base_url: Custom API endpoint (e.g. 'http://localhost:11434/v1').
            timeout: HTTP request timeout in seconds.
        """
        self.provider = provider.lower().strip()
        self.base_url = base_url
        self.timeout = timeout

        if self.provider == "gemini":
            self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
            self.model = model or "gemini-2.0-flash"
        elif self.provider == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
            self.model = model or "gpt-4o"
            self.base_url = base_url or "https://api.openai.com/v1"
        elif self.provider == "anthropic":
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
            self.model = model or "claude-3-5-sonnet-20241022"
            self.base_url = base_url or "https://api.anthropic.com/v1"
        elif self.provider in ("ollama", "openai_compatible"):
            self.api_key = api_key or os.getenv("OLLAMA_API_KEY", "ollama")
            self.model = model or "llama3"
            self.base_url = base_url or "http://localhost:11434/v1"
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def call_raw(self, user_prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
        """Dispatch a single prompt completion request to the configured provider."""
        with httpx.Client(timeout=self.timeout) as client:
            if self.provider == "gemini":
                return self._call_gemini(client, user_prompt, system_prompt)
            elif self.provider in ("openai", "ollama", "openai_compatible"):
                return self._call_openai_compatible(client, user_prompt, system_prompt)
            elif self.provider == "anthropic":
                return self._call_anthropic(client, user_prompt, system_prompt)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")

    def _call_gemini(self, client: httpx.Client, user_prompt: str, system_prompt: str) -> str:
        if not self.api_key:
            raise ValueError("Gemini API key is required. Provide it in settings or set GEMINI_API_KEY.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system_prompt}\n\nUSER PROMPT:\n{user_prompt}"}]}
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        resp = client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"Gemini returned empty candidates: {data}")
        return candidates[0]["content"]["parts"][0]["text"]

    def _call_openai_compatible(self, client: httpx.Client, user_prompt: str, system_prompt: str) -> str:
        if self.provider == "openai" and not self.api_key:
            raise ValueError("OpenAI API key is required. Provide it in settings or set OPENAI_API_KEY.")

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }

        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def _call_anthropic(self, client: httpx.Client, user_prompt: str, system_prompt: str) -> str:
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY or provide in settings.")

        url = f"{self.base_url.rstrip('/')}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "temperature": 0.2,
        }

        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        content_blocks = data.get("content", [])
        for block in content_blocks:
            if block.get("type") == "text":
                return block.get("text", "")
        raise RuntimeError("No text block returned from Anthropic.")

    def synthesize(self, user_prompt: str, auto_repair_attempts: int = 2) -> Dict[str, Any]:
        """Synthesize recipe and analytical answers from a natural-language prompt.

        Performs JSON extraction and recipe schema validation. Automatically repairs
        the recipe if schema errors are detected.

        Returns:
            Dictionary with 'academic_answers', 'recipe', and 'raw_response'.
        """
        raw_text = self.call_raw(user_prompt)
        parsed = self._extract_json(raw_text)

        academic_answers = parsed.get("academic_answers", "")
        recipe = parsed.get("recipe", {})

        # Validation & repair loop
        for attempt in range(auto_repair_attempts + 1):
            try:
                validate_recipe(recipe)
                logger.info("Successfully synthesized and validated recipe '%s'", recipe.get("name", "Unnamed"))
                return {
                    "academic_answers": academic_answers,
                    "recipe": recipe,
                    "raw_response": raw_text,
                    "provider": self.provider,
                    "model": self.model,
                }
            except RecipeValidationError as val_err:
                if attempt == auto_repair_attempts:
                    logger.error("Recipe failed validation after %d repair attempts: %s", attempt, val_err)
                    raise

                logger.warning("Recipe validation error on attempt %d: %s. Requesting LLM repair...", attempt + 1, val_err)
                repair_prompt = (
                    f"The previously generated recipe had a validation error:\n{val_err}\n\n"
                    f"Here is the broken recipe:\n{json.dumps(recipe, indent=2)}\n\n"
                    "Fix all errors so it strictly satisfies the NetGent schema. Return ONLY valid JSON."
                )
                raw_text = self.call_raw(repair_prompt)
                parsed = self._extract_json(raw_text)
                recipe = parsed.get("recipe", parsed)

        return {
            "academic_answers": academic_answers,
            "recipe": recipe,
            "raw_response": raw_text,
        }

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        """Extract a valid JSON dictionary from raw model text."""
        cleaned = text.strip()
        # Remove potential markdown fences ```json ... ```
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback regex search for outer braces
            match = re.search(r"(\{[\s\S]*\})", cleaned)
            if match:
                return json.loads(match.group(1))
            raise ValueError(f"Could not parse valid JSON from LLM response:\n{text[:300]}...")
