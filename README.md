# NetGent

<p align="center">
  <b>Because dragging virtual Ethernet cables at 3 AM is a form of digital torture that the Geneva Convention forgot to ban.</b>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg" alt="Python Version"></a>
  <a href="tests/"><img src="https://img.shields.io/badge/Tests-Passing%20(100%25%20Green)-success.svg" alt="Tests Status"></a>
  <a href="https://github.com/zidanaetrna/netgent"><img src="https://img.shields.io/badge/Vibe-Claude%20Code%20x%20Antigravity-purple.svg" alt="Agent Vibe"></a>
  <a href="https://github.com/zidanaetrna/netgent"><img src="https://img.shields.io/badge/Engine-Pure%20IPC%20Socket-orange.svg" alt="Pure IPC Socket"></a>
  <a href="https://github.com/zidanaetrna/netgent"><img src="https://img.shields.io/badge/Dragging%20Cables%20Manually-0%25-red.svg" alt="No Manual Dragging"></a>
</p>

---

## Why Does This Exist?

Let's be completely honest with each other for five seconds:

Have you ever sat in front of **Cisco Packet Tracer**, squinting at 24 tiny switch ports on a 1080p screen, trying to connect `FastEthernet0/14` to a PC, only to accidentally click the `RS-232 Console` port and hate your life?

Have you ever forgotten to type `no shutdown` on an interface, stared at a blinking red triangle for 45 minutes, questioned your career choices in computer science, and wondered if farming alpacas in New Zealand was still a viable life plan?

Have you ever had a professor or lab instructor demand a **10-Router Full Mesh topology** ($L = \frac{10 \times 9}{2} = 45\text{ links}$), forcing you to drag **45 individual crossover cables** like a medieval digital peasant?

**NetGent solves this.**

NetGent is an autonomous AI network engineering agent that takes declarative YAML recipes and talks directly to Cisco Packet Tracer via an Inter-Process Communication (IPC) Socket bridge. It drops routers, switches, and PCs onto the canvas, wires them up, applies full IOS configs, fast-forwards Spanning Tree Protocol convergence, and verifies end-to-end ping reachability—**all while you sit back, sip iced coffee, and look like a high-tech wizard.**

---

## Philosophy & Code Standards

