"""Unit tests for preflight_check module."""

import unittest
from unittest.mock import MagicMock, patch

from src.automation.preflight_check import (
    check_ipc_port,
    check_python_dependencies,
    check_schemas_and_topologies,
    check_window_status,
    run_all_checks,
)


class TestPreflightCheck(unittest.TestCase):
    """Test environment pre-flight diagnostics."""

    def test_check_python_dependencies(self):
        res = check_python_dependencies()
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(len(res["missing"]), 0)

    def test_check_schemas_and_topologies(self):
        res = check_schemas_and_topologies()
        self.assertEqual(res["status"], "PASS")
        self.assertTrue(res["schema_exists"])
        self.assertGreater(res["topologies_found"], 0)

    @patch("socket.socket")
    def test_check_ipc_port_open(self, mock_sock_cls):
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_sock_cls.return_value = mock_sock

        res = check_ipc_port()
        self.assertEqual(res["status"], "PASS")
        self.assertTrue(res["connected"])

    @patch("socket.socket")
    def test_check_ipc_port_closed(self, mock_sock_cls):
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 111
        mock_sock_cls.return_value = mock_sock

        res = check_ipc_port()
        self.assertEqual(res["status"], "WARN")
        self.assertFalse(res["connected"])

    @patch("src.automation.preflight_check.find_cpt_window")
    def test_check_window_status_detected(self, mock_find):
        mock_win = MagicMock()
        mock_win.title = "Cisco Packet Tracer"
        mock_win.left = 0
        mock_win.top = 0
        mock_win.width = 1920
        mock_win.height = 1080
        mock_win.isMaximized = True
        mock_win.isMinimized = False
        mock_find.return_value = mock_win

        res = check_window_status()
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["title"], "Cisco Packet Tracer")

    @patch("src.automation.preflight_check.find_cpt_window")
    def test_check_window_status_not_detected(self, mock_find):
        mock_find.return_value = None
        res = check_window_status()
        self.assertEqual(res["status"], "WARN")

    @patch("src.automation.preflight_check.find_cpt_window")
    def test_run_all_checks(self, mock_find):
        mock_find.return_value = None
        results = run_all_checks()
        self.assertIn(results["overall_status"], ["PASS", "WARN", "FAIL"])
        self.assertIn("python_dependencies", results["checks"])
        self.assertIn("ipc_bridge", results["checks"])
        self.assertIn("schemas_and_topologies", results["checks"])


if __name__ == "__main__":
    unittest.main()
