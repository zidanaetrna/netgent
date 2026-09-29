# NetGent

<p align="center">
  <b>Because dragging virtual Ethernet cables at 3 AM is a form of digital torture that the Geneva Convention forgot to ban.</b>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg" alt="Python Version"></a>
  <a href="tests/"><img src="https://img.shields.io/badge/Tests-80%20Passed%20(Zero%20Flakes)-success.svg" alt="Tests Status"></a>
  <a href="https://github.com/zidanaetrna/netgent"><img src="https://img.shields.io/badge/Vibe-Claude%20Code%20x%20Antigravity-purple.svg" alt="Agent Vibe"></a>
  <a href="https://github.com/zidanaetrna/netgent"><img src="https://img.shields.io/badge/Dragging%20Cables%20Manually-0%25-red.svg" alt="No Manual Dragging"></a>
</p>

---

## Why Does This Exist?

Let's be completely honest with each other for five seconds:

Have you ever sat in front of **Cisco Packet Tracer**, squinting at 24 tiny switch ports on a 1080p screen, trying to connect `FastEthernet0/14` to a PC, only to accidentally click the `RS-232 Console` port and hate your life?

Have you ever forgotten to type `no shutdown` on an interface, stared at a blinking red triangle for 45 minutes, questioned your career choices in computer science, and wondered if farming alpacas in New Zealand was still a viable life plan?

Have you ever had a professor or lab instructor demand a **10-Router Full Mesh topology** ($L = \frac{10 \times 9}{2} = 45\text{ links}$), forcing you to drag **45 individual crossover cables** like a medieval digital peasant?

**NetGent solves this.**

NetGent is an autonomous AI network engineering agent that takes declarative YAML recipes and talks directly to Cisco Packet Tracer. It drops routers, switches, and PCs onto the canvas, wires them up, types the IOS commands, kicks Spanning Tree to fast-forward time, and verifies ping reachability—**all while you sit back, sip iced coffee, and look like a high-tech sorcerer.**

---

## Philosophy & Code Standards

> *"Look, we're not building software for a Swiss central bank or landing autonomous rovers on Mars. But let's not write absolute shit code either."*  
> — **zidanaetrna**

We believe in three simple truths:
1. **Clean Code Still Matters**: Functions have one job, variable names explain themselves, and we don't commit spaghetti monsters into `git`.
2. **Zero Mouse Hijacking**: We communicate with Packet Tracer via a pure WebSockets / Socket.IO IPC bridge. We don't hijack your mouse cursor like a rogue malware from 2004. Your mouse stays yours so you can scroll Twitter or shitpost while your network builds itself.
3. **No Bullshit Automation**: When NetGent says a ping succeeded, it verified the ICMP PDU response from the simulation engine. No fake green checkmarks.

---

## Architecture: How The Black Magic Works

```
        ┌────────────────────────────────────────────────────────┐
        │        Declarative YAML Recipe (.yaml)                 │
        │  "Put 4 Routers, make them Full Mesh, run OSPF, ping"  │
        └───────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
        ┌────────────────────────────────────────────────────────┐
        │             NetGent Core Orchestrator                  │
        │           (src/recipe_runner.py & CLI)                 │
        └───────────────────────────┬────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
       [Primary: IPC Socket.IO]          [Fallback: OpenCV Vision]
       Talks JSON-RPC to PT JS Engine    Multi-scale template matching
       (Speed: Instant, 0 mouse moves)   (When IPC extension isn't loaded)
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │               Cisco Packet Tracer Canvas                │
       │                                                         │
       │   [R1] ══════════════ [R2]      - Chassis Deployed      │
       │     ║ ╲             ╱  ║        - Interfaces Wired      │
       │     ║   ╲         ╱    ║        - IOS Config Applied    │
       │     ║     ╲     ╱      ║        - OSPF / VLAN Converged │
       │     ║       ╲ ╱        ║        - PDU Verified (PASS)   │
       │   [R4] ══════════════ [R3]                              │
       └─────────────────────────────────────────────────────────┘
```

---

## Key Features

