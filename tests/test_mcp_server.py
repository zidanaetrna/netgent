"""Unit tests for mcp_server module."""

import json
import unittest
from unittest.mock import MagicMock, patch

from src.ai.mcp_server import (
    handle_tool_call,
    load_tools_catalog,
    process_json_rpc_message,
)


class TestMCPServer(unittest.TestCase):
    """Test MCP JSON-RPC protocol handling and tool dispatch."""

    def test_load_tools_catalog(self):
        tools = load_tools_catalog()
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)
        tool_names = [t["name"] for t in tools]
        self.assertIn("deploy_device", tool_names)
        self.assertIn("execute_recipe", tool_names)
        self.assertIn("configure_pc_ip", tool_names)

    def test_initialize_handshake(self):
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
        }
        resp = process_json_rpc_message(req)
        self.assertEqual(resp["id"], 1)
        self.assertIn("serverInfo", resp["result"])
        self.assertEqual(resp["result"]["serverInfo"]["name"], "cpt-netgent-server")

    def test_ping(self):
        req = {"jsonrpc": "2.0", "id": 2, "method": "ping"}
        resp = process_json_rpc_message(req)
        self.assertEqual(resp["id"], 2)
        self.assertEqual(resp["result"], {})

    def test_tools_list(self):
        req = {"jsonrpc": "2.0", "id": 3, "method": "tools/list"}
        resp = process_json_rpc_message(req)
        self.assertEqual(resp["id"], 3)
        self.assertIn("tools", resp["result"])
        self.assertIsInstance(resp["result"]["tools"], list)

    def test_tools_call_configure_vlan(self):
        req = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "configure_vlan",
                "arguments": {
                    "vlan_id": 100,
                    "vlan_name": "TEST_VLAN",
                    "interfaces": ["Fa0/1"],
                },
            },
        }
        resp = process_json_rpc_message(req)
        self.assertEqual(resp["id"], 4)
        self.assertFalse(resp["result"]["isError"])
        content_text = resp["result"]["content"][0]["text"]
        self.assertIn("TEST_VLAN", content_text)

    def test_unknown_method(self):
        req = {"jsonrpc": "2.0", "id": 5, "method": "non_existent_method"}
        resp = process_json_rpc_message(req)
        self.assertIn("error", resp)
        self.assertEqual(resp["error"]["code"], -32601)


if __name__ == "__main__":
    unittest.main()
