"""Unit tests for topology_builder module."""

import unittest
from unittest.mock import MagicMock, patch

from src.core.primitives import CanvasCoordinateMapper
from src.automation.topology_builder import (
    CABLE_CATALOG,
    CABLE_PALETTE_INDEX,
    DEVICE_CATALOG,
    TopologyError,
    connect_devices,
    delete_element,
    deploy_device,
)


class TestTopologyCatalog(unittest.TestCase):
    """Test device and cable catalog integrity."""

    def test_device_catalog_structure(self):
        expected_keys = {"category", "subcategory", "template", "palette_index"}
        for device_name, info in DEVICE_CATALOG.items():
            self.assertTrue(expected_keys.issubset(set(info.keys())), f"Missing keys in {device_name}")
            self.assertIsInstance(info["palette_index"], int)

    def test_cable_catalog_structure(self):
        for cable_name, template_name in CABLE_CATALOG.items():
            self.assertIn(cable_name, CABLE_PALETTE_INDEX)
            self.assertIsInstance(CABLE_PALETTE_INDEX[cable_name], int)


class TestTopologyBuilderActions(unittest.TestCase):
    """Test topology builder functions with mocked UI interactions."""

    def setUp(self):
        self.mock_mapper = CanvasCoordinateMapper((0, 0, 1920, 1080))

    def test_deploy_unknown_device_raises(self):
        with self.assertRaises(TopologyError):
            deploy_device("quantum_switch_9999", 500, 500)

    @patch("src.automation.topology_builder.pyautogui.click")
    @patch("src.automation.topology_builder.find_and_click_element")
    def test_deploy_device_success(self, mock_find_click, mock_click):
        mock_find_click.return_value = (100, 200)

        deployed_pos = deploy_device("router_2911", 600, 400, coordinate_mapper=self.mock_mapper)
        self.assertEqual(deployed_pos, (600, 400))
        mock_click.assert_called_with(600, 400)

    @patch("src.automation.topology_builder.pyautogui.click")
    def test_deploy_device_clamped_coordinates(self, mock_click):
        with patch("src.automation.topology_builder.find_and_click_element") as mock_find_click:
            mock_find_click.return_value = (100, 200)
            deployed_pos = deploy_device("router_2911", 5000, -100, coordinate_mapper=self.mock_mapper)
            # Clamped to canvas bounds
            self.assertEqual(deployed_pos[0], self.mock_mapper.canvas_right)
            self.assertEqual(deployed_pos[1], self.mock_mapper.canvas_top)

    @patch("src.automation.topology_builder.find_and_click_element")
    @patch("src.automation.topology_builder.pyautogui.press")
    @patch("src.automation.topology_builder.pyautogui.click")
    @patch("src.automation.topology_builder._select_cable_tool")
    @patch("src.automation.topology_builder._select_port")
    def test_connect_devices_with_ports(self, mock_port, mock_cable, mock_click, mock_press, mock_find_click):
        mock_find_click.return_value = (56, 483)
        dev1 = (300, 300)
        dev2 = (600, 300)

        connect_devices(dev1, dev2, cable_type="copper_cross_over", port_1=1, port_2=2)

        mock_cable.assert_called_once()
        self.assertEqual(mock_click.call_count, 2)
        mock_click.assert_any_call(300, 300)
        mock_click.assert_any_call(600, 300)
        self.assertEqual(mock_port.call_count, 2)
        mock_press.assert_called_with("esc")

    @patch("src.automation.topology_builder.find_and_click_element")
    @patch("src.automation.topology_builder.pyautogui.press")
    @patch("src.automation.topology_builder.pyautogui.click")
    @patch("src.automation.topology_builder._select_cable_tool")
    @patch("src.automation.topology_builder._select_port")
    def test_connect_devices_auto_connection_skips_ports(self, mock_port, mock_cable, mock_click, mock_press, mock_find_click):
        mock_find_click.return_value = (56, 483)
        dev1 = (300, 300)
        dev2 = (600, 300)

        connect_devices(dev1, dev2, cable_type="auto_connection")

        mock_cable.assert_called_once()
        self.assertEqual(mock_click.call_count, 2)
        # Port selection popup should NOT be triggered for auto_connection
        mock_port.assert_not_called()
        mock_press.assert_called_with("esc")

    @patch("src.automation.topology_builder.pyautogui.press")
    @patch("src.automation.topology_builder.pyautogui.click")
    @patch("src.automation.topology_builder.find_and_click_element")
    def test_delete_element(self, mock_find_click, mock_click, mock_press):
        delete_element(450, 450)
        mock_click.assert_called_with(450, 450)
        mock_press.assert_any_call("enter")
        mock_press.assert_any_call("esc")

    @patch("src.automation.topology_builder.find_cpt_window")
    @patch("src.automation.topology_builder.pyautogui.click")
    @patch("src.automation.topology_builder.find_and_click_element")
    def test_deploy_device_fallback_on_template_error(self, mock_find_click, mock_click, mock_window):
        from src.core.primitives import ElementNotFoundError
        # Simulate template matching failure
        mock_find_click.side_effect = ElementNotFoundError("Failed to find category_end_devices.png")
        mock_win = MagicMock()
        mock_win.left = 0
        mock_win.top = 0
        mock_win.width = 1920
        mock_win.height = 1080
        mock_window.return_value = mock_win

        deployed_pos = deploy_device("pc", 500, 400, coordinate_mapper=self.mock_mapper)
        self.assertEqual(deployed_pos, (500, 400))
        # Should click fallback coordinates and target placement
        self.assertTrue(mock_click.call_count >= 2)


if __name__ == "__main__":
    unittest.main()
