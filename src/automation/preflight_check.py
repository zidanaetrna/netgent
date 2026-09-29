"""Pre-flight diagnostic and environment verification tool for Cisco Packet Tracer automation.

Performs health checks on:
- Cisco Packet Tracer window / process detection
- IPC Socket / PTBridge connectivity (127.0.0.1:7531)
- Python dependencies
- Recipe directory and schemas integrity
"""

import argparse
import json
import logging
import os
import socket
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path when executed directly as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import (
    CPT_WINDOW_TITLE_KEYWORDS,
    DEFAULT_IPC_HOST,
    DEFAULT_IPC_PORT,
    PROJECT_ROOT,
)
from src.automation.window_manager import find_cpt_window

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("preflight")


def check_python_dependencies() -> Dict[str, Any]:
    """Check required third-party packages."""
    required = ["yaml", "rich", "pyautogui", "pygetwindow"]
    installed = {}
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
            installed[pkg] = True
        except ImportError:
            installed[pkg] = False
            missing.append(pkg)

    return {
        "status": "PASS" if not missing else "FAIL",
        "missing": missing,
        "packages": installed,
    }


def check_window_status() -> Dict[str, Any]:
    """Inspect Cisco Packet Tracer window presence and state."""
    win = find_cpt_window()
    if not win:
        return {
            "status": "WARN",
            "message": "Cisco Packet Tracer window not detected. Make sure the application is open.",
            "window": None,
        }

    return {
        "status": "PASS",
        "title": win.title,
        "geometry": {
            "left": win.left,
            "top": win.top,
            "width": win.width,
            "height": win.height,
        },
        "is_maximized": win.isMaximized,
        "is_minimized": win.isMinimized,
    }


def check_ipc_port(host: str = DEFAULT_IPC_HOST, port: int = DEFAULT_IPC_PORT) -> Dict[str, Any]:
    """Check if the IPC socket bridge port is accessible or listening."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1.0)
    try:
        res = sock.connect_ex((host, port))
        sock.close()
        if res == 0:
            return {
                "status": "PASS",
                "message": f"IPC bridge socket is listening on {host}:{port}",
                "connected": True,
            }
        else:
            return {
                "status": "WARN",
                "message": f"IPC bridge not currently listening on {host}:{port}. Run NetGent or load extensions/cisco-pt-mcp.pts.",
                "connected": False,
            }
    except Exception as exc:
        return {
            "status": "WARN",
            "message": f"Could not probe IPC port: {exc}",
            "connected": False,
        }


def check_schemas_and_topologies() -> Dict[str, Any]:
    """Verify recipe schemas and topology catalog integrity."""
    schema_file = PROJECT_ROOT / "schemas" / "recipe_schema.json"
    topos_dir = PROJECT_ROOT / "topologies"

    if not schema_file.exists():
        return {"status": "FAIL", "message": f"Recipe schema missing: {schema_file}"}

    if not topos_dir.exists():
        return {"status": "FAIL", "message": f"Topologies directory missing: {topos_dir}"}

    recipes = list(topos_dir.glob("*.yaml")) + list(topos_dir.glob("*.yml"))
    return {
        "status": "PASS",
        "schema_exists": True,
        "topologies_found": len(recipes),
        "recipes": [r.name for r in recipes],
    }


def run_all_checks() -> Dict[str, Any]:
    """Run all pre-flight diagnostic checks and return aggregated results."""
    logger.info("Executing NetGent Pre-flight Environment Diagnostics...")
    checks = {
        "python_dependencies": check_python_dependencies(),
        "cpt_window": check_window_status(),
        "ipc_bridge": check_ipc_port(),
        "schemas_and_topologies": check_schemas_and_topologies(),
    }

    statuses = [c["status"] for c in checks.values()]
    if "FAIL" in statuses:
        overall = "FAIL"
    elif "WARN" in statuses:
        overall = "WARN"
    else:
        overall = "PASS"

    return {
        "overall_status": overall,
        "checks": checks,
    }


def main() -> int:
    """CLI entry point for pre-flight diagnostics."""
    parser = argparse.ArgumentParser(description="NetGent Pre-flight Diagnostics")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    results = run_all_checks()

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("\n" + "=" * 60)
        print(f"NETGENT PRE-FLIGHT DIAGNOSTICS: {results['overall_status']}")
        print("=" * 60)
        for name, data in results["checks"].items():
            status = data.get("status", "UNKNOWN")
            print(f"[{status}] {name.replace('_', ' ').title()}")
            for k, v in data.items():
                if k != "status":
                    print(f"    - {k}: {v}")
        print("=" * 60)

    return 0 if results["overall_status"] in ("PASS", "WARN") else 1


if __name__ == "__main__":
    sys.exit(main())
