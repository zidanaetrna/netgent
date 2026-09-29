"""Inter-Process Communication (IPC) bridge client for Cisco Packet Tracer.

Connects to the Cisco Packet Tracer MCP plugin running inside Packet Tracer
over Socket.IO (127.0.0.1:7531). Enables reliable, programmatic topology deployment,
cabling, IP configuration, and IOS CLI execution without GUI fragility.
"""

from __future__ import annotations

import asyncio
import logging
import sys
import threading
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

import importlib.util
from pathlib import Path
import site

# Ensure user site-packages are available for mcp_server import
user_site = site.getusersitepackages()

PTBridge = None
try:
    bridge_file = Path(user_site) / "mcp_server" / "bridge.py"
    if bridge_file.is_file():
        spec = importlib.util.spec_from_file_location("cisco_pt_bridge_module", str(bridge_file))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            PTBridge = getattr(mod, "PTBridge", None)
except Exception as _exc:
    logger.debug("Could not load PTBridge directly: %s", _exc)

# Mapping from recipe abstract device types to Packet Tracer models
DEVICE_MODEL_MAP: Dict[str, str] = {
    "pc": "PC-PT",
    "server": "Server-PT",
    "laptop": "Laptop-PT",
    "printer": "Printer-PT",
    "switch": "2960-24TT",
    "switch_2960": "2960-24TT",
    "switch_3560": "3560-24PS",
    "router": "2911",
    "router_2911": "2911",
    "router_1941": "1941",
    "router_2811": "2811",
    "hub": "Hub-PT",
    "hub_pt": "Hub-PT",
}

# Mapping from recipe cable types to PT link types
CABLE_TYPE_MAP: Dict[str, str] = {
    "copper_straight_through": "straight",
    "copper_cross_over": "cross",
    "fiber": "fiber",
    "serial": "serial",
    "auto": "auto",
}


def normalize_device_model(device_type: str) -> str:
    """Normalize recipe device type to Packet Tracer internal model name."""
    clean_type = device_type.strip().lower()
    return DEVICE_MODEL_MAP.get(clean_type, "PC-PT")


def normalize_cable_type(cable_type: str) -> str:
    """Normalize recipe cable type to Packet Tracer link type."""
    clean_cable = cable_type.strip().lower()
    return CABLE_TYPE_MAP.get(clean_cable, "straight")


def format_interface_name(device_type: str, port_index_or_name: Any) -> str:
    """Resolve port index or string name to valid Packet Tracer interface name.

    Examples:
        - PC + 0 -> 'FastEthernet0'
        - Switch + 0 -> 'FastEthernet0/1'
        - Router + 0 -> 'GigabitEthernet0/0'
        - Explicit string 'FastEthernet0/1' -> 'FastEthernet0/1'
    """
    if isinstance(port_index_or_name, str):
        # Already an interface name like 'FastEthernet0' or 'GigabitEthernet0/0'
        return port_index_or_name.strip()

    index = int(port_index_or_name)
    clean_type = device_type.strip().lower()

    if clean_type in ("pc", "server", "laptop", "printer", "pc-pt", "server-pt"):
        return f"FastEthernet{index}"
    elif "switch" in clean_type or "2960" in clean_type or "3560" in clean_type:
        return f"FastEthernet0/{index + 1}"
    elif "router" in clean_type or "2911" in clean_type or "1941" in clean_type:
        return f"GigabitEthernet0/{index}"
    else:
        return f"FastEthernet{index}"


