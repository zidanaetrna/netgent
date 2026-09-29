"""Model Context Protocol (MCP) server for Cisco Packet Tracer automation.

Exposes Netgent's autonomous Packet Tracer tools over standard MCP JSON-RPC 2.0 (stdio),
allowing AI agents (Antigravity, Claude Desktop, etc.) to control Packet Tracer directly.
"""

import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path when executed directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.automation.cli_manager import (
    configure_interface_ip,
    configure_trunk,
    configure_vlan,
    execute_ios_commands,
    open_cli_tab,
    read_cli_output,
    verify_cli_command,
)
from src.automation.pc_manager import configure_pc_ip, run_pc_ping
from src.core.recipe_runner import execute_recipe, load_recipe
from src.automation.simulation_manager import (
    fast_forward_time,
    switch_to_realtime_mode,
    switch_to_simulation_mode,
)
from src.automation.topology_builder import connect_devices, delete_element, deploy_device
from src.automation.window_manager import focus_and_maximize_cpt

# Logging to stderr so stdin/stdout remains dedicated to JSON-RPC
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [MCP] %(levelname)s: %(message)s",
)
logger = logging.getLogger("mcp_server")


def load_tools_catalog() -> List[Dict[str, Any]]:
    """Load tool specifications from schemas/skills_schema.json."""
    schema_path = PROJECT_ROOT / "schemas" / "skills_schema.json"
    if schema_path.is_file():
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                tools = data.get("tools", [])
                # Add execute_recipe tool
                tools.append({
                    "name": "execute_recipe",
                    "description": "Execute a declarative topology recipe (YAML or JSON).",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "recipe_path": {"type": "string", "description": "Path to YAML/JSON recipe file"},
                            "dry_run": {"type": "boolean", "default": False},
                        },
                        "required": ["recipe_path"],
                    },
                })
                # Normalize schema parameters to inputSchema for MCP compatibility
                for t in tools:
                    if "parameters" in t and "inputSchema" not in t:
                        t["inputSchema"] = t["parameters"]
                return tools
        except Exception as exc:
            logger.warning("Could not read skills_schema.json: %s", exc)

    return []


def handle_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """Dispatch an incoming MCP tool call to the corresponding Python function."""
    logger.info("Executing tool '%s' with args %s", tool_name, arguments)

    if tool_name == "focus_and_maximize_cpt":
        timeout = float(arguments.get("timeout", 5.0))
        box = focus_and_maximize_cpt(timeout=timeout)
        return {"geometry": box, "status": "focused"}

    elif tool_name == "deploy_device":
        device_type = str(arguments["device_type"])
        tx = int(arguments["target_x"])
        ty = int(arguments["target_y"])
        pos = deploy_device(device_type, tx, ty)
        return {"deployed_at": pos, "device_type": device_type}

    elif tool_name == "connect_devices":
        dev1 = tuple(arguments["device_1_coords"])
        dev2 = tuple(arguments["device_2_coords"])
        cable = arguments.get("cable_type", "copper_straight_through")
        p1 = arguments.get("port_1", arguments.get("port_1_index", 0))
        p2 = arguments.get("port_2", arguments.get("port_2_index", 0))
        connect_devices(dev1, dev2, cable_type=cable, port_1=p1, port_2=p2)
        return {"status": "connected", "device_1": dev1, "device_2": dev2, "cable": cable}

    elif tool_name == "delete_element":
        tx = int(arguments["target_x"])
        ty = int(arguments["target_y"])
        delete_element(tx, ty)
        return {"status": "deleted", "target": (tx, ty)}

    elif tool_name == "open_cli_tab":
        dx = int(arguments["device_x"])
        dy = int(arguments["device_y"])
        open_cli_tab(dx, dy)
        return {"status": "cli_opened", "device": (dx, dy)}

    elif tool_name == "execute_ios_commands":
        cmds = arguments["command_list"]
        dismiss = arguments.get("dismiss_initial_dialog", True)
        execute_ios_commands(cmds, dismiss_initial_dialog=dismiss)
        return {"status": "executed", "command_count": len(cmds)}

    elif tool_name == "configure_pc_ip":
        dx = int(arguments["device_x"])
        dy = int(arguments["device_y"])
        ip = arguments["ip_address"]
        mask = arguments.get("subnet_mask", "255.255.255.0")
        gw = arguments.get("default_gateway")
        configure_pc_ip(dx, dy, ip, mask, gw)
        return {"status": "configured", "ip": ip, "mask": mask, "gateway": gw}

    elif tool_name == "run_pc_ping":
        dx = int(arguments["device_x"])
        dy = int(arguments["device_y"])
        target = arguments["target_ip"]
        count = int(arguments.get("ping_count", 4))
        run_pc_ping(dx, dy, target, ping_count=count)
        return {"status": "ping_completed", "target_ip": target}

    elif tool_name == "fast_forward_time":
        clicks = int(arguments.get("clicks", 4))
        fast_forward_time(clicks=clicks)
        return {"status": "accelerated", "clicks": clicks}

    elif tool_name == "read_cli_output":
        text = read_cli_output()
        return {"output": text}

    elif tool_name == "configure_vlan":
        vid = int(arguments["vlan_id"])
        name = str(arguments["vlan_name"])
        interfaces = arguments.get("interfaces")
        cmds = configure_vlan(vid, name, interfaces)
        return {"commands": cmds, "vlan_id": vid, "vlan_name": name}

    elif tool_name == "execute_recipe":
        path = arguments["recipe_path"]
        dry_run = arguments.get("dry_run", False)
        recipe = load_recipe(path)
        report = execute_recipe(recipe, dry_run=dry_run)
        return {"report": report}

    raise ValueError(f"Unknown MCP tool: '{tool_name}'")


def process_json_rpc_message(msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Process a single incoming JSON-RPC 2.0 request and return the response."""
    msg_id = msg.get("id")
    method = msg.get("method")
    params = msg.get("params", {})

    logger.debug("Received method '%s' (id=%s)", method, msg_id)

    if method == "initialize":
        return {
            "jsonrpc": "2020-12",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False},
                },
                "serverInfo": {
                    "name": "cpt-netgent-server",
                    "version": "1.0.0",
                },
            },
        }

    elif method == "notifications/initialized":
        logger.info("Client completed MCP initialization handshake.")
        return None

    elif method == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

    elif method == "tools/list":
        tools = load_tools_catalog()
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": tools},
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        try:
            result = handle_tool_call(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                    "isError": False,
                },
            }
        except Exception as exc:
            logger.error("Tool '%s' failed: %s", tool_name, exc)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": f"Error: {exc}"}],
                    "isError": True,
                },
            }

    # Method not found
    if msg_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method not found: '{method}'"},
        }
    return None


def run_stdio_server() -> None:
    """Run the standard I/O loop consuming line-delimited JSON-RPC messages."""
    logger.info("Starting Netgent Packet Tracer MCP Server on stdio...")
    for line in sys.stdin:
        clean_line = line.strip()
        if not clean_line:
            continue

        try:
            req = json.loads(clean_line)
        except json.JSONDecodeError as exc:
            logger.error("JSON decode error: %s", exc)
            continue

        resp = process_json_rpc_message(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_stdio_server()
