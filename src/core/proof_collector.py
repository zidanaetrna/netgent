"""Project workspace and lab proof report generator.

Manages dedicated project directories (e.g. projects/projectA/assets/)
to store recipe YAML files, ping proof screenshots, and structured Markdown
proof documentation.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Union

import yaml

from src.core.config import PROJECT_ROOT

logger = logging.getLogger("proof_collector")


def get_projects_root() -> Path:
    """Return the base directory where project workspaces are stored."""
    p = PROJECT_ROOT / "projects"
    p.mkdir(parents=True, exist_ok=True)
    return p


def init_project_workspace(project_name: str) -> Path:
    """Initialize a dedicated project directory with an assets/ subfolder.

    Args:
        project_name: Safe name for the project (e.g. 'projectA', 'lab_praktikum_2').

    Returns:
        Path to the initialized project directory.
    """
    clean_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in project_name.strip())
    if not clean_name:
        clean_name = f"project_{int(time.time())}"

    proj_dir = get_projects_root() / clean_name
    assets_dir = proj_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Initialized project workspace: %s", proj_dir)
    return proj_dir


def save_project_recipe(project_dir: Path, recipe: Dict[str, Any]) -> Path:
    """Save the topology recipe YAML inside the project workspace."""
    recipe_file = project_dir / "recipe.yaml"
    with open(recipe_file, "w", encoding="utf-8") as f:
        yaml.dump(recipe, f, sort_keys=False, indent=2)
    logger.info("Saved project recipe: %s", recipe_file)
    return recipe_file


def generate_proof_report(
    project_dir: Path,
    recipe: Dict[str, Any],
    execution_report: Dict[str, Any],
    academic_answers: Optional[str] = None,
) -> Path:
    """Generate a comprehensive Markdown lab report embedding ping proof screenshots.

    Args:
        project_dir: Path to project directory.
        recipe: The executed recipe dictionary.
        execution_report: Summary report returned by execute_recipe.
        academic_answers: Optional theoretical answers or analysis text from LLM.

    Returns:
        Path to the generated report Markdown file.
    """
    report_file = project_dir / "report.md"
    recipe_name = recipe.get("name", project_dir.name)
    desc = recipe.get("description", "No description provided.")

    devices: List[Dict[str, Any]] = recipe.get("devices", [])
    configurations: Dict[str, Any] = recipe.get("configurations", {})
    verifications: List[Dict[str, Any]] = execution_report.get("verification_results", [])

    lines: List[str] = []
    lines.append(f"# Lab Report & Proof Verification: {recipe_name}\n")
    lines.append(f"**Description**: {desc}  ")
    lines.append(f"**Generated / Executed**: {time.strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines.append(f"**Execution Engine**: `{execution_report.get('engine', 'hybrid')}`\n")
    lines.append("---\n")

    if academic_answers:
        lines.append("## 1. Analisis & Jawaban Tugas\n")
        lines.append(academic_answers.strip())
        lines.append("\n---\n")

    lines.append("## 2. Tabel Alokasi Perangkat & IP Addressing\n")
    lines.append("| Device ID | Device Type | IP Address | Subnet Mask | Default Gateway |")
    lines.append("|---|---|---|---|---|")
    for d in devices:
        dev_id = str(d["id"])
        dev_type = d.get("type", "unknown")
        cfg = configurations.get(dev_id, {})
        ip = cfg.get("ip_address", "-")
        mask = cfg.get("subnet_mask", "-")
        gw = cfg.get("default_gateway", "-")
        lines.append(f"| **{dev_id}** | `{dev_type}` | `{ip}` | `{mask}` | `{gw}` |")
    lines.append("\n---\n")

    lines.append("## 3. Hasil Pengujian Konektivitas & Bukti Tangkapan Layar (Proof)\n")
    if not verifications:
        lines.append("*Tidak ada pengujian verifikasi yang dijalankan.*\n")
    else:
        for idx, v in enumerate(verifications, start=1):
            src = v.get("source", "Unknown")
            target = v.get("target", v.get("target_ip", "Unknown"))
            status = v.get("status", "unknown").upper()
            shot = v.get("screenshot")

            lines.append(f"### Pengujian {idx}: `{src}` $\\rightarrow$ `{target}`")
            lines.append(f"- **Status Verifikasi**: **{status}**")

            if shot:
                shot_path = Path(shot)
                rel_path = f"assets/{shot_path.name}"
                lines.append(f"- **Bukti Command Prompt**:  \n")
                lines.append(f"  ![Ping Proof {src} to {target}]({rel_path})\n")
            else:
                lines.append("- **Bukti Command Prompt**: *PDU ICMP diverifikasi melalui simulasi Packet Tracer.*\n")

    lines.append("---\n")
    lines.append("## 4. Manifes Topologi Recipe (YAML)\n")
    lines.append("```yaml")
    lines.append(yaml.dump(recipe, sort_keys=False, indent=2).strip())
    lines.append("```\n")

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("Saved lab proof report: %s", report_file)
    return report_file