class CPTIPCClient:
    """Synchronous thread-safe client managing communication with Packet Tracer IPC bridge."""

    def __init__(self, host: str = "127.0.0.1", port: int = 7531) -> None:
        self.host = host
        self.port = port
        self._bridge: Optional[PTBridge] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._is_running = False

    def start_bridge(self, timeout: float = 15.0) -> bool:
        """Start the async Socket.IO server in a background thread and wait for PT to connect."""
        if PTBridge is None:
            logger.error("mcp_server package is not installed; cannot start PTBridge")
            return False

        if self._is_running:
            return True

        self._loop = asyncio.new_event_loop()
        self._bridge = PTBridge(host=self.host, port=self.port)

        ready_event = threading.Event()

        def _run_loop():
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._bridge.start())
            self._is_running = True
            ready_event.set()
            try:
                self._loop.run_forever()
            finally:
                try:
                    self._loop.run_until_complete(self._loop.shutdown_asyncgens())
                except Exception:
                    pass

        self._thread = threading.Thread(target=_run_loop, name="CPT-IPC-Bridge", daemon=True)
        self._thread.start()

        # Wait until HTTP server starts listening
        if not ready_event.wait(timeout=5.0):
            logger.error("Failed to start PTBridge background server within 5s")
            return False

        logger.info("PTBridge listening on http://%s:%d. Waiting for Packet Tracer plugin...", self.host, self.port)

        # Wait for Packet Tracer plugin to connect
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._bridge.wait_until_connected(timeout=timeout),
                self._loop,
            )
            future.result(timeout=timeout + 1.0)
            logger.info("Packet Tracer plugin successfully connected to IPC bridge.")
            return True
        except Exception as exc:
            logger.warning("Packet Tracer plugin did not connect within %.1fs: %s", timeout, exc)
            return False

    def stop_bridge(self) -> None:
        """Stop the background server and clean up event loop gracefully."""
        if not self._is_running or not self._loop:
            return

        # Suppress transport teardown noise during shutdown
        sys.unraisablehook = lambda hook_args: None
        logging.getLogger("asyncio").setLevel(logging.CRITICAL)
        logging.getLogger("aiohttp").setLevel(logging.CRITICAL)
        logging.getLogger("engineio").setLevel(logging.CRITICAL)

        async def _graceful_stop():
            if self._bridge:
                try:
                    await self._bridge.stop()
                except Exception:
                    pass
            try:
                cur = asyncio.current_task()
                pending = [t for t in asyncio.all_tasks() if t is not cur and not t.done()]
                for t in pending:
                    t.cancel()
                if pending:
                    await asyncio.gather(*pending, return_exceptions=True)
            except Exception:
                pass
            finally:
                self._loop.stop()

        try:
            future = asyncio.run_coroutine_threadsafe(_graceful_stop(), self._loop)
            future.result(timeout=2.0)
        except Exception:
            try:
                self._loop.call_soon_threadsafe(self._loop.stop)
            except Exception:
                pass

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        self._is_running = False
        logger.info("CPT IPC Bridge stopped.")

    @property
    def is_connected(self) -> bool:
        """Return True if Packet Tracer is currently connected to the bridge."""
        return bool(self._bridge and self._bridge.is_connected)

    def _call(self, tool_name: str, tool_input: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
        """Dispatch a tool call to Packet Tracer synchronously through the bridge."""
        if not self.is_connected or not self._loop or not self._bridge:
            raise RuntimeError("Packet Tracer is not connected to IPC bridge.")

        future = asyncio.run_coroutine_threadsafe(
            self._bridge.call_tool(tool_name, tool_input),
            self._loop,
        )
        return future.result(timeout=timeout)

    def get_network(self) -> Dict[str, Any]:
        """Query the full network topology state from Packet Tracer."""
        return self._call("getNetwork", {})

    def remove_devices(self, device_names: List[str]) -> Dict[str, Any]:
        """Remove devices from the workspace by name."""
        logger.info("IPC: Removing existing devices: %s", device_names)
        return self._call("removeDevice", {"deviceNames": device_names})

    def remove_links(self, endpoints: List[Dict[str, str]]) -> Dict[str, Any]:
        """Remove links from workspace given an array of {'device': ..., 'port': ...}."""
        logger.info("IPC: Removing %d links from canvas...", len(endpoints))
        return self._call("removeLink", {"links": endpoints})

    def clear_canvas(self) -> None:
        """Completely clean all links and devices from Packet Tracer workspace."""
        try:
            net = self.get_network()
            conns = net.get("result", {}).get("result", {}).get("connections", [])
            if conns:
                endpoints = [
                    {"device": c["from"], "port": c["fromInterface"]}
                    for c in conns
                    if isinstance(c, dict) and "from" in c and "fromInterface" in c
                ]
                if endpoints:
                    self.remove_links(endpoints)

            devs = net.get("result", {}).get("result", {}).get("devices", [])
            names = [d["name"] for d in devs if isinstance(d, dict) and "name" in d]
            if names:
                self.remove_devices(names)
            logger.info("IPC: Workspace canvas cleared cleanly.")
        except Exception as exc:
            logger.debug("IPC clear_canvas skipped: %s", exc)

    def add_device(self, device_name: str, device_model: str, x: int, y: int) -> Dict[str, Any]:
        """Deploy a device onto the Packet Tracer workspace at (x, y)."""
        model = normalize_device_model(device_model)
        logger.info("IPC: Deploying device '%s' (model: %s) at (%d, %d)...", device_name, model, x, y)
        return self._call("addDevice", {
            "deviceName": device_name,
            "deviceModel": model,
            "x": float(x),
            "y": float(y),
        })

    def add_link(
        self,
        dev1_name: str,
        dev1_port: str,
        dev2_name: str,
        dev2_port: str,
        cable_type: str = "straight",
    ) -> Dict[str, Any]:
        """Connect two devices with a specified cable."""
        link_type = normalize_cable_type(cable_type)
        logger.info(
            "IPC: Connecting '%s' [%s] <-> '%s' [%s] with cable '%s'...",
            dev1_name,
            dev1_port,
            dev2_name,
            dev2_port,
            link_type,
        )
        return self._call("addLink", {
            "device1Name": dev1_name,
            "device1Interface": dev1_port,
            "device2Name": dev2_name,
            "device2Interface": dev2_port,
            "linkType": link_type,
        })

    def configure_pc_ip(
        self,
        device_name: str,
        ip_address: str,
        subnet_mask: str = "255.255.255.0",
        default_gateway: Optional[str] = None,
        dns_server: Optional[str] = None,
        dhcp: bool = False,
    ) -> Dict[str, Any]:
        """Configure IP settings on a PC or Server."""
        logger.info("IPC: Configuring PC '%s' IP=%s, Mask=%s, GW=%s...", device_name, ip_address, subnet_mask, default_gateway)
        payload: Dict[str, Any] = {
            "deviceName": device_name,
            "dhcpEnabled": dhcp,
            "ipaddress": ip_address,
            "subnetMask": subnet_mask,
        }
        if default_gateway:
            payload["defaultGateway"] = default_gateway
        if dns_server:
            payload["dnsServer"] = dns_server

        return self._call("configurePcIp", payload)

    def configure_ios_device(self, device_name: str, commands: List[str]) -> Dict[str, Any]:
        """Apply a list of IOS commands to a router or switch."""
        cmd_str = "\n".join(commands)
        logger.info("IPC: Applying %d IOS commands to '%s'...", len(commands), device_name)
        return self._call("configureIosDevice", {
            "deviceName": device_name,
            "commands": cmd_str,
        }, timeout=60.0)

    def send_pdu(self, source_device: str, destination_device: str) -> Dict[str, Any]:
        """Send an ICMP PDU (ping) between two devices in simulation."""
        logger.info("IPC: Sending PDU from '%s' to '%s'...", source_device, destination_device)
        return self._call("sendPdu", {
            "sourceDevice": source_device,
            "destinationDevice": destination_device,
        })

    def set_power(self, device_name: str, power_on: bool = True) -> Dict[str, Any]:
        """Turn device power on or off."""
        return self._call("setPower", {
            "deviceName": device_name,
            "power": power_on,
        })

    def set_simulation_mode(self, to_sim_mode: bool) -> Dict[str, Any]:
        """Switch Packet Tracer between simulation mode (True) and realtime mode (False)."""
        mode_str = "simulation" if to_sim_mode else "realtime"
        logger.info("IPC: Switching Packet Tracer to %s mode...", mode_str)
        return self._call("setSimulationMode", {
            "toSimMode": to_sim_mode,
        })

    def step_simulation(self, direction: str = "forward", steps: int = 1) -> Dict[str, Any]:
        """Step the simulation clock forward or backward, or reset it."""
        logger.info("IPC: Stepping simulation %s (%d steps)...", direction, steps)
        return self._call("stepSimulation", {
            "direction": direction,
            "steps": max(1, min(steps, 100)),
        })

    def get_pdu_results(self, types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Query outcome of PDUs in current simulation."""
        payload: Dict[str, Any] = {}
        if types:
            payload["types"] = types
        return self._call("getPduResults", payload)

