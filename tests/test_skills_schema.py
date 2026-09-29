"""Unit tests validating skills_schema.json against implementation modules."""

import json
import unittest
from pathlib import Path

from src.core.config import PROJECT_ROOT


class TestSkillsSchema(unittest.TestCase):
    """Validate JSON tool schema format and tool names."""

    def setUp(self):
        self.schema_path = PROJECT_ROOT / "schemas" / "skills_schema.json"

    def test_schema_valid_json(self):
        self.assertTrue(self.schema_path.is_file(), "skills_schema.json must exist")
        with open(self.schema_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("title", data)
        self.assertIn("tools", data)
        self.assertIsInstance(data["tools"], list)

    def test_schema_tools_have_required_fields(self):
        with open(self.schema_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        tools = data["tools"]
        tool_names = set()
        for tool in tools:
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("parameters", tool)
            self.assertEqual(tool["parameters"].get("type"), "object")
            tool_names.add(tool["name"])

        expected_tools = {
            "focus_and_maximize_cpt",
            "deploy_device",
            "connect_devices",
            "delete_element",
            "open_cli_tab",
            "execute_ios_commands",
            "configure_pc_ip",
            "run_pc_ping",
            "fast_forward_time",
            "read_cli_output",
            "configure_vlan",
        }
        self.assertTrue(
            expected_tools.issubset(tool_names),
            f"Missing tools in schema: {expected_tools - tool_names}",
        )


if __name__ == "__main__":
    unittest.main()
