"""Unit tests for the IPC bridge client."""

import unittest
from unittest.mock import MagicMock, patch

from src.automation.ipc_bridge import (
    CPTIPCClient,
    format_interface_name,
    normalize_cable_type,
    normalize_device_model,
)


class TestIPCBridge(unittest.TestCase):
    """Test IPC bridge normalization, interface formatting, and client calls."""

    def test_normalize_device_model(self):
        self.assertEqual(normalize_device_model("pc"), "PC-PT")
        self.assertEqual(normalize_device_model("server"), "Server-PT")
        self.assertEqual(normalize_device_model("switch"), "2960-24TT")
        self.assertEqual(normalize_device_model("router"), "2911")
        self.assertEqual(normalize_device_model("unknown"), "PC-PT")

    def test_normalize_cable_type(self):
        self.assertEqual(normalize_cable_type("copper_straight_through"), "straight")
        self.assertEqual(normalize_cable_type("copper_cross_over"), "cross")
        self.assertEqual(normalize_cable_type("fiber"), "fiber")
        self.assertEqual(normalize_cable_type("serial"), "serial")

    def test_format_interface_name(self):
        # Numeric indices
        self.assertEqual(format_interface_name("pc", 0), "FastEthernet0")
        self.assertEqual(format_interface_name("switch", 0), "FastEthernet0/1")
        self.assertEqual(format_interface_name("switch", 1), "FastEthernet0/2")
        self.assertEqual(format_interface_name("router", 0), "GigabitEthernet0/0")
        # Explicit strings
        self.assertEqual(format_interface_name("pc", "FastEthernet0"), "FastEthernet0")
        self.assertEqual(format_interface_name("switch", "GigabitEthernet0/1"), "GigabitEthernet0/1")

    def test_client_is_connected_initially_false(self):
        client = CPTIPCClient()
        self.assertFalse(client.is_connected)

    def test_client_not_connected_raises(self):
        client = CPTIPCClient()
        with self.assertRaises(RuntimeError):
            client.get_network()


if __name__ == "__main__":
    unittest.main()
