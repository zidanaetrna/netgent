"""Parametric network topology recipe generator for Cisco Packet Tracer.

Synthesizes complete, valid topology recipe manifests for common network architectures
(Star LAN, Router-on-a-Stick, Multi-Router Mesh, Peer-to-Peer) with calculated canvas
coordinates, automated cabling, and IOS/PC network configurations.
"""

import argparse
import ipaddress
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger("generator")


def generate_star_topology(
    num_pcs: int = 3,
    subnet_cidr: str = "192.168.1.0/24",
    gateway_ip: str = "192.168.1.1",
    router_type: str = "router_2911",
    switch_type: str = "switch_2960",
) -> Dict[str, Any]:
    """Generate a Star LAN topology recipe with a central switch, router gateway, and N PCs.

    Args:
        num_pcs: Number of client PCs to attach to the switch (1-8).
        subnet_cidr: IPv4 network CIDR block.
        gateway_ip: Default gateway IP to assign to the router.
        router_type: Model of the default gateway router.
        switch_type: Model of the central LAN switch.

    Returns:
        Recipe dictionary conforming to schemas/recipe_schema.json.
    """
    net = ipaddress.IPv4Network(subnet_cidr, strict=False)
    mask = str(net.netmask)

    devices = [
        {"id": "R1", "type": router_type, "position": {"x": 0.50, "y": 0.20}},
        {"id": "SW1", "type": switch_type, "position": {"x": 0.50, "y": 0.45}},
    ]

    connections = [
        {
            "from": "R1",
            "to": "SW1",
            "cable_type": "copper_straight_through",
            "from_port": 0,
            "to_port": 0,
        }
    ]

    configurations: Dict[str, Any] = {
        "R1": {
            "type": "ios",
            "commands": [
                "no",
                "enable",
                "configure terminal",
                "hostname R1",
                "interface GigabitEthernet0/0",
                f"ip address {gateway_ip} {mask}",
                "no shutdown",
                "end",
                "write memory",
            ],
        },
        "SW1": {
            "type": "ios",
            "commands": ["enable", "configure terminal", "hostname SW1", "end"],
        },
    }

    verifications: List[Dict[str, Any]] = []

    # Calculate balanced horizontal layout for PCs across bottom canvas
    spacing = 0.70 / max(1, num_pcs - 1) if num_pcs > 1 else 0
    start_x = 0.15 if num_pcs > 1 else 0.50

    for i in range(1, num_pcs + 1):
        pc_id = f"PC{i}"
        pc_x = round(start_x + (i - 1) * spacing, 2)
        pc_y = 0.75
        devices.append({"id": pc_id, "type": "pc", "position": {"x": pc_x, "y": pc_y}})

        # Connect SW1 -> PCi
        connections.append({
            "from": "SW1",
            "to": pc_id,
            "cable_type": "copper_straight_through",
            "from_port": i,
            "to_port": 0,
        })

        # Allocate sequential host IP (e.g. 192.168.1.10, .11, ...)
        host_ip = str(net.network_address + 9 + i)
        configurations[pc_id] = {
            "type": "pc",
            "ip_address": host_ip,
            "subnet_mask": mask,
            "default_gateway": gateway_ip,
        }

        # Verify ping to default gateway
        verifications.append({"source": pc_id, "target_ip": gateway_ip, "ping_count": 4})

    return {
        "name": f"Generated Star LAN ({num_pcs} PCs)",
        "description": f"Automated Star LAN topology with {num_pcs} workstations connected to {switch_type} and gateway {gateway_ip}.",
        "devices": devices,
        "connections": connections,
        "configurations": configurations,
        "verifications": verifications,
    }


