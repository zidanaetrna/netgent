"""Unit tests for recipe_runner module."""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.core.config import PROJECT_ROOT
from src.core.recipe_runner import (
    RecipeValidationError,
    execute_recipe,
    load_recipe,
    validate_recipe,
)


class TestRecipeRunner(unittest.TestCase):
    """Test topology recipe loading, validation, and multi-stage execution."""

    def setUp(self):
        self.topologies_dir = PROJECT_ROOT / "topologies"
        self.sample_recipe = {
            "name": "Sample Test Network",
            "devices": [
                {"id": "R1", "type": "router_2911", "position": {"x": 0.4, "y": 0.3}},
                {"id": "PC1", "type": "pc", "position": {"x": 0.6, "y": 0.7}},
            ],
            "connections": [
                {
                    "from": "R1",
                    "to": "PC1",
                    "cable_type": "copper_cross_over",
                    "from_port": 0,
                    "to_port": 0,
                }
            ],
            "configurations": {
                "R1": {"type": "ios", "commands": ["enable", "show running-config"]},
                "PC1": {"type": "pc", "ip_address": "192.168.1.10", "subnet_mask": "255.255.255.0"},
            },
            "verifications": [
                {"source": "PC1", "target_ip": "192.168.1.1", "ping_count": 4}
            ],
        }

    def test_load_all_prebuilt_recipes(self):
        """Ensure all pre-built YAML recipes exist and parse without schema errors."""
        recipe_files = ["pc_crossover_ping.yaml", "star_lan.yaml", "router_on_a_stick.yaml"]
        for filename in recipe_files:
            recipe_path = self.topologies_dir / filename
            self.assertTrue(recipe_path.is_file(), f"Recipe file {filename} must exist")
            data = load_recipe(recipe_path)
            self.assertIn("name", data)
            self.assertIn("devices", data)
            self.assertGreater(len(data["devices"]), 0)

    def test_validate_recipe_success(self):
        validate_recipe(self.sample_recipe)

    def test_validate_missing_name_raises(self):
        bad_recipe = {"devices": [{"id": "PC1", "type": "pc", "position": {"x": 0.5, "y": 0.5}}]}
        with self.assertRaises(RecipeValidationError):
            validate_recipe(bad_recipe)

    def test_validate_missing_devices_raises(self):
        bad_recipe = {"name": "No devices"}
        with self.assertRaises(RecipeValidationError):
            validate_recipe(bad_recipe)

    def test_validate_duplicate_device_id_raises(self):
        bad_recipe = {
            "name": "Duplicate IDs",
            "devices": [
                {"id": "PC1", "type": "pc", "position": {"x": 0.2, "y": 0.2}},
                {"id": "PC1", "type": "pc", "position": {"x": 0.8, "y": 0.8}},
            ],
        }
        with self.assertRaises(RecipeValidationError):
            validate_recipe(bad_recipe)

    def test_validate_unknown_connection_target_raises(self):
        bad_recipe = {
            "name": "Bad Connection",
            "devices": [{"id": "PC1", "type": "pc", "position": {"x": 0.2, "y": 0.2}}],
            "connections": [{"from": "PC1", "to": "PC_NONEXISTENT"}],
        }
        with self.assertRaises(RecipeValidationError):
            validate_recipe(bad_recipe)

    def test_validate_unknown_configuration_device_raises(self):
        bad_recipe = {
            "name": "Bad Config",
            "devices": [{"id": "PC1", "type": "pc", "position": {"x": 0.2, "y": 0.2}}],
            "configurations": {"GHOST_DEVICE": {"type": "pc", "ip_address": "1.1.1.1"}},
        }
        with self.assertRaises(RecipeValidationError):
            validate_recipe(bad_recipe)

    def test_dry_run_execution(self):
        report = execute_recipe(self.sample_recipe, dry_run=True)
        self.assertTrue(report["dry_run"])
        self.assertIn("R1", report["deployed_devices"])
        self.assertIn("PC1", report["deployed_devices"])
        self.assertEqual(len(report["cabled_connections"]), 1)
        self.assertEqual(len(report["configured_devices"]), 2)
        self.assertEqual(len(report["verification_results"]), 1)

    @patch("src.core.recipe_runner.pyautogui.press")
    @patch("src.core.recipe_runner.run_pc_ping")
    @patch("src.core.recipe_runner.configure_pc_ip")
    @patch("src.core.recipe_runner.execute_ios_commands")
    @patch("src.core.recipe_runner.open_cli_tab")
    @patch("src.core.recipe_runner.fast_forward_time")
    @patch("src.core.recipe_runner.connect_devices")
    @patch("src.core.recipe_runner.deploy_device")
    @patch("src.core.recipe_runner.focus_and_maximize_cpt")
    def test_mock_live_execution(
        self,
        mock_focus,
        mock_deploy,
        mock_connect,
        mock_fft,
        mock_open_cli,
        mock_exec_ios,
        mock_config_pc,
        mock_ping,
        mock_press,
    ):
        mock_focus.return_value = (0, 0, 1920, 1080)

        report = execute_recipe(self.sample_recipe, dry_run=False, engine="gui")

        # Verify Stage 2: Deployment
        self.assertEqual(mock_deploy.call_count, 2)

        # Verify Stage 3: Cabling
        mock_connect.assert_called_once()

        # Verify Stage 4 & 5.5: STP Fast-forwarding
        self.assertGreaterEqual(mock_fft.call_count, 1)

        # Verify Stage 5: IOS & PC configuration
        mock_open_cli.assert_called_once()
        mock_exec_ios.assert_called_once()
        mock_config_pc.assert_called_once()

        # Verify Stage 6: Ping verification
        mock_ping.assert_called_once()

    @patch("src.core.recipe_runner.CPTIPCClient")
    def test_mock_ipc_execution(self, mock_ipc_cls):
        mock_client = MagicMock()
        mock_client.start_bridge.return_value = True
        mock_client.send_pdu.return_value = {"result": {"message": "Success"}}
        mock_ipc_cls.return_value = mock_client

        report = execute_recipe(self.sample_recipe, dry_run=False, engine="ipc")

        self.assertEqual(mock_client.add_device.call_count, 2)
        mock_client.add_link.assert_called_once()
        mock_client.configure_ios_device.assert_called_once()
        mock_client.configure_pc_ip.assert_called_once()
        mock_client.send_pdu.assert_called_once()
        self.assertEqual(report["engine"], "ipc")


if __name__ == "__main__":
    unittest.main()
