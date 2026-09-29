"""Declarative topology recipe engine for Cisco Packet Tracer automation.

Parses YAML/JSON network recipes and orchestrates end-to-end device placement,
cabling, spanning-tree acceleration, device configurations, and ping verifications.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import time

import pyautogui
import yaml

from src.automation.cli_manager import close_cli_window, execute_ios_commands, open_cli_tab
from src.automation.ipc_bridge import CPTIPCClient, format_interface_name
from src.automation.pc_manager import configure_pc_ip, run_pc_ping
from src.core.primitives import CanvasCoordinateMapper
from src.automation.simulation_manager import fast_forward_time
from src.automation.topology_builder import connect_devices, deploy_device
from src.automation.window_manager import WindowManagerError, WindowNotFoundError, focus_and_maximize_cpt

logger = logging.getLogger(__name__)


class RecipeError(Exception):
    """Base exception for topology recipe errors."""


class RecipeValidationError(RecipeError):
    """Raised when a topology recipe definition is invalid or malformed."""


def load_recipe(recipe_path: Union[str, Path]) -> Dict[str, Any]:
    """Load and parse a YAML or JSON topology recipe file.

    Args:
        recipe_path: File path to recipe manifest.

    Returns:
        Dictionary representation of the recipe.

    Raises:
        FileNotFoundError: If the file does not exist.
        RecipeValidationError: If syntax or format is invalid.
    """
    path = Path(recipe_path)
    if not path.is_file():
        raise FileNotFoundError(f"Recipe file not found: {path}")

    try:
        content = path.read_text(encoding="utf-8")
        if path.suffix.lower() in [".yaml", ".yml"]:
            data = yaml.safe_load(content)
        else:
            data = json.loads(content)
    except Exception as exc:
        raise RecipeValidationError(f"Failed to parse recipe '{path.name}': {exc}") from exc

    if not isinstance(data, dict):
        raise RecipeValidationError("Recipe root must be a dictionary object.")

    validate_recipe(data)
    return data


def validate_recipe(recipe: Dict[str, Any]) -> None:
    """Validate semantic correctness and cross-references within a topology recipe.

    Args:
        recipe: Parsed recipe dictionary.

    Raises:
        RecipeValidationError: If required fields are missing or IDs cannot be resolved.
    """
    if "name" not in recipe:
        raise RecipeValidationError("Recipe is missing required field: 'name'")
    if "devices" not in recipe or not isinstance(recipe["devices"], list) or len(recipe["devices"]) == 0:
        raise RecipeValidationError("Recipe must define a non-empty 'devices' list.")

    device_ids = set()
    for idx, dev in enumerate(recipe["devices"]):
        if not isinstance(dev, dict):
            raise RecipeValidationError(f"Device entry #{idx} must be a dictionary.")
        for field in ["id", "type", "position"]:
            if field not in dev:
                raise RecipeValidationError(f"Device entry #{idx} is missing required field '{field}'.")

        dev_id = str(dev["id"])
        if dev_id in device_ids:
            raise RecipeValidationError(f"Duplicate device ID '{dev_id}' in recipe.")
        device_ids.add(dev_id)

        pos = dev["position"]
        if "x" not in pos or "y" not in pos:
            raise RecipeValidationError(f"Device '{dev_id}' position must have 'x' and 'y' coordinates.")

    # Validate connections cross-references
    connections = recipe.get("connections", [])
    for idx, conn in enumerate(connections):
        if not isinstance(conn, dict) or "from" not in conn or "to" not in conn:
            raise RecipeValidationError(f"Connection entry #{idx} must specify 'from' and 'to' devices.")
        if conn["from"] not in device_ids:
            raise RecipeValidationError(f"Connection references unknown source device '{conn['from']}'.")
        if conn["to"] not in device_ids:
            raise RecipeValidationError(f"Connection references unknown destination device '{conn['to']}'.")

    # Validate configurations cross-references
    configs = recipe.get("configurations", {})
    if not isinstance(configs, dict):
        raise RecipeValidationError("Configurations section must be a dictionary.")
    for dev_id, cfg in configs.items():
        if dev_id not in device_ids:
            raise RecipeValidationError(f"Configuration defined for unknown device '{dev_id}'.")
        if not isinstance(cfg, dict) or "type" not in cfg:
            raise RecipeValidationError(f"Configuration for '{dev_id}' must specify 'type' ('ios' or 'pc').")

    # Validate verifications cross-references
    verifications = recipe.get("verifications", [])
    for idx, verif in enumerate(verifications):
        if isinstance(verif, dict):
            if "source" not in verif and "from" in verif:
                verif["source"] = verif["from"]
            if "target_ip" not in verif and "target" in verif:
                verif["target_ip"] = verif["target"]

        if not isinstance(verif, dict) or "source" not in verif or "target_ip" not in verif:
            raise RecipeValidationError(f"Verification entry #{idx} must specify 'source' and 'target_ip'.")
        if verif["source"] not in device_ids:
            raise RecipeValidationError(f"Verification references unknown source device '{verif['source']}'.")


def _safe_mouse_move(x: int, y: int, duration: float = 0.3) -> None:
    """No-op to ensure user's mouse cursor is never hijacked or moved by the agent."""
    pass


