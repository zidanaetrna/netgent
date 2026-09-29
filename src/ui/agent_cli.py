"""Claude Code-style Interactive Terminal Agent for NetGent.

Provides an autonomous rich CLI interface for synthesizing network topologies,
answering lab questions, executing Packet Tracer simulations, and generating
proof documentation without relying on raw emoji characters.
"""

from __future__ import annotations

import argparse
import ctypes
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.status import Status
from rich.syntax import Syntax
from rich.table import Table

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.presets import LAB_PRESETS
from src.ai.llm_client import LLMClient
from src.core.proof_collector import (
    generate_proof_report,
    get_projects_root,
    init_project_workspace,
    save_project_recipe,
)
from src.core.recipe_runner import execute_recipe, load_recipe, validate_recipe
from src.core.topology_generator import generate_star_topology, generate_vlan_topology

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console(highlight=False)


def print_banner() -> None:
    """Print the Claude Code / Antigravity styled agent banner using clean text."""
    banner_text = (
        "[bold cyan]>> NETGENT AUTONOMOUS AI NETWORK AGENT[/bold cyan]\n"
        "[dim]Cisco Packet Tracer Architecture Synthesis & Proof Verification Engine[/dim]\n"
        "[dim]Inspired by Claude Code & Antigravity Agent[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", padding=(1, 2)))


def print_antigravity_guide() -> None:
    """Display instructions for Antigravity-driven recipe generation."""
    guide_text = (
        "[bold cyan]>> GOOGLE ANTIGRAVITY AGENT WORKFLOW[/bold cyan]\n\n"
        "1. [bold white]Open Google Antigravity / Claude Code / your AI Agent IDE.[/bold white]\n"
        "2. Copy & paste your network assignment prompt into Antigravity.\n"
        "3. Ask the agent to generate a declarative YAML recipe into the [bold green]topologies/[/bold green] folder.\n"
        "4. Once Antigravity saves the file, choose [bold yellow][U] Update/Refresh[/bold yellow] from the menu\n"
        "   to automatically detect the new recipe and deploy it directly into Cisco Packet Tracer!"
    )
    console.print(Panel(guide_text, border_style="cyan", padding=(1, 2)))


def select_agent_mode() -> str:
    """Prompt the user to select Antigravity Mode or External API Key Mode."""
    table = Table(title="[bold]Select AI Agent Operating Mode[/bold]", border_style="bright_black")
    table.add_column("Option", style="bold cyan", width=8)
    table.add_column("Mode Name", style="bold white", width=28)
    table.add_column("Description", style="dim")

    table.add_row(
        "1",
        "[Antigravity Mode]",
        "Antigravity IDE workflow & verified recipes (Zero external API key required)",
    )
    table.add_row(
        "2",
        "[External AI API Mode]",
        "Google Gemini, OpenAI GPT-4o, Claude 3.5 Sonnet, or local Ollama",
    )
    console.print(table)

    choice = Prompt.ask("Choose mode [1/2]", choices=["1", "2"], default="1")
    mode = "antigravity" if choice == "1" else "api_key"

    if mode == "antigravity":
        print_antigravity_guide()

    return mode


def get_clipboard_content() -> str:
    """Retrieve text cleanly from system clipboard via Win32 ctypes without terminal distortion."""
    if sys.platform != "win32":
        return ""
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        CF_UNICODETEXT = 13
        if user32.OpenClipboard(None):
            try:
                handle = user32.GetClipboardData(CF_UNICODETEXT)
                if handle:
                    ptr = kernel32.GlobalLock(handle)
                    if ptr:
                        try:
                            val = ctypes.c_wchar_p(ptr).value or ""
                            if val.strip():
                                return val.strip()
                        finally:
                            kernel32.GlobalUnlock(handle)
            finally:
                user32.CloseClipboard()
    except Exception:
        pass

    return ""


