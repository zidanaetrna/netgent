"""Unit tests for topology_generator module."""

import unittest
from pathlib import Path

from src.core.config import PROJECT_ROOT
from src.core.recipe_runner import validate_recipe
from src.core.topology_generator import (
    generate_star_topology,
    generate_vlan_topology,
    save_recipe_to_file,
)


class TestTopologyGenerator(unittest.TestCase):
    """Test parametric topology generation and schema compliance."""

    def test_generate_star_topology(self):
        recipe = generate_star_topology(num_pcs=4, subnet_cidr="10.0.0.0/24", gateway_ip="10.0.0.1")
        self.assertEqual(len(recipe["devices"]), 6)  # R1 + SW1 + 4 PCs
        self.assertEqual(len(recipe["connections"]), 5)  # R1-SW1 + 4 SW1-PC
        # Validate against recipe schema validator
        validate_recipe(recipe)

    def test_generate_vlan_topology(self):
        recipe = generate_vlan_topology()
        self.assertIn("R1", recipe["configurations"])
        self.assertIn("SW1", recipe["configurations"])

        r_cmds = recipe["configurations"]["R1"]["commands"]
        has_dot1q = any("encapsulation dot1Q" in c for c in r_cmds)
        self.assertTrue(has_dot1q)

        validate_recipe(recipe)

    def test_save_recipe_to_file(self):
        recipe = generate_star_topology(num_pcs=2)
        out_yaml = PROJECT_ROOT / "tests" / "test_gen.yaml"
        try:
            save_recipe_to_file(recipe, out_yaml)
            self.assertTrue(out_yaml.is_file())
            content = out_yaml.read_text(encoding="utf-8")
            self.assertIn("Generated Star LAN", content)
        finally:
            if out_yaml.exists():
                out_yaml.unlink()


if __name__ == "__main__":
    unittest.main()
