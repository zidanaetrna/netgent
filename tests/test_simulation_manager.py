"""Unit tests for simulation_manager module."""

import unittest
from unittest.mock import MagicMock, patch

from src.automation.simulation_manager import (
    fast_forward_time,
    switch_to_realtime_mode,
    switch_to_simulation_mode,
)


class TestSimulationManager(unittest.TestCase):
    """Test simulation time acceleration and mode switching."""

    @patch("src.automation.simulation_manager.time.sleep")
    @patch("src.automation.simulation_manager.pyautogui.hotkey")
    def test_fast_forward_time_hotkey(self, mock_hotkey, mock_sleep):
        fast_forward_time(clicks=3, delay=0.01)

        self.assertEqual(mock_hotkey.call_count, 3)
        mock_hotkey.assert_called_with("alt", "d")

    @patch("src.automation.simulation_manager.pyautogui.hotkey")
    def test_switch_to_realtime_mode(self, mock_hotkey):
        switch_to_realtime_mode()
        mock_hotkey.assert_called_once_with("alt", "r")

    @patch("src.automation.simulation_manager.pyautogui.hotkey")
    def test_switch_to_simulation_mode(self, mock_hotkey):
        switch_to_simulation_mode()
        mock_hotkey.assert_called_once_with("alt", "s")


if __name__ == "__main__":
    unittest.main()