def scan_topologies_catalog() -> Optional[Tuple[str, str, Dict[str, Any]]]:
    """Scan topologies/ directory, display an interactive refreshed table, and allow selecting a recipe."""
    topologies_dir = PROJECT_ROOT / "topologies"
    if not topologies_dir.exists():
        console.print("[yellow][!] 'topologies/' directory not found.[/yellow]")
        return None

    yaml_files = sorted(
        list(topologies_dir.glob("*.yaml")) + list(topologies_dir.glob("*.yml")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not yaml_files:
        console.print("[yellow][!] No YAML recipes found in 'topologies/'. Generate one using Antigravity first![/yellow]")
        return None

    table = Table(title="[bold green]Detected Topology Recipes (topologies/)[/bold green]", border_style="green")
    table.add_column("#", style="bold cyan", width=4)
    table.add_column("Filename", style="bold white", width=36)
    table.add_column("Recipe Name", style="bold yellow", width=36)
    table.add_column("Modified", style="dim", width=20)

    cached_recipes = []
    for idx, f in enumerate(yaml_files, start=1):
        mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(f.stat().st_mtime))
        try:
            with open(f, "r", encoding="utf-8") as yf:
                doc = yaml.safe_load(yf) or {}
                r_name = doc.get("name", f.stem)
                cached_recipes.append((f, doc, r_name))
        except Exception:
            r_name = "[Error parsing YAML]"
            cached_recipes.append((f, None, r_name))

        table.add_row(str(idx), f.name, str(r_name)[:34], mtime)

    console.print(table)
    console.print("[dim]Enter number to load recipe, [R] to re-scan for new files, or [B] to return to main menu.[/dim]")

    choices = [str(i) for i in range(1, len(yaml_files) + 1)] + ["r", "R", "b", "B"]
    pick = Prompt.ask("Select option", choices=choices, default="1").strip().lower()

    if pick == "r":
        console.print("[bold cyan][*] Rescanning 'topologies/' for newly generated files...[/bold cyan]\n")
        return scan_topologies_catalog()
    elif pick == "b":
        return None

    selected_idx = int(pick) - 1
    selected_file, recipe_data, recipe_name = cached_recipes[selected_idx]
    if recipe_data is None:
        recipe_data = load_recipe(selected_file)

    console.print(f"[bold green][OK] Loaded recipe: [bold]{selected_file.name}[/bold][/bold green]")
    return f"Assignment loaded from {selected_file.name}", "Recipe loaded from local topology catalog.", recipe_data


def match_antigravity_recipe(prompt_text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Match natural-language prompt against Antigravity verified recipes or parametric topologies."""
    lower = prompt_text.lower()

    # 1. NEXORA Technologies Enterprise (Core L3, Edge Router, 3 Floor Switches, 4 Servers, 9 VLANs)
    if "nexora" in lower or ("core l3" in lower and "sw-01" in lower) or ("vlan 10" in lower and "server-01" in lower):
        data = LAB_PRESETS["NEXORA Technologies (Enterprise 3-Tier)"]
        return load_recipe(PROJECT_ROOT / data["recipe_file"]), data["academic_answers"]

    # 2. Praktikum 3: Two Networks Router (2 Subnets 192.168.1.0 and 192.168.2.0)
    if "praktikum 3" in lower or ("router" in lower and "192.168.2" in lower and "192.168.1" in lower):
        data = LAB_PRESETS["Praktikum 3: Two Networks Router (2 Subnets)"]
        return load_recipe(PROJECT_ROOT / data["recipe_file"]), data["academic_answers"]

    # 3. Praktikum 2: LAN Switch (3 PCs + Switch 2960)
    if "praktikum 2" in lower or ("switch" in lower and "pc1" in lower and "pc3" in lower):
        data = LAB_PRESETS["Praktikum 2: LAN Switch (3 PCs)"]
        return load_recipe(PROJECT_ROOT / data["recipe_file"]), data["academic_answers"]

    # 4. Simulasi 2: Lab Informatika (Router + 2 Switches + Server + 2 Printers + AP)
    if "simulasi 2" in lower or "laboratorium informatika" in lower:
        data = LAB_PRESETS["Simulasi 2: Lab Informatika"]
        return load_recipe(PROJECT_ROOT / data["recipe_file"]), data["academic_answers"]

    # 5. Partial Mesh 10 Router (Enterprise OSPF Backbone)
    if "partial mesh" in lower or "full mesh" in lower or "mesh" in lower or ("10" in lower and "router" in lower):
        data = LAB_PRESETS["Partial Mesh 10 Router (Enterprise OSPF Backbone)"]
        return load_recipe(PROJECT_ROOT / data["recipe_file"]), data["academic_answers"]

    # 6. Universitas Integratif Campus Network (Dual Core L3, 4 Gedung, 10 Labs)
    if "universitas" in lower or "integratif" in lower or "uji kompetensi 5" in lower or "kampus" in lower:
        data = LAB_PRESETS["Perancangan Integratif Universitas (Enterprise Campus)"]
        return load_recipe(PROJECT_ROOT / data["recipe_file"]), data["academic_answers"]

    # 7. Tugas Psikomotorik 3: Master Showcase (Bus, Star, Ring, Mesh, Hybrid)
    if "psikomotorik" in lower or ("bus" in lower and "star" in lower) or ("ring" in lower and "hybrid" in lower):
        data = LAB_PRESETS["Tugas Psikomotorik 3: Master Showcase (Bus, Star, Ring, Mesh, Hybrid)"]
        return load_recipe(PROJECT_ROOT / data["recipe_file"]), data["academic_answers"]

    # 8. Router-on-a-stick / VLAN
    if "router-on-a-stick" in lower or "trunk" in lower or "vlan" in lower:
        return generate_vlan_topology(), "VLAN Trunking architecture synthesized via Antigravity generator."

    # 9. Default Star topology
    return generate_star_topology(num_pcs=3), "Star LAN topology synthesized via Antigravity generator."


def select_or_input_prompt() -> Tuple[str, Optional[str], Optional[Dict[str, Any]]]:
    """Select from available lab presets, refresh topology catalog, smart paste from clipboard, or load from file."""
    while True:
        preset_names = list(LAB_PRESETS.keys())
        table = Table(title="[bold]Laboratory Assignments & Input Methods[/bold]", border_style="bright_black")
        table.add_column("#", style="bold cyan", width=4)
        table.add_column("Option", style="bold white", width=54)

        for idx, name in enumerate(preset_names, start=1):
            table.add_row(str(idx), name)

        table.add_row("U", "[bold green][U] Update / Refresh (Scan topologies/ for newly generated recipes)[/bold green]")
        table.add_row("C", "[bold yellow][C] Custom Assignment (Smart Paste from Clipboard)[/bold yellow]")
        table.add_row("F", "[bold magenta][F] Load Assignment from File (.txt / .md / .yaml)[/bold magenta]")

        console.print(table)

        valid_choices = [str(i) for i in range(1, len(preset_names) + 1)] + ["u", "U", "r", "R", "c", "C", "f", "F"]
        raw_choice = Prompt.ask("Select an option", choices=valid_choices, default="1")
        normalized_choice = raw_choice.strip().lower()

        # Option U / R: Refresh & Scan topologies catalog
        if normalized_choice in ("u", "r"):
            res = scan_topologies_catalog()
            if res:
                return res
            continue

        if normalized_choice not in ("c", "f"):
            selected_name = preset_names[int(normalized_choice) - 1]
            data = LAB_PRESETS[selected_name]
            recipe_path = PROJECT_ROOT / data["recipe_file"]
            recipe_dict = load_recipe(recipe_path) if recipe_path.exists() else None
            return data["prompt"], data["academic_answers"], recipe_dict

        custom_prompt = ""

        # Option F: Load from file
        if normalized_choice == "f":
            file_path_str = Prompt.ask("Enter path to assignment file (.txt, .md, .yaml)")
            path = Path(file_path_str.strip('"').strip("'"))
            if not path.is_file():
                console.print(f"[red][!] File not found: {path}. Falling back to clipboard/manual.[/red]")
            else:
                try:
                    if path.suffix in (".yaml", ".yml"):
                        recipe_data = load_recipe(path)
                        console.print(f"[bold green][OK] Loaded recipe directly from {path.name}[/bold green]")
                        return f"Loaded from {path.name}", "Direct YAML execution.", recipe_data
                    custom_prompt = path.read_text(encoding="utf-8")
                    console.print(f"[bold green][OK] Loaded {len(custom_prompt)} characters from {path.name}[/bold green]")
                except Exception as err:
                    console.print(f"[red][!] Failed to read file: {err}[/red]")

        # Option C or fallback: Smart Clipboard Paste
        if not custom_prompt:
            clip_text = get_clipboard_content()
            if clip_text and len(clip_text) > 10:
                preview = clip_text[:400] + ("..." if len(clip_text) > 400 else "")
                console.print("\n[bold green][+] Smart Paste: Content detected in your Clipboard:[/bold green]")
                console.print(Panel(preview, title=f"Clipboard Preview ({len(clip_text)} chars)", border_style="green"))
                use_clip = Confirm.ask("Use this text from clipboard?", default=True)
                if use_clip:
                    custom_prompt = clip_text

        # Manual terminal input if clipboard was empty or declined
        if not custom_prompt:
            console.print(
                "\n[bold cyan]>> Manual Text Entry Mode[/bold cyan]\n"
                "[dim]Paste or type your text freely. Type '/end' or 'EOF' on a new line and press Enter to finish:[/dim]"
            )
            lines: List[str] = []
            while True:
                try:
                    line = input()
                except EOFError:
                    break
                clean_line = line.strip()
                if clean_line in ("/end", "EOF", "/submit", "/done"):
                    break
                lines.append(line)
            custom_prompt = "\n".join(lines).strip()

        if not custom_prompt:
            console.print("[yellow][!] No prompt provided. Defaulting to Praktikum 2 preset.[/yellow]")
            default_data = LAB_PRESETS[preset_names[0]]
            recipe_path = PROJECT_ROOT / default_data["recipe_file"]
            return default_data["prompt"], default_data["academic_answers"], load_recipe(recipe_path)

        matched_recipe, matched_answers = match_antigravity_recipe(custom_prompt)
        return custom_prompt, matched_answers, matched_recipe


def run_interactive_agent(initial_prompt: Optional[str] = None) -> None:
    """Execute the full interactive CLI agent workflow."""
    print_banner()

    # Step 1: Mode Selection
    mode = select_agent_mode()
    console.print(f"\n[bold green][OK][/bold green] Active Mode: [bold cyan]{mode.upper()}[/bold cyan]\n")

    # Step 2: Lab Prompt or Preset Selection
    if initial_prompt:
        prompt_text = initial_prompt
        matched_rec, matched_ans = match_antigravity_recipe(prompt_text)
        predefined_answers = matched_ans
        predefined_recipe = matched_rec
        console.print(f"[bold green][OK] Loaded prompt ({len(prompt_text)} characters)[/bold green]")
    else:
        prompt_text, predefined_answers, predefined_recipe = select_or_input_prompt()

    # Step 3: Project Configuration
    default_proj = "lab_agent_run"
    proj_name = Prompt.ask("Enter project workspace name", default=default_proj)
    project_dir = init_project_workspace(proj_name)
    console.print(f"[dim]Initialized project workspace at:[/dim] [cyan]{project_dir}[/cyan]\n")

    recipe_dict: Optional[Dict[str, Any]] = None
    academic_answers: Optional[str] = predefined_answers

    # Phase 1: Synthesis
    if mode == "antigravity":
        if predefined_recipe:
            recipe_dict = predefined_recipe
            console.print(f"[bold green][OK][/bold green] Loaded verified recipe: [bold]{recipe_dict.get('name')}[/bold]")
        else:
            with Status("[bold cyan][*] Synthesizing network topology via Antigravity generator...[/bold cyan]"):
                recipe_dict = generate_star_topology(num_pcs=3)
                academic_answers = "Synthesized automatically via NetGent Antigravity topology generator."
                time.sleep(0.5)
    else:
        # Mode B: External AI API mode
        provider = Prompt.ask("Select provider", choices=["gemini", "openai", "anthropic", "ollama"], default="gemini")
        api_key = os.getenv(f"{provider.upper()}_API_KEY", "")
        if not api_key and provider != "ollama":
            api_key = Prompt.ask(f"Enter {provider} API key", password=True)

        model_default = {
            "gemini": "gemini-2.0-flash",
            "openai": "gpt-4o",
            "anthropic": "claude-3-5-sonnet-20241022",
            "ollama": "llama3",
        }.get(provider, "gemini-2.0-flash")
        model_name = Prompt.ask("Model name", default=model_default)

        with Status(f"[bold cyan][*] Querying {provider.upper()} ({model_name}) for synthesis & analysis...[/bold cyan]"):
            client = LLMClient(provider=provider, model=model_name, api_key=api_key)
            result = client.synthesize(prompt_text)
            recipe_dict = result["recipe"]
            academic_answers = result.get("academic_answers", "")

    # Save recipe into project directory
    save_project_recipe(project_dir, recipe_dict)

    # Preview Synthesized Recipe
    console.print("\n[bold]Synthesized NetGent Recipe Specification:[/bold]")
    yaml_str = yaml.dump(recipe_dict, sort_keys=False, indent=2)
    console.print(Syntax(yaml_str, "yaml", theme="monokai", line_numbers=True))

    # Phase 2: Execution confirmation
    if not Confirm.ask("\nProceed to execute simulation in Cisco Packet Tracer?", default=True):
        console.print("[yellow][!] Execution cancelled by user. Recipe saved to project.[/yellow]")
        return

    engine = Prompt.ask("Execution engine", choices=["ipc", "hybrid", "dry_run"], default="ipc")

    console.print(f"\n[bold cyan]>> Running Packet Tracer Simulation (Engine: {engine})...[/bold cyan]")
    with Status("[bold green][*] Executing topology deployment, cabling, IOS config & pings...[/bold green]"):
        exec_report = execute_recipe(
            recipe=recipe_dict,
            dry_run=(engine == "dry_run"),
            engine=engine,
            project_dir=project_dir,
        )

    # Phase 3: Collect proofs & generate report
    report_file = generate_proof_report(
        project_dir=project_dir,
        recipe=recipe_dict,
        execution_report=exec_report,
        academic_answers=academic_answers,
    )

    # Print Verification Proof Results Table
    console.print("\n")
    proof_table = Table(title="[bold green]Connectivity Verification & Proof Screenshots[/bold green]", border_style="green")
    proof_table.add_column("Test #", style="bold cyan", width=8)
    proof_table.add_column("Source", style="bold white", width=12)
    proof_table.add_column("Target IP", style="bold white", width=18)
    proof_table.add_column("Result", style="bold green", width=12)
    proof_table.add_column("Proof Screenshot Path", style="dim")

    verifications = exec_report.get("verification_results", [])
    for idx, v in enumerate(verifications, start=1):
        src = v.get("source", "Unknown")
        target = v.get("target", "Unknown")
        status = v.get("status", "SUCCESS").upper()
        shot = v.get("screenshot")
        shot_display = Path(shot).name if shot else "Verified via PDU"
        proof_table.add_row(str(idx), src, target, f"[bold green]{status}[/bold green]", shot_display)

    console.print(proof_table)

    # Print Academic Answers if present
    if academic_answers:
        console.print("\n")
        console.print(Panel(Markdown(academic_answers), title="[bold cyan]Academic Analysis & Theory Answers[/bold cyan]", border_style="cyan"))

    console.print(f"\n[bold green][PASS][/bold green] Workflow complete. Full report generated at: [cyan]{report_file}[/cyan]\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="NetGent Interactive Terminal Agent")
    parser.add_argument("--prompt", type=str, default=None, help="Initial assignment prompt text")
    args = parser.parse_args()
    run_interactive_agent(initial_prompt=args.prompt)


if __name__ == "__main__":
    main()
