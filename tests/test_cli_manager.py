"""Unit tests for cli_manager module."""

import unittest
from unittest.mock import MagicMock, patch

from src.automation.cli_manager import (
    configure_interface_ip,
    configure_trunk,
    configure_vlan,
    execute_ios_commands,
    open_cli_tab,
    read_cli_output,
    verify_cli_command,
)


class TestCLIManager(unittest.TestCase):
    """Test CLI automation commands and tab management."""

    def test_configure_interface_ip_commands(self):
        commands = configure_interface_ip("GigabitEthernet0/0", "192.168.1.1", "255.255.255.0")
        expected = [
            "enable",
            "configure terminal",
            "interface GigabitEthernet0/0",
            "ip address 192.168.1.1 255.255.255.0",
            "no shutdown",
            "exit",
            "exit",
            "write memory",
        ]
        self.assertEqual(commands, expected)

    @patch("src.automation.cli_manager.type_text_payload")
    @patch("src.automation.cli_manager.pyautogui.press")
    def test_execute_ios_commands_with_dialog_dismiss(self, mock_press, mock_type):
        cmd_list = ["enable", "show ip interface brief"]
        execute_ios_commands(cmd_list, dismiss_initial_dialog=True)

        # Verify initial dialog dismissal ('no') and subsequent commands
        mock_type.assert_any_call("no", interval=unittest.mock.ANY, press_enter=True)
        mock_type.assert_any_call("enable", interval=unittest.mock.ANY, press_enter=True)
        mock_type.assert_any_call("show ip interface brief", interval=unittest.mock.ANY, press_enter=True)

    @patch("src.automation.cli_manager.type_text_payload")
    @patch("src.automation.cli_manager.pyautogui.press")
    def test_execute_ios_commands_without_dialog_dismiss(self, mock_press, mock_type):
        cmd_list = ["enable", "show running-config"]
        execute_ios_commands(cmd_list, dismiss_initial_dialog=False)

        calls = [c.args[0] for c in mock_type.call_args_list]
        self.assertNotIn("no", calls)
        self.assertEqual(calls, ["enable", "show running-config"])

    @patch("src.automation.cli_manager.pyautogui.doubleClick")
    @patch("src.automation.cli_manager.pyautogui.click")
    @patch("src.automation.cli_manager._get_active_modal_window")
    def test_open_cli_tab_with_modal_window(self, mock_get_window, mock_click, mock_double_click):
        mock_win = MagicMock()
        mock_win.title = "Router0"
        mock_win.left = 100
        mock_win.top = 100
        mock_win.width = 600
        mock_win.height = 400
        mock_get_window.return_value = mock_win

        open_cli_tab(400, 300)

        mock_double_click.assert_called_with(400, 300)
        # Should click CLI tab relative to window
        mock_click.assert_any_call(mock_win.left + 145, mock_win.top + 55)

    @patch("src.automation.cli_manager.pyperclip.paste")
    @patch("src.automation.cli_manager.pyautogui.click")
    @patch("src.automation.cli_manager._get_active_modal_window")
    def test_read_cli_output(self, mock_get_window, mock_click, mock_paste):
        mock_win = MagicMock()
        mock_win.left = 100
        mock_win.top = 100
        mock_win.width = 600
        mock_win.height = 400
        mock_get_window.return_value = mock_win
        mock_paste.return_value = "Router# show ip interface brief\nGigabitEthernet0/0 up up"

        output = read_cli_output()
        self.assertIn("GigabitEthernet0/0 up up", output)

    @patch("src.automation.cli_manager.read_cli_output")
    @patch("src.automation.cli_manager.execute_ios_commands")
    def test_verify_cli_command_success(self, mock_exec, mock_read):
        mock_read.return_value = "GigabitEthernet0/0 is up, line protocol is up"
        success, out = verify_cli_command("show ip interface brief", expected_snippet="is up")
        self.assertTrue(success)
        self.assertEqual(out, mock_read.return_value)

    @patch("src.automation.cli_manager.read_cli_output")
    @patch("src.automation.cli_manager.execute_ios_commands")
    def test_verify_cli_command_error_detected(self, mock_exec, mock_read):
        mock_read.return_value = "% Invalid input detected at '^' marker."
        success, out = verify_cli_command("invalid_cmd_xyz")
        self.assertFalse(success)

    def test_configure_vlan_commands(self):
        cmds = configure_vlan(10, "MANAGEMENT", interfaces=["FastEthernet0/1", "FastEthernet0/2"])
        self.assertIn("vlan 10", cmds)
        self.assertIn("name MANAGEMENT", cmds)
        self.assertIn("switchport access vlan 10", cmds)

    @patch("src.automation.cli_manager.pyautogui.hotkey")
    @patch("src.automation.cli_manager._get_active_modal_window")
    def test_close_cli_window_via_window_object(self, mock_get_window, mock_hotkey):
        mock_win = MagicMock()
        mock_get_window.return_value = mock_win
        from src.automation.cli_manager import close_cli_window
        close_cli_window(mock_win)
        mock_win.close.assert_called_once()

    @patch("src.automation.cli_manager.pyautogui.hotkey")
    @patch("src.automation.cli_manager._get_active_modal_window")
    def test_close_cli_window_via_alt_f4_fallback(self, mock_get_window, mock_hotkey):
        mock_get_window.return_value = None
        from src.automation.cli_manager import close_cli_window
        close_cli_window()
        mock_hotkey.assert_called_with("alt", "f4")

    @patch("src.automation.cli_manager.read_cli_output")
    @patch("src.automation.cli_manager.pyautogui.press")
    def test_wait_for_ios_ready_success(self, mock_press, mock_read):
        mock_read.side_effect = ["Self decompressing...", "Router>"]
        from src.automation.cli_manager import wait_for_ios_ready
        ready = wait_for_ios_ready(timeout_seconds=5.0, poll_interval=0.1)
        self.assertTrue(ready)

    @patch("src.automation.cli_manager.close_cli_window")
    @patch("src.automation.cli_manager.type_text_payload")
    @patch("src.automation.cli_manager.pyautogui.press")
    def test_execute_ios_commands_with_close_window(self, mock_press, mock_type, mock_close):
        execute_ios_commands(["enable"], close_window_after=True)
        mock_close.assert_called_once()


if __name__ == "__main__":
    unittest.main()

