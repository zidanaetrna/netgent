"""Unit tests for agent CLI interface and topology presets."""

from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from src.core.presets import LAB_PRESETS
from src.ui.agent_cli import (
    match_antigravity_recipe,
    scan_topologies_catalog,
    select_agent_mode,
    select_or_input_prompt,
)


class TestAgentCLI(unittest.TestCase):
    """Test interactive CLI components, topology presets, and live catalog scanning."""

    def test_presets_validity(self):
        """Verify all lab presets have non-empty prompt and recipe file."""
        self.assertGreaterEqual(len(LAB_PRESETS), 3)
        for name, data in LAB_PRESETS.items():
            self.assertIn("prompt", data)
            self.assertIn("recipe_file", data)
            self.assertTrue(len(data["prompt"]) > 20)
            self.assertTrue(data["recipe_file"].endswith(".yaml"))

    @patch("src.ui.agent_cli.Prompt.ask")
    @patch("src.ui.agent_cli.console.print")
    def test_select_agent_mode_antigravity(self, mock_print, mock_prompt):
        """Test choosing Antigravity Mode displays guide and returns antigravity."""
        mock_prompt.return_value = "1"
        mode = select_agent_mode()
        self.assertEqual(mode, "antigravity")

    @patch("src.ui.agent_cli.Prompt.ask")
    @patch("src.ui.agent_cli.console.print")
    def test_select_agent_mode_api_key(self, mock_print, mock_prompt):
        """Test choosing External API Key Mode."""
        mock_prompt.return_value = "2"
        mode = select_agent_mode()
        self.assertEqual(mode, "api_key")

    @patch("src.ui.agent_cli.Prompt.ask")
    @patch("src.ui.agent_cli.console.print")
    def test_cli_interactive_preset_selection(self, mock_print, mock_prompt):
        """Test selecting a pre-configured lab preset from the menu."""
        mock_prompt.return_value = "1"
        prompt_text, answers, recipe = select_or_input_prompt()
        self.assertIn("PRAKTIKUM 2", prompt_text)
        self.assertIsNotNone(recipe)

    @patch("src.ui.agent_cli.Prompt.ask")
    @patch("src.ui.agent_cli.console.print")
    def test_cli_scan_topologies_catalog(self, mock_print, mock_prompt):
        """Test scanning topologies/ directory and selecting a detected YAML recipe."""
        mock_prompt.return_value = "1"
        res = scan_topologies_catalog()
        self.assertIsNotNone(res)
        prompt_info, answers, recipe = res
        self.assertIn("Assignment loaded from", prompt_info)
        self.assertIn("devices", recipe)

    @patch("src.ui.agent_cli.Prompt.ask")
    @patch("src.ui.agent_cli.Confirm.ask")
    @patch("src.ui.agent_cli.console.print")
    def test_cli_custom_prompt_input(self, mock_print, mock_confirm, mock_prompt):
        """Test typing a custom assignment prompt."""
        mock_prompt.return_value = "C"
        with patch("src.ui.agent_cli.get_clipboard_content", return_value=""), \
             patch("builtins.input", side_effect=["Simulasi Jaringan Kustom", "/end"]):
            custom_prompt, _, _ = select_or_input_prompt()
            self.assertIn("Simulasi Jaringan Kustom", custom_prompt)


if __name__ == "__main__":
    unittest.main()
