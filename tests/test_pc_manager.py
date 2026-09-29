"""Unit tests for pc_manager module."""

import unittest
from unittest.mock import MagicMock, patch

from src.automation.pc_manager import configure_pc_ip, open_pc_desktop, run_pc_ping


class TestPCManager(unittest.TestCase):
    """Test PC desktop app automation and ping verification."""

    def _create_mock_window(self):
        mock_win = MagicMock()
        mock_win.title = "PC0"
        mock_win.left = 100
        mock_win.top = 100
        mock_win.width = 600
        mock_win.height = 400
        return mock_win

    @patch("src.automation.pc_manager.ensure_pc_power_on")
    @patch("src.automation.pc_manager.pyautogui.press")
    @patch("src.automation.pc_manager.pyautogui.click")
    @patch("src.automation.pc_manager.pyautogui.doubleClick")
    @patch("src.automation.pc_manager._get_active_pc_window")
    def test_open_pc_desktop(self, mock_get_win, mock_double_click, mock_click, mock_press, mock_power):
        mock_win = self._create_mock_window()
        mock_get_win.return_value = mock_win

        res = open_pc_desktop(300, 200)

        self.assertEqual(res, mock_win)
        mock_double_click.assert_called_with(300, 200)
        mock_power.assert_called_once_with(mock_win)
        # Desktop tab offset: left + 205, top + 72
        mock_click.assert_called_with(mock_win.left + 205, mock_win.top + 72)

    @patch("src.automation.pc_manager.pyautogui.click")
    @patch("src.automation.pc_manager.pyautogui.screenshot")
    def test_ensure_pc_power_on(self, mock_screenshot, mock_click):
        from src.automation.pc_manager import ensure_pc_power_on
        mock_win = self._create_mock_window()
        # Simulate dark LED
        mock_img = MagicMock()
        mock_screenshot.return_value = mock_img
        with patch("src.automation.pc_manager.np.array") as mock_np:
            import numpy as np
            mock_np.return_value = np.zeros((6, 6, 3), dtype=np.uint8)
            result = ensure_pc_power_on(mock_win)
            self.assertTrue(result)
            mock_click.assert_called_with(mock_win.left + 370, mock_win.top + 297)

    @patch("src.automation.pc_manager.pyautogui.press")
    @patch("src.automation.pc_manager.pyautogui.write")
    @patch("src.automation.pc_manager.pyautogui.hotkey")
    @patch("src.automation.pc_manager.pyautogui.click")
    @patch("src.automation.pc_manager.open_pc_desktop")
    def test_configure_pc_ip(self, mock_open_desktop, mock_click, mock_hotkey, mock_write, mock_press):
        mock_win = self._create_mock_window()
        mock_open_desktop.return_value = mock_win

        configure_pc_ip(300, 200, "192.168.1.10", "255.255.255.0", default_gateway="192.168.1.1")

        mock_open_desktop.assert_called_with(300, 200)
        # Verify IP Configuration tile click (left + 100, top + 138)
        mock_click.assert_any_call(mock_win.left + 100, mock_win.top + 138)
        # Verify writing IP and mask
        mock_write.assert_any_call("192.168.1.10", interval=unittest.mock.ANY)
        mock_write.assert_any_call("255.255.255.0", interval=unittest.mock.ANY)
        mock_write.assert_any_call("192.168.1.1", interval=unittest.mock.ANY)
        # Verify closing dialogs
        mock_press.assert_any_call("esc")

    @patch("src.automation.pc_manager.time.sleep")
    @patch("src.automation.pc_manager.type_text_payload")
    @patch("src.automation.pc_manager.pyautogui.press")
    @patch("src.automation.pc_manager.pyautogui.click")
    @patch("src.automation.pc_manager.open_pc_desktop")
    def test_run_pc_ping(self, mock_open_desktop, mock_click, mock_press, mock_type, mock_sleep):
        mock_win = self._create_mock_window()
        mock_open_desktop.return_value = mock_win

        run_pc_ping(300, 200, "192.168.1.2", ping_count=4)

        mock_open_desktop.assert_called_with(300, 200)
        # Verify Command Prompt tile click (left + 585, top + 138)
        mock_click.assert_any_call(mock_win.left + 585, mock_win.top + 138)
        # Verify ping command executed
        mock_type.assert_called_once_with("ping 192.168.1.2 -n 4", interval=unittest.mock.ANY, press_enter=True)
        # Verify closing windows
        mock_press.assert_any_call("esc")


if __name__ == "__main__":
    unittest.main()