- **Claude Code-Inspired Terminal UI**:
  A gorgeous interactive CLI built with `rich`. Live status spinners, syntax panels, preset selection, and smart clipboard pasting (it literally detects when you copied a networking assignment from your browser).
- **Dual Execution Engines**:
  - **IPC Engine (`--engine ipc`)**: Speaks directly to Packet Tracer's internal JavaScript engine. Sub-second deployments with zero screen clicks.
  - **Vision Engine (`--engine gui`)**: OpenCV template matching fallback that can find buttons and ports visually if you don't have the IPC plugin installed.
- **Enterprise-Grade Pre-Built Topologies**:
  - **Tugas Psikomotorik 3 Master**: 5 topologies in 1 single canvas (Bus, Star, Ring, Mesh, Hybrid) cleanly separated into distinct zones with numbered labels (`NO1-`, `NO2-`, etc.) so you know exactly what to screenshot for your lecturer.
  - **10-Router OSPF Partial Mesh**: A 14-link high-availability WAN backbone demonstrating why Full Mesh is expensive and Partial Mesh is smart.
  - **Universitas Integratif**: 4 buildings, 10 labs, dual Layer-3 3560 core switches, server farm, and Rapid-PVST+.
  - **NEXORA Technologies**: 3-tier enterprise campus with 9 VLANs and server clustering.
  - **Classic CCNA Labs**: Praktikum 2 (LAN Switch), Praktikum 3 (Two Networks Router), Simulasi 2 (Lab Informatika).
- **Automated Time-Travel**:
  Automatically triggers fast-forward simulation pulses (`Alt+D`) so you don't have to sit there staring at Spanning Tree's orange port dots while waiting 50 seconds for listening/learning states.

---

## Installation

### Prerequisites
- **OS**: Windows 10 or 11 (64-bit)
- **Python**: 3.10, 3.11, or 3.12
- **Cisco Packet Tracer**: Version 8.0, 8.1, or 8.2+

### 1. Clone & Setup Virtualenv
```bash
git clone https://github.com/zidanaetrna/netgent.git
cd netgent

python -m venv .venv
.venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
pip install -e .
```

### 3. Connect Packet Tracer IPC Bridge
1. Open **Cisco Packet Tracer**.
2. Navigate to **Extensions** -> **Scripting** -> **Script Manager**.
3. Load `extensions/pt_ipc_bridge.js` (or run NetGent and let it communicate on port `7531`).

---

## Usage

### 1. The "I Just Want To Talk To It" Mode (Interactive CLI)
Just run `python src/main.py` without arguments:
```bash
python src/main.py
```
You will be greeted by the interactive agent terminal:
```text
╭──────────────────────────────────────────────────────────────────────────╮
│                                                                          │
│  >> NETGENT AUTONOMOUS AI NETWORK AGENT                                  │
│  Cisco Packet Tracer Architecture Synthesis & Proof Verification Engine  │
│  Inspired by Claude Code & Antigravity Agent                             │
│                                                                          │
╰──────────────────────────────────────────────────────────────────────────╯
```
Choose a preset (1 through 7) or press `C` to smart-paste a custom assignment from your clipboard!

### 2. Direct Recipe Execution (Speedrun Mode)
Deploy pre-built declarative topologies directly to Packet Tracer:

```bash
# Deploy all 5 psychomotor topologies (Bus, Star, Ring, Mesh, Hybrid) at once:
python src/main.py --recipe topologies/psikomotorik_master.yaml --engine ipc

# Deploy 10-Router OSPF Partial Mesh:
python src/main.py --recipe topologies/partial_mesh_10routers.yaml --engine ipc

# Deploy Campus Enterprise Network:
python src/main.py --recipe topologies/universitas_integratif.yaml --engine ipc
```

### 3. "Check My Work First" (Dry Run Mode)
Want to verify that your recipe coordinates and port names aren't hallucinated before touching Packet Tracer?
```bash
python src/main.py --recipe topologies/psikomotorik_master.yaml --dry-run
```

### 4. Diagnostics & Sanity Check
Test screen resolution, template matching confidence, and Packet Tracer window detection:
```bash
python src/main.py --preflight
```

