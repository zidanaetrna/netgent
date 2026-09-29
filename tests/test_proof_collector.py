"""Unit tests for proof_collector module."""

import shutil
import unittest
from pathlib import Path

from src.core.proof_collector import (
    generate_proof_report,
    get_projects_root,
    init_project_workspace,
    save_project_recipe,
)


class TestProofCollector(unittest.TestCase):
    """Test project directory management and report markdown generation."""

    def setUp(self):
        self.test_proj_name = "test_lab_run"
        self.proj_dir = init_project_workspace(self.test_proj_name)

    def tearDown(self):
        if self.proj_dir.exists():
            shutil.rmtree(self.proj_dir)

    def test_init_project_workspace(self):
        self.assertTrue(self.proj_dir.is_dir())
        self.assertTrue((self.proj_dir / "assets").is_dir())

    def test_save_project_recipe(self):
        recipe = {"name": "Test Recipe", "devices": []}
        saved_file = save_project_recipe(self.proj_dir, recipe)
        self.assertTrue(saved_file.is_file())
        self.assertEqual(saved_file.name, "recipe.yaml")

    def test_generate_proof_report(self):
        recipe = {
            "name": "Test Star LAN",
            "description": "Star LAN test",
            "devices": [{"id": "PC1", "type": "pc"}],
            "configurations": {"PC1": {"ip_address": "192.168.1.10"}},
        }
        exec_report = {
            "engine": "hybrid",
            "verification_results": [
                {
                    "source": "PC1",
                    "target": "PC2",
                    "status": "success",
                    "screenshot": str(self.proj_dir / "assets" / "ping_PC1_to_PC2.png"),
                }
            ],
        }

        report_path = generate_proof_report(
            project_dir=self.proj_dir,
            recipe=recipe,
            execution_report=exec_report,
            academic_answers="Jawaban praktikum nomor 1-5.",
        )

        self.assertTrue(report_path.is_file())
        content = report_path.read_text(encoding="utf-8")
        self.assertIn("Test Star LAN", content)
        self.assertIn("Jawaban praktikum nomor 1-5.", content)
        self.assertIn("assets/ping_PC1_to_PC2.png", content)
        self.assertIn("192.168.1.10", content)


if __name__ == "__main__":
    unittest.main()