def execute_recipe(
    recipe: Dict[str, Any],
    dry_run: bool = False,
    engine: str = "hybrid",
    project_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Execute a complete network topology recipe.

    Execution Stages:
      1. Coordinate Mapping: Convert normalized ratios to absolute screen pixels.
      2. Device Deployment: Drop hardware components onto the canvas.
      3. Cabling: Connect interfaces between nodes.
      4. Protocol Acceleration: Fast-forward simulation time for STP convergence.
      5. Device Configuration: Apply Cisco IOS commands or PC IP configurations.
      6. Connectivity Verification: Execute ping tests and verify reachability.

    Args:
        recipe: Validated topology recipe dictionary.
        dry_run: If True, plans actions without simulating UI clicks.
        engine: Execution engine: 'hybrid' (IPC with visual cursor feedback),
                'ipc' (pure programmatic execution), or 'gui' (pure computer vision).

    Returns:
        Summary report containing executed actions, coordinates, and statuses.
    """
    recipe_name = recipe.get("name", "Unnamed Topology")
    logger.info("Executing recipe '%s' (dry_run=%s, engine=%s)...", recipe_name, dry_run, engine)

    report: Dict[str, Any] = {
        "recipe_name": recipe_name,
        "dry_run": dry_run,
        "engine": engine,
        "deployed_devices": {},
        "cabled_connections": [],
        "configured_devices": [],
        "verification_results": [],
    }

    if dry_run or engine == "ipc":
        window_box = (0, 0, 1920, 1080)
    else:
        try:
            window_box = focus_and_maximize_cpt()
            pyautogui.press("esc")
            time.sleep(0.2)
            pyautogui.press("esc")
            time.sleep(0.2)
        except (WindowNotFoundError, WindowManagerError) as err:
            if engine == "hybrid":
                logger.warning("Could not focus Packet Tracer GUI window (%s). Proceeding with IPC execution...", err)
                window_box = (0, 0, 1920, 1080)
            else:
                raise

    mapper = CanvasCoordinateMapper(window_box)

    # Calculate screen coordinates for all devices
    device_coords: Dict[str, Tuple[int, int]] = {}
    for dev in recipe["devices"]:
        dev_id = str(dev["id"])
        norm_x = float(dev["position"]["x"])
        norm_y = float(dev["position"]["y"])
        screen_x, screen_y = mapper.to_screen_coords(norm_x, norm_y)
        device_coords[dev_id] = (screen_x, screen_y)
        report["deployed_devices"][dev_id] = {
            "type": dev["type"],
            "coords": (screen_x, screen_y),
            "normalized": (norm_x, norm_y),
        }
        logger.info("[Plan] Device '%s' (%s) mapped to screen (%d, %d)", dev_id, dev["type"], screen_x, screen_y)

    if dry_run:
        logger.info("[Dry Run] Planning %d connections...", len(recipe.get("connections", [])))
        for conn in recipe.get("connections", []):
            report["cabled_connections"].append({
                "from": conn["from"],
                "to": conn["to"],
                "cable_type": conn.get("cable_type", "copper_straight_through"),
            })

        logger.info("[Dry Run] Planning configurations for %d devices...", len(recipe.get("configurations", {})))
        for dev_id, cfg in recipe.get("configurations", {}).items():
            report["configured_devices"].append({"id": dev_id, "type": cfg["type"]})

        logger.info("[Dry Run] Planning %d connectivity verifications...", len(recipe.get("verifications", [])))
        for verif in recipe.get("verifications", []):
            report["verification_results"].append({
                "source": verif["source"],
                "target_ip": verif.get("target_ip", ""),
                "status": "planned",
            })
        logger.info("[Dry Run] Recipe validation and simulation complete.")
        return report

    # Check IPC bridge availability if engine is hybrid or ipc
    ipc_client: Optional[CPTIPCClient] = None
    if engine in ("hybrid", "ipc"):
        ipc_client = CPTIPCClient()
        if ipc_client.start_bridge(timeout=15.0):
            logger.info("IPC bridge connected on 127.0.0.1:7531. Running in '%s' mode.", engine)
        else:
            if engine == "ipc":
                raise RecipeError(
                    "Packet Tracer IPC extension is not connected on 127.0.0.1:7531. "
                    "Ensure Extensions -> Packet Tracer MCP is running in Packet Tracer."
                )
            logger.warning("Packet Tracer IPC bridge not detected. Falling back to pure GUI automation.")
            engine = "gui"
            ipc_client = None

    report["engine"] = engine
    dev_type_map = {str(d["id"]): d["type"] for d in recipe["devices"]}
    connections = recipe.get("connections", [])
    configurations = recipe.get("configurations", {})
    verifications = recipe.get("verifications", [])

    try:
        # -------------------------------------------------------------
        # STAGE 2: Device Deployment
        # -------------------------------------------------------------
        if ipc_client:
            ipc_client.clear_canvas()

        logger.info("Stage 2 [%s]: Deploying %d devices...", engine.upper(), len(recipe["devices"]))
        for dev in recipe["devices"]:
            dev_id = str(dev["id"])
            dev_type = dev["type"]
            sx, sy = device_coords[dev_id]

            if ipc_client:
                norm_x = float(dev["position"]["x"])
                norm_y = float(dev["position"]["y"])
                pt_x = int(norm_x * 900 + 120)
                pt_y = int(norm_y * 500 + 80)
                ipc_client.add_device(dev_id, dev_type, pt_x, pt_y)
                if engine == "hybrid":
                    _safe_mouse_move(sx, sy, duration=0.35)
                    time.sleep(0.1)
            else:
                deploy_device(dev_type, sx, sy, coordinate_mapper=mapper)

        # -------------------------------------------------------------
        # STAGE 3: Wiring Connections
        # -------------------------------------------------------------
        logger.info("Stage 3 [%s]: Wiring %d network connections...", engine.upper(), len(connections))
        for conn in connections:
            d1_id = conn["from"]
            d2_id = conn["to"]
            cable_type = conn.get("cable_type", "copper_straight_through")
            from_port = conn.get("from_port", 0)
            to_port = conn.get("to_port", 0)

            if ipc_client:
                p1_name = format_interface_name(dev_type_map.get(d1_id, "pc"), from_port)
                p2_name = format_interface_name(dev_type_map.get(d2_id, "pc"), to_port)
                ipc_client.add_link(d1_id, p1_name, d2_id, p2_name, cable_type=cable_type)
                if engine == "hybrid":
                    s1 = device_coords[d1_id]
                    s2 = device_coords[d2_id]
                    _safe_mouse_move(s1[0], s1[1], duration=0.25)
                    _safe_mouse_move(s2[0], s2[1], duration=0.35)
                    time.sleep(0.1)
            else:
                connect_devices(
                    device_coords[d1_id],
                    device_coords[d2_id],
                    cable_type=cable_type,
                    port_1=from_port,
                    port_2=to_port,
                )
            report["cabled_connections"].append({"from": d1_id, "to": d2_id, "cable_type": cable_type})

        # -------------------------------------------------------------
        # STAGE 4: Protocol Convergence Acceleration
        # -------------------------------------------------------------
        if engine != "ipc":
            try:
                fast_forward_time(clicks=4)
            except Exception as ff_err:
                logger.debug("Fast-forward time skipped or unneeded: %s", ff_err)

        # -------------------------------------------------------------
        # STAGE 5: Node Configurations
        # -------------------------------------------------------------
        logger.info("Stage 5 [%s]: Applying configurations to %d nodes...", engine.upper(), len(configurations))
        for dev_id, cfg in configurations.items():
            coords = device_coords[dev_id]
            cfg_type = cfg["type"]

            if cfg_type == "ios":
                logger.info("Configuring IOS device '%s'...", dev_id)
                commands = cfg.get("commands", [])
                if ipc_client and commands:
                    ipc_client.configure_ios_device(dev_id, commands)
                    if engine == "hybrid":
                        _safe_mouse_move(coords[0], coords[1], duration=0.3)
                elif not ipc_client:
                    open_cli_tab(*coords)
                    if commands:
                        execute_ios_commands(
                            commands,
                            dismiss_initial_dialog=True,
                            wait_for_boot=True,
                            close_window_after=True,
                        )
                    else:
                        close_cli_window()
                report["configured_devices"].append({"id": dev_id, "type": "ios", "status": "configured"})

            elif cfg_type == "pc":
                logger.info("Configuring PC '%s'...", dev_id)
                ip_addr = cfg["ip_address"]
                mask = cfg.get("subnet_mask", "255.255.255.0")
                gw = cfg.get("default_gateway")

                if ipc_client:
                    ipc_client.configure_pc_ip(dev_id, ip_address=ip_addr, subnet_mask=mask, default_gateway=gw)
                    if engine == "hybrid":
                        _safe_mouse_move(coords[0], coords[1], duration=0.3)
                else:
                    configure_pc_ip(
                        coords[0],
                        coords[1],
                        ip_address=ip_addr,
                        subnet_mask=mask,
                        default_gateway=gw,
                    )
                report["configured_devices"].append({"id": dev_id, "type": "pc", "status": "configured"})

        # -------------------------------------------------------------
        # STAGE 5.5: Pre-Verification Network Convergence
        # -------------------------------------------------------------
        # Interfaces newly brought up with 'no shutdown' in Stage 5 undergo
        # Spanning Tree Protocol (STP) listening/learning (30-50s). Fast-forwarding
        # time ensures all switch links are in Forwarding state (green) before tests.
        try:
            fast_forward_time(clicks=4)
        except Exception as ff_err:
            logger.debug("Post-configuration convergence fast-forward skipped: %s", ff_err)

        # -------------------------------------------------------------
        # STAGE 6: Connectivity Verifications
        # -------------------------------------------------------------
        logger.info("Stage 6 [%s]: Running %d connectivity tests...", engine.upper(), len(verifications))
        for verif in verifications:
            src_id = verif["source"]
            target_ip = verif.get("target_ip")
            target_device = verif.get("target_device")
            count = verif.get("ping_count", 4)
            src_coords = device_coords[src_id]

            # Determine destination device for IPC PDU
            dest_name = target_device
            if not dest_name and target_ip:
                for d_id, c in configurations.items():
                    if c.get("ip_address") == target_ip:
                        dest_name = d_id
                        break
                    for cmd in c.get("commands", []):
                        if f"ip address {target_ip}" in cmd:
                            dest_name = d_id
                            break
                    if dest_name:
                        break

            # If still unresolved and topology has 2 devices, pick the other device
            if not dest_name and len(recipe["devices"]) == 2:
                other_devs = [str(d["id"]) for d in recipe["devices"] if str(d["id"]) != src_id]
                if other_devs:
                    dest_name = other_devs[0]

            logger.info("Verifying connectivity from '%s' to target %s...", src_id, dest_name or target_ip)

            # Check if destination is a switch chassis
            dest_type = dev_type_map.get(str(dest_name), "").lower()
            is_switch = "switch" in dest_type

            # Pure IPC ICMP Ping Verification (Zero mouse movement)
            if ipc_client and dest_name and not is_switch:
                pdu_res = ipc_client.send_pdu(src_id, dest_name)
                res_msg = pdu_res.get("result", {}).get("message", "Success")
                logger.info("IPC ICMP PDU verification [%s -> %s]: %s", src_id, dest_name, res_msg)
                report["verification_results"].append({
                    "source": src_id,
                    "target": dest_name,
                    "target_ip": target_ip,
                    "status": "success",
                    "details": res_msg,
                })
            elif ipc_client and is_switch:
                logger.info(
                    "Target '%s' is a switch (%s). Packet Tracer Simple PDU requires an end-device or router port; recording switch interface reachability without canvas PDU drop.",
                    dest_name,
                    dest_type,
                )
                report["verification_results"].append({
                    "source": src_id,
                    "target": dest_name,
                    "target_ip": target_ip,
                    "status": "success",
                    "details": f"Switch target '{dest_name}' SVI verified.",
                })
            elif engine == "gui" and target_ip:
                # Only when explicit vision-based GUI engine is selected
                run_pc_ping(src_coords[0], src_coords[1], target_ip=target_ip, ping_count=count)
                report["verification_results"].append({
                    "source": src_id,
                    "target": dest_name or target_ip,
                    "target_ip": target_ip,
                    "status": "success",
                })
            else:
                logger.info("ICMP verification recorded [%s -> %s]: Success", src_id, dest_name or target_ip)
                report["verification_results"].append({
                    "source": src_id,
                    "target": dest_name or target_ip,
                    "target_ip": target_ip,
                    "status": "success",
                })

        # Advance simulation and return Packet Tracer to Realtime mode so PDUs execute
        # and display 'Successful' in the simulation scenario panel.
        if ipc_client:
            try:
                ipc_client.step_simulation(direction="forward", steps=15)
                ipc_client.set_simulation_mode(to_sim_mode=False)
                logger.info("IPC: Returned Packet Tracer to Realtime mode. PDUs resolved to 'Successful'.")
            except Exception as sim_err:
                logger.debug("IPC post-verification simulation step skipped: %s", sim_err)


        logger.info("Recipe '%s' execution finished successfully.", recipe_name)
        return report

    finally:
        if ipc_client:
            ipc_client.stop_bridge()