> *"Look, we're not building software for a Swiss central bank or landing autonomous rovers on Mars. But let's not write absolute shit code either."*  
> — **[zidanaetrna](https://github.com/zidanaetrna)**

We believe in three simple truths:
1. **Clean Modular Architecture**: Clean code over clever code. 4 distinct layers (`core`, `automation`, `ui`, `ai`), single-responsibility functions, and descriptive names.
2. **Zero Mouse Hijacking**: We communicate with Packet Tracer via a pure WebSockets / Socket.IO IPC bridge (`127.0.0.1:7531`). We don't hijack your mouse cursor like a rogue malware from 2004. Your cursor stays yours so you can scroll Twitter or shitpost while your network builds itself.
3. **Headless & Asset-Free**: No brittle OpenCV pixel template matching. No screen resolution scaling issues. Zero GBs of loose PNG crops. Direct, deterministic JSON-RPC IPC calls to Packet Tracer's internal engine.
4. **No Bullshit Verification**: When NetGent says a ping succeeded, it verified the actual ICMP PDU response from the simulation engine. No fake green checkmarks.

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
        │             (src/core/recipe_runner.py)                │
        └───────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
        ┌────────────────────────────────────────────────────────┐
        │            Deterministic IPC Socket Bridge             │
        │            (src/automation/ipc_bridge.py)              │
        │            Port 7531 (JSON-RPC over Socket.IO)         │
        └───────────────────────────┬────────────────────────────┘
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
- **Antigravity Interactive Mode**:
  Built-in guidance for pairing with **Google Antigravity** or Claude Code. Generate your YAML topology recipes, hit `[U]` / `[R]` in the live catalog refresh scanner, and watch your freshly generated topology execute immediately.
- **Pure IPC Engine (`127.0.0.1:7531`)**:
  Speaks directly to Packet Tracer's internal JavaScript engine via `extensions/cisco-pt-mcp.pts`. Sub-second deployments, zero mouse cursor locks, and zero fragile image template matches.
- **Enterprise-Grade Pre-Built Topologies**:
  - **Tugas Psikomotorik 3 Master**: 5 topologies in 1 single canvas (Bus, Star, Ring, Mesh, Hybrid) cleanly separated into distinct zones with numbered labels (`NO1-`, `NO2-`, etc.) so you know exactly what to screenshot for your lecturer.
  - **10-Router OSPF Partial Mesh**: A 14-link high-availability WAN backbone demonstrating why Full Mesh is expensive and Partial Mesh is smart.
  - **Universitas Integratif**: 4 buildings, 10 labs, dual Layer-3 3560 core switches, server farm, and Rapid-PVST+.
  - **NEXORA Technologies**: 3-tier enterprise campus with 9 VLANs and server clustering.
  - **Classic CCNA Labs**: Praktikum 2 (LAN Switch), Praktikum 3 (Two Networks Router), Simulasi 2 (Lab Informatika).
- **Automated Time-Travel**:
  Automatically fast-forwards simulation pulses (`Alt+D`) so you don't have to sit there staring at Spanning Tree's orange port dots while waiting 50 seconds for listening/learning states.

---

## Installation

### Prerequisites
- **OS**: Windows 10 or 11 (64-bit)
- **Python**: 3.10, 3.11, 3.12, or 3.13
- **Cisco Packet Tracer**: Version 8.0, 8.1, 8.2, or 8.3+

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

### 3. Load Cisco Packet Tracer IPC Extension
1. Open **Cisco Packet Tracer**.
2. Navigate to **Extensions** -> **Scripting** -> **Script Manager**.
3. Add and run `extensions/cisco-pt-mcp.pts` (or `extensions/Builder.pts`).
4. NetGent will automatically connect to `127.0.0.1:7531`.

---

## Usage

### 1. Interactive Agent Mode (Recommended)
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
- Select `[1-7]` to run built-in lab presets.
- Select `[A]` to launch **Antigravity Mode** with live catalog file watching.
- Select `[C]` to smart-paste an assignment from your clipboard.
- Select `[D]` to run non-destructive dry-runs.
- Press `[U]` or `[R]` anywhere in the recipe catalog to refresh newly added YAML files.

### 2. Direct Recipe Execution (Speedrun Mode)
Deploy pre-built declarative topologies directly to Packet Tracer:

```bash
# Deploy all 5 psychomotor topologies (Bus, Star, Ring, Mesh, Hybrid) at once:
python src/main.py --recipe topologies/psikomotorik_master.yaml

# Deploy 10-Router OSPF Partial Mesh:
python src/main.py --recipe topologies/partial_mesh_10routers.yaml

# Deploy Campus Enterprise Network:
python src/main.py --recipe topologies/universitas_integratif.yaml
```

### 3. Dry-Run Mode ("Check My Math First")
Want to verify that your recipe coordinates, subnets, and port names aren't hallucinated before touching Packet Tracer?
```bash
python src/main.py --recipe topologies/psikomotorik_master.yaml --dry-run
```

### 4. Diagnostics & Pre-flight Sanity Check
Verify Python dependencies, CPT process detection, IPC socket connectivity, and schema integrity:
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
├── extensions/             # Cisco Packet Tracer PTS IPC extensions (cisco-pt-mcp.pts, Builder.pts)
├── projects/               # Generated lab proof reports and evidence
├── schemas/                # JSON schemas for recipes and skills
├── src/                    # Clean 4-layer modular architecture
│   ├── ai/                 # LLM client & Model Context Protocol (MCP) server
│   │   ├── llm_client.py
│   │   └── mcp_server.py
│   ├── automation/         # Packet Tracer IPC socket client & automation drivers
│   │   ├── ipc_bridge.py
│   │   ├── window_manager.py
│   │   ├── topology_builder.py
│   │   ├── cli_manager.py
│   │   ├── pc_manager.py
│   │   ├── simulation_manager.py
│   │   └── preflight_check.py
│   ├── core/               # Configuration, models, and recipe orchestration
│   │   ├── config.py
│   │   ├── presets.py
│   │   ├── primitives.py
│   │   ├── recipe_runner.py
│   │   ├── proof_collector.py
│   │   └── topology_generator.py
│   ├── ui/                 # Interactive Claude Code / Antigravity terminal CLI
│   │   └── agent_cli.py
│   ├── __init__.py
│   └── main.py             # Unified CLI entry point
├── tests/                  # Comprehensive unittest suite (100% passing)
├── topologies/             # Ready-to-run declarative YAML topologies
├── requirements.txt        # Runtime dependencies
├── pyproject.toml          # PEP 517 package configuration & pyright setup
├── pyrightconfig.json      # IDE language server configuration
├── LICENSE                 # MIT License (zidanaetrna)
├── CONTRIBUTING.md         # Developer contribution guidelines
└── README.md               # Project documentation
```

---

## Testing

NetGent comes with an extensive unit test suite covering coordinate mappers, recipe validators, IPC event loops, simulation timers, and CLI managers:

```bash
python -m unittest discover tests
```

Output:
```text
Ran 68 tests in 20.151s

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