---

## Declarative Recipe Anatomy

Writing a network in NetGent is as simple as writing a grocery list:

```yaml
name: "Two Routers Talking OSPF"
description: "Because static routing in 2026 is embarrassing"

devices:
  - id: "R1"
    type: "router_2911"
    position: { x: 0.35, y: 0.50 }

  - id: "R2"
    type: "router_2911"
    position: { x: 0.65, y: 0.50 }

connections:
  - from: "R1"
    to: "R2"
    cable_type: "copper_cross_over"
    from_port: "GigabitEthernet0/0"
    to_port: "GigabitEthernet0/0"

configurations:
  R1:
    type: "ios"
    commands:
      - "no"
      - "enable"
      - "configure terminal"
      - "interface GigabitEthernet0/0"
      - "ip address 10.0.0.1 255.255.255.252"
      - "no shutdown"
      - "exit"
      - "router ospf 1"
      - "network 10.0.0.0 0.0.0.3 area 0"
      - "end"

  R2:
    type: "ios"
    commands:
      - "no"
      - "enable"
      - "configure terminal"
      - "interface GigabitEthernet0/0"
      - "ip address 10.0.0.2 255.255.255.252"
      - "no shutdown"
      - "exit"
      - "router ospf 1"
      - "network 10.0.0.0 0.0.0.3 area 0"
      - "end"

verifications:
  - source: "R1"
    target_ip: "10.0.0.2"
    ping_count: 4
```

---

## Directory Structure

```text
netgent/
├── assets/                 # Reference images and CV templates
├── docs/                   # Additional documentation and guides
├── extensions/             # Cisco Packet Tracer JS IPC extensions
├── projects/               # Generated lab proof reports and evidence
├── schemas/                # JSON schemas for recipes and skills
├── src/                    # Core NetGent modular source code
│   ├── ai/                 # LLM client & Model Context Protocol (MCP) server
│   │   ├── llm_client.py
│   │   └── mcp_server.py
│   ├── automation/         # Low-level Packet Tracer IPC & vision drivers
│   │   ├── ipc_bridge.py
│   │   ├── window_manager.py
│   │   ├── topology_builder.py
│   │   ├── cli_manager.py
│   │   ├── pc_manager.py
│   │   ├── simulation_manager.py
│   │   ├── calibrate_assets.py
│   │   └── preflight_check.py
│   ├── core/               # Configuration, models, and recipe orchestration
│   │   ├── config.py
│   │   ├── primitives.py
│   │   ├── recipe_runner.py
│   │   ├── proof_collector.py
│   │   └── topology_generator.py
│   ├── ui/                 # Interactive Claude Code-style CLI & desktop GUI
│   │   ├── agent_cli.py
│   │   ├── agent_gui.py
│   │   └── web_server.py
│   ├── __init__.py
│   └── main.py             # Unified CLI entry point
├── tests/                  # Comprehensive unittest suite (80 passed)
├── topologies/             # Ready-to-run declarative YAML topologies
├── requirements.txt        # Runtime dependencies
├── pyproject.toml          # PEP 517 package configuration
├── LICENSE                 # MIT License (zidanaetrna)
└── README.md               # Project documentation
```

---

## Testing

NetGent comes with **80 unit tests** covering coordinate mappers, recipe validators, IPC event loops, simulation timers, and CLI managers:

```bash
python -m unittest discover tests
```

Output:
```text
Ran 80 tests in 28.626s

OK
```
Zero skipped tests. Zero flaky tests. Zero drama.

---

## Contributing

Found a bug? Want to add support for Cisco ASA Firewalls or Access Points? Want to submit a new killer topology?

Check out [CONTRIBUTING.md](CONTRIBUTING.md). Pull requests are very welcome!

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.  
You are free to use it, learn from it, fork it, and pass your networking practical exams with it.

---

## Author

Crafted with caffeine, frustration at repetitive manual clicks, and a love for clean code by **[zidanaetrna](https://github.com/zidanaetrna)**.

*Special shoutout to the Google DeepMind Antigravity and Claude Code teams for inspiring the agent architecture.*