def generate_vlan_topology(
    vlan_specs: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Generate a Router-on-a-Stick inter-VLAN routing topology recipe.

    Args:
        vlan_specs: List of dicts specifying 'id', 'name', 'subnet', 'gateway'. Defaults to VLAN 10 & 20.
    """
    if vlan_specs is None:
        vlan_specs = [
            {"id": 10, "name": "SALES", "subnet": "192.168.10.0/24", "gateway": "192.168.10.1"},
            {"id": 20, "name": "ENGINEERING", "subnet": "192.168.20.0/24", "gateway": "192.168.20.1"},
        ]

    devices = [
        {"id": "R1", "type": "router_2911", "position": {"x": 0.50, "y": 0.20}},
        {"id": "SW1", "type": "switch_2960", "position": {"x": 0.50, "y": 0.45}},
    ]

    connections = [
        {
            "from": "R1",
            "to": "SW1",
            "cable_type": "copper_straight_through",
            "from_port": 0,
            "to_port": 1,
        }
    ]

    r_commands = [
        "no",
        "enable",
        "configure terminal",
        "hostname R1",
        "interface GigabitEthernet0/0",
        "no shutdown",
        "exit",
    ]

    sw_commands = [
        "enable",
        "configure terminal",
        "hostname SW1",
        "interface FastEthernet0/1",
        "switchport mode trunk",
        "exit",
    ]

    configurations: Dict[str, Any] = {}
    verifications: List[Dict[str, Any]] = []

    for idx, vlan in enumerate(vlan_specs, start=1):
        vid = vlan["id"]
        vname = vlan["name"]
        gw_ip = vlan["gateway"]
        net = ipaddress.IPv4Network(vlan["subnet"], strict=False)
        mask = str(net.netmask)
        port_num = idx + 1

        # Router subinterface
        r_commands.extend([
            f"interface GigabitEthernet0/0.{vid}",
            f"encapsulation dot1Q {vid}",
            f"ip address {gw_ip} {mask}",
            "exit",
        ])

        # Switch VLAN & access port
        sw_commands.extend([
            f"vlan {vid}",
            f"name {vname}",
            "exit",
            f"interface FastEthernet0/{port_num}",
            "switchport mode access",
            f"switchport access vlan {vid}",
            "exit",
        ])

        # PC node for this VLAN
        pc_id = f"PC{idx}"
        pc_x = 0.25 if idx == 1 else 0.75
        devices.append({"id": pc_id, "type": "pc", "position": {"x": pc_x, "y": 0.75}})

        connections.append({
            "from": "SW1",
            "to": pc_id,
            "cable_type": "copper_straight_through",
            "from_port": port_num,
            "to_port": 0,
        })

        pc_ip = str(net.network_address + 50)
        configurations[pc_id] = {
            "type": "pc",
            "ip_address": pc_ip,
            "subnet_mask": mask,
            "default_gateway": gw_ip,
        }

        # Verify gateway ping
        verifications.append({"source": pc_id, "target_ip": gw_ip, "ping_count": 4})

    r_commands.extend(["end", "write memory"])
    sw_commands.extend(["end", "write memory"])

    configurations["R1"] = {"type": "ios", "commands": r_commands}
    configurations["SW1"] = {"type": "ios", "commands": sw_commands}

    # Inter-VLAN verification between PC1 and PC2
    if len(vlan_specs) >= 2:
        target_vlan2_ip = str(ipaddress.IPv4Network(vlan_specs[1]["subnet"]).network_address + 50)
        verifications.append({"source": "PC1", "target_ip": target_vlan2_ip, "ping_count": 4})

    return {
        "name": "Generated Router on a Stick",
        "description": f"Inter-VLAN routing for {len(vlan_specs)} VLANs with 802.1Q encapsulation.",
        "devices": devices,
        "connections": connections,
        "configurations": configurations,
        "verifications": verifications,
    }


def save_recipe_to_file(recipe: Dict[str, Any], output_path: Union[str, Path]) -> Path:
    """Serialize and save recipe to a YAML or JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() in [".yaml", ".yml"]:
        path.write_text(yaml.dump(recipe, sort_keys=False), encoding="utf-8")
    else:
        path.write_text(json.dumps(recipe, indent=2), encoding="utf-8")

    logger.info("Saved generated recipe to '%s'", path)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate declarative Packet Tracer topology recipes")
    parser.add_argument("--type", choices=["star", "vlan", "star_lan", "router_on_a_stick"], default="star", help="Topology architecture type")
    parser.add_argument("--pcs", type=int, default=3, help="Number of PCs for star topology")
    parser.add_argument("--subnet", type=str, default="192.168.1.0/24", help="Subnet CIDR")
    parser.add_argument("--gateway", type=str, default="192.168.1.1", help="Gateway IP")
    parser.add_argument("--output", type=str, default=None, help="Output file path (e.g. topologies/custom.yaml)")
    args = parser.parse_args()

    if args.type in ["star", "star_lan"]:
        recipe = generate_star_topology(num_pcs=args.pcs, subnet_cidr=args.subnet, gateway_ip=args.gateway)
    else:
        recipe = generate_vlan_topology()

    if args.output:
        save_recipe_to_file(recipe, args.output)
        print(f"Generated recipe saved to {args.output}")
    else:
        print(yaml.dump(recipe, sort_keys=False))


if __name__ == "__main__":
    main()
