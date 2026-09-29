---
name: cpt-automation
description: Autonomous IPC socket automation skills for Cisco Packet Tracer (programmatic device deployment, cabling, IP assignment, and IOS command configuration).
---

# Cisco Packet Tracer Automation Skill

This skill provides autonomous, programmatic control over Cisco Packet Tracer using a direct Inter-Process Communication (IPC) Socket bridge over port 7531 (`extensions/cisco-pt-mcp.pts`), eliminating mouse cursor hijacking and brittle visual template matching.

## Prerequisites

1. Cisco Packet Tracer 8.x open with IPC extension loaded (`extensions/cisco-pt-mcp.pts` running in Script Manager on port 7531).
2. Python dependencies installed via `requirements.txt`.
3. Valid YAML topology recipes located under `topologies/`.

## Key Capabilities & Modular Architecture

NetGent is organized into 4 clean layers:

### 1. IPC & Low-Level Automation (`src.automation`)
- **IPC Bridge Client**: `src.automation.ipc_bridge.CPTIPCClient`
  - `add_device(device_name, device_model, x, y)`: Deploys router, switch, or PC chassis to canvas coordinates.
  - `add_link(dev1_name, dev1_port, dev2_name, dev2_port, cable_type)`: Wires devices together with specified cable type.
  - `configure_pc_ip(device_name, ip_address, subnet_mask, default_gateway)`: Sets static IP parameters on end hosts.
  - `configure_ios_device(device_name, commands)`: Injects and executes Cisco IOS command lists directly.
  - `send_pdu(source_device, destination_device)`: Dispatches simulation ICMP ping PDUs.
  - `set_simulation_mode(to_sim_mode)` & `step_simulation(direction, steps)`: Controls simulation clock and state.
  - `clear_canvas()`: Programmatically wipes devices and links from canvas.
- **Window Management**: `src.automation.window_manager`
  - `find_cpt_window()`: Locates active Cisco Packet Tracer window handle.
  - `focus_and_maximize_cpt()`: Brings window to foreground when UI inspection is required.
- **Simulation Time Controls**: `src.automation.simulation_manager`
  - `fast_forward_time(clicks)`: Dispatches `Alt+D` to accelerate Spanning Tree Protocol (STP) convergence.
  - `switch_to_realtime_mode()`: Dispatches `Alt+R`.
  - `switch_to_simulation_mode()`: Dispatches `Alt+S`.
- **Pre-flight Diagnostics**: `src.automation.preflight_check`
  - `check_python_dependencies()`: Verifies Python runtime packages.
  - `check_ipc_port()`: Probes port 7531 for active bridge listener.
  - `check_window_status()`: Verifies Packet Tracer window state.
  - `check_schemas_and_topologies()`: Verifies JSON schemas and recipe files.

### 2. Core Recipe Orchestration (`src.core`)
- **Recipe Engine**: `src.core.recipe_runner`
  - `load_recipe(path)`: Loads and strictly validates declarative YAML recipes against `schemas/recipe_schema.json`.
  - `execute_recipe(recipe, dry_run=False)`: Orchestrates multi-stage topology synthesis:
    - Stage 1: Window & Canvas initialization
    - Stage 2: Programmatic device deployment
    - Stage 3: Programmatic cabling & interface assignment
    - Stage 4: Protocol convergence acceleration
    - Stage 5: Node configuration (IOS & PC IP)
    - Stage 6: Deterministic ICMP PDU reachability verification
- **Proof & Evidence Collector**: `src.core.proof_collector`
  - `init_project_workspace(name)`: Generates project folders in `projects/`.
  - `generate_proof_report(...)`: Generates comprehensive markdown proof logs with verification outcomes.
- **Topology Synthesis Engine**: `src.core.topology_generator`
  - `generate_star_topology(...)`: Algorithmically generates star topologies with switch hubs.
  - `generate_vlan_topology(...)`: Generates multi-VLAN campus topologies with subnets.

### 3. Agent UI (`src.ui`)
- **Interactive Agent Terminal**: `src.ui.agent_cli`
  - `run_interactive_agent()`: Rich-powered terminal with clipboard detection, preset selection, and Antigravity workflow mode.
  - `scan_topologies_catalog()`: Live recipe catalog scanner with `[U]` / `[R]` refresh hotkey.

### 4. AI & MCP Integration (`src.ai`)
- **Model Context Protocol (MCP)**: `src.ai.mcp_server`
  - Exposes tools (`deploy_device`, `connect_devices`, `execute_ios_commands`, `configure_pc_ip`) to external AI coding agents (Antigravity, Claude Code).
- **LLM Client**: `src.ai.llm_client`
  - Synthesizes YAML recipes directly from free-form natural language assignment prompts.

## Example Workflows

### 1. Declarative Recipe Execution via Python
```python
from src.core.recipe_runner import load_recipe, execute_recipe

recipe = load_recipe("topologies/psikomotorik_master.yaml")
report = execute_recipe(recipe, dry_run=False)

print(f"Deployed {len(report['deployed_devices'])} devices.")
for result in report["verification_results"]:
    print(f"Ping {result['source']} -> {result.get('target')}: {result['status']}")
```

### 2. Programmatic IPC Bridge Usage
```python
from src.automation.ipc_bridge import CPTIPCClient

client = CPTIPCClient(host="127.0.0.1", port=7531)
if client.start_bridge(timeout=10.0):
    # Deploy devices
    client.add_device("R1", "router_2911", 300, 200)
    client.add_device("PC1", "pc", 600, 200)

    # Wire crossover cable
    client.add_link("R1", "GigabitEthernet0/0", "PC1", "FastEthernet0", cable_type="cross")

    # Configure PC IP
    client.configure_pc_ip("PC1", "192.168.1.10", "255.255.255.0", default_gateway="192.168.1.1")

    # Configure Router IOS
    client.configure_ios_device("R1", [
        "enable",
        "configure terminal",
        "interface GigabitEthernet0/0",
        "ip address 192.168.1.1 255.255.255.0",
        "no shutdown",
        "end"
    ])

    # Test reachability
    res = client.send_pdu("PC1", "R1")
    print("PDU Result:", res)

    client.stop_bridge()
```
