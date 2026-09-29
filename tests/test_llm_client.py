"""Unit tests for llm_client module."""

import json
import unittest
from unittest.mock import MagicMock, patch

from src.ai.llm_client import LLMClient


class TestLLMClient(unittest.TestCase):
    """Test LLM client initialization, prompt routing, and JSON extraction."""

    def test_provider_initialization(self):
        client_gemini = LLMClient(provider="gemini", api_key="dummy-gemini-key")
        self.assertEqual(client_gemini.provider, "gemini")
        self.assertEqual(client_gemini.model, "gemini-2.0-flash")

        client_openai = LLMClient(provider="openai", api_key="dummy-openai-key")
        self.assertEqual(client_openai.provider, "openai")
        self.assertEqual(client_openai.model, "gpt-4o")

        client_anthropic = LLMClient(provider="anthropic", api_key="dummy-anthropic-key")
        self.assertEqual(client_anthropic.provider, "anthropic")
        self.assertEqual(client_anthropic.model, "claude-3-5-sonnet-20241022")

        client_ollama = LLMClient(provider="ollama")
        self.assertEqual(client_ollama.provider, "ollama")
        self.assertEqual(client_ollama.base_url, "http://localhost:11434/v1")

    def test_invalid_provider_raises(self):
        with self.assertRaises(ValueError):
            LLMClient(provider="unsupported_ai")

    def test_extract_json_clean(self):
        raw = '{"academic_answers": "test", "recipe": {"name": "test"}}'
        parsed = LLMClient._extract_json(raw)
        self.assertEqual(parsed["academic_answers"], "test")

    def test_extract_json_markdown_fences(self):
        raw = "```json\n{\"academic_answers\": \"jawaban\", \"recipe\": {\"name\": \"Test Net\"}}\n```"
        parsed = LLMClient._extract_json(raw)
        self.assertEqual(parsed["recipe"]["name"], "Test Net")

    @patch.object(LLMClient, "call_raw")
    def test_synthesize_success(self, mock_call):
        valid_recipe = {
            "name": "Synthesized Network",
            "devices": [
                {"id": "PC1", "type": "pc", "position": {"x": 0.3, "y": 0.7}},
                {"id": "PC2", "type": "pc", "position": {"x": 0.7, "y": 0.7}},
            ],
            "connections": [
                {"from": "PC1", "to": "PC2", "cable_type": "copper_cross_over", "from_port": 0, "to_port": 0}
            ],
            "configurations": {
                "PC1": {"type": "pc", "ip_address": "192.168.1.10", "subnet_mask": "255.255.255.0"},
                "PC2": {"type": "pc", "ip_address": "192.168.1.20", "subnet_mask": "255.255.255.0"},
            },
            "verifications": [{"source": "PC1", "target_ip": "192.168.1.20"}],
        }

        mock_call.return_value = json.dumps({
            "academic_answers": "Jawaban praktikum lengkap",
            "recipe": valid_recipe,
        })

        client = LLMClient(provider="gemini", api_key="dummy")
        result = client.synthesize("Buat jaringan 2 PC peer-to-peer")

        self.assertIn("academic_answers", result)
        self.assertEqual(result["recipe"]["name"], "Synthesized Network")
        self.assertEqual(len(result["recipe"]["devices"]), 2)


if __name__ == "__main__":
    unittest.main()
