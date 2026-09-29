---
name: cpt-automation
description: Autonomous UI automation skills for Cisco Packet Tracer (device deployment, cabling, deletion, and IOS command configuration).
---

# Cisco Packet Tracer Automation Skill

This skill provides autonomous control over Cisco Packet Tracer using computer vision template matching and input simulation.

## Prerequisites

1. Cisco Packet Tracer must be open and visible on screen (Windows display scaling set to 100%).
2. Dependencies installed via `requirements.txt`.
3. Reference template assets stored under `assets/reference_images/`.

## Key Capabilities & Python Modules

- **Window Management**: `src.window_manager.focus_and_maximize_cpt()`
  Brings Cisco Packet Tracer to the foreground, unminimizes, and maximizes the window.
- **Topology Building**: `src.topology_builder`
  - `deploy_device(device_type, target_x, target_y)`: Drops routers, switches, or PCs onto the canvas (with template matching and palette slot fallback).
  - `connect_devices(device_1_coords, device_2_coords, cable_type, port_1, port_2)`: Connects two devices with straight-through, crossover, or auto-connection cables, supporting port names or indices.
  - `delete_element(target_x, target_y)`: Removes a component from the canvas.
- **CLI Configuration**: `src.cli_manager`
  - `open_cli_tab(device_x, device_y)`: Opens device modal and selects the CLI tab with modal offset fallback.
  - `execute_ios_commands(command_list, dismiss_initial_dialog=True)`: Executes command sequence in IOS, automatically dismissing initial boot setup dialogs.
  - `read_cli_output()`: Extracts current terminal text buffer.
  - `verify_cli_command(command, expected_snippet)`: Executes and checks IOS commands for errors.
  - `configure_vlan(vlan_id, vlan_name, interfaces)`: Creates VLANs and assigns switchports.
  - `configure_trunk(interface_name)`: Configures 802.1Q trunk interfaces.
- **PC Desktop Automation**: `src.pc_manager`
  - `configure_pc_ip(device_x, device_y, ip_address, subnet_mask)`: Configures static IP on PC via Desktop app.
  - `run_pc_ping(device_x, device_y, target_ip, ping_count)`: Runs ping in PC Command Prompt.
- **Simulation & Time Controls**: `src.simulation_manager`
  - `fast_forward_time(clicks)`: Fast-forwards simulation time to immediately converge Spanning Tree Protocol (STP).
  - `switch_to_realtime_mode()`: Activates Realtime simulation mode.
  - `switch_to_simulation_mode()`: Activates Event/Simulation mode.
- **Topology Recipe Engine**: `src.recipe_runner`
  - `load_recipe(path)`: Loads and validates YAML/JSON declarative topology recipes.
  - `execute_recipe(recipe, dry_run=False)`: Orchestrates complete deployment, cabling, convergence, and verification.

## Example Workflows

### 1. Declarative Recipe Execution

```python
from src.recipe_runner import load_recipe, execute_recipe

recipe = load_recipe("topologies/star_lan.yaml")
report = execute_recipe(recipe, dry_run=False)
```

```python
from src.window_manager import focus_and_maximize_cpt
from src.primitives import CanvasCoordinateMapper
from src.topology_builder import deploy_device, connect_devices
from src.cli_manager import open_cli_tab, execute_ios_commands

window_box = focus_and_maximize_cpt()
mapper = CanvasCoordinateMapper(window_box)

r1_pos = mapper.to_screen_coords(0.3, 0.5)
r2_pos = mapper.to_screen_coords(0.7, 0.5)

deploy_device("router_2911", *r1_pos)
deploy_device("router_2911", *r2_pos)
connect_devices(r1_pos, r2_pos, cable_type="copper_cross_over")

open_cli_tab(*r1_pos)
execute_ios_commands([
    "no",
    "enable",
    "configure terminal",
    "hostname R1",
    "interface GigabitEthernet0/0",
    "ip address 192.168.1.1 255.255.255.0",
    "no shutdown",
    "end"
])
```

### 2. PC-to-PC Crossover Ping Test (Task 5.2)

```python
from src.window_manager import focus_and_maximize_cpt
from src.primitives import CanvasCoordinateMapper
from src.topology_builder import deploy_device, connect_devices
from src.pc_manager import configure_pc_ip, run_pc_ping

window_box = focus_and_maximize_cpt()
mapper = CanvasCoordinateMapper(window_box)

pc1_pos = mapper.to_screen_coords(0.35, 0.45)
pc2_pos = mapper.to_screen_coords(0.65, 0.45)

# Deploy two PCs and connect with crossover cable
deploy_device("pc", *pc1_pos, coordinate_mapper=mapper)
deploy_device("pc", *pc2_pos, coordinate_mapper=mapper)
connect_devices(pc1_pos, pc2_pos, cable_type="copper_cross_over")

# Assign IP addresses in 192.168.1.0/24 subnet
configure_pc_ip(*pc1_pos, "192.168.1.1", "255.255.255.0")
configure_pc_ip(*pc2_pos, "192.168.1.2", "255.255.255.0")

# Verify connectivity from PC1 to PC2
run_pc_ping(*pc1_pos, "192.168.1.2", ping_count=4)
```
