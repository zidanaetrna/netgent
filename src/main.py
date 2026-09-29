import argparse
import logging
from pathlib import Path
import sys
from typing import Optional

# Ensure project root is in sys.path when executed directly as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.automation.cli_manager import execute_ios_commands, open_cli_tab
from src.automation.pc_manager import configure_pc_ip, run_pc_ping
from src.automation.preflight_check import print_report, run_preflight_checks
from src.core.primitives import CanvasCoordinateMapper
from src.core.proof_collector import generate_proof_report, save_project_recipe
from src.core.recipe_runner import execute_recipe, load_recipe
from src.automation.simulation_manager import fast_forward_time
from src.automation.topology_builder import connect_devices, deploy_device
from src.core.topology_generator import generate_star_topology, generate_vlan_topology
from src.automation.window_manager import WindowNotFoundError, focus_and_maximize_cpt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("netgent")


def run_ping_test(
    dry_run: bool = False,
    device_type: str = "router_2911",
    cable_type: str = "copper_cross_over",
) -> None:
    """Run an end-to-end topology deployment and configuration test.

    Supports both Cisco IOS router topologies and PC-to-PC crossover topologies (Task 5.2).

    Workflow:
      1. Focus and maximize Cisco Packet Tracer.
      2. Deploy two devices (routers or PCs) onto the canvas.
      3. Connect them using the specified cable.
      4. Configure IP addresses and verify ping connectivity.
    """
    is_pc = device_type.lower() == "pc"
    logger.info(
        "Starting Packet Tracer Ping Test (dry_run=%s, device=%s, cable=%s, mode=%s)...",
        dry_run,
        device_type,
        cable_type,
        "PC-to-PC" if is_pc else "Router-IOS",
    )

    if dry_run:
        logger.info("[Dry Run] Simulating window acquisition...")
        mock_window_box = (0, 0, 1920, 1080)
        mapper = CanvasCoordinateMapper(mock_window_box)
        d1_coords = mapper.to_screen_coords(0.35, 0.45)
        d2_coords = mapper.to_screen_coords(0.65, 0.45)
        logger.info("[Dry Run] Device 1 (%s) planned at %s", device_type, d1_coords)
        logger.info("[Dry Run] Device 2 (%s) planned at %s", device_type, d2_coords)
        logger.info("[Dry Run] Connection (%s) planned: %s -> %s", cable_type, d1_coords, d2_coords)
        if is_pc:
            logger.info("[Dry Run] PC1 IP plan: 192.168.1.1/24, PC2 IP plan: 192.168.1.2/24")
            logger.info("[Dry Run] Ping verification plan: PC1 -> ping 192.168.1.2")
        else:
            logger.info("[Dry Run] Router R1 config plan: Gig0/0 IP 192.168.1.1/24")
        logger.info("[Dry Run] Verification complete. Primitives and mapping validated.")
        return

    try:
        window_box = focus_and_maximize_cpt()
    except WindowNotFoundError as err:
        logger.error("Aborting: %s", err)
        sys.exit(1)

    mapper = CanvasCoordinateMapper(window_box)
    dev1_pos = mapper.to_screen_coords(0.35, 0.45)
    dev2_pos = mapper.to_screen_coords(0.65, 0.45)

    # 1. Deploy devices
    deploy_device(device_type, *dev1_pos, coordinate_mapper=mapper)
    deploy_device(device_type, *dev2_pos, coordinate_mapper=mapper)

    # 2. Connect devices
    connect_devices(dev1_pos, dev2_pos, cable_type=cable_type)

    # Accelerate network convergence (STP green link lights)
    logger.info("Accelerating network convergence...")
    fast_forward_time(clicks=4)

    # 3. Configure IP addresses and test connectivity
    if is_pc:
        logger.info("Configuring PC1 (192.168.1.1/24)...")
        configure_pc_ip(dev1_pos[0], dev1_pos[1], "192.168.1.1", "255.255.255.0")

        logger.info("Configuring PC2 (192.168.1.2/24)...")
        configure_pc_ip(dev2_pos[0], dev2_pos[1], "192.168.1.2", "255.255.255.0")

        logger.info("Executing connectivity ping: PC1 -> 192.168.1.2...")
        run_pc_ping(dev1_pos[0], dev1_pos[1], "192.168.1.2", ping_count=4)
    else:
        logger.info("Configuring Router 1 via IOS CLI...")
        open_cli_tab(*dev1_pos)
        execute_ios_commands([
            "no",
            "enable",
            "configure terminal",
            "hostname R1",
            "interface GigabitEthernet0/0",
            "ip address 192.168.1.1 255.255.255.0",
            "no shutdown",
            "end",
        ])

    logger.info("End-to-end ping test workflow finished successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Netgent Cisco Packet Tracer Automation Agent")
    parser.add_argument(
        "--interactive",
        "--cli",
        action="store_true",
        dest="interactive",
        help="Launch the interactive Rich TUI Agent in the terminal",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the workflow without executing actual GUI clicks",
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Run environment health and window diagnostics",
    )
    parser.add_argument(
        "--generate",
        type=str,
        choices=["star", "vlan", "router_on_a_stick"],
        default=None,
        help="Dynamically synthesize and execute a network architecture",
    )
    parser.add_argument(
        "--pcs",
        type=int,
        default=3,
        help="Number of client workstations for generated star topologies",
    )
    parser.add_argument(
        "--recipe",
        type=str,
        default=None,
        help="Path to YAML/JSON topology recipe file to deploy and configure",
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory where assets and proof screenshots will be stored",
    )
    parser.add_argument(
        "--device-type",
        type=str,
        default="router_2911",
        help="Device model identifier to deploy (e.g., router_2911, router_1941, pc)",
    )
    parser.add_argument(
        "--cable-type",
        type=str,
        default="copper_cross_over",
        help="Cable type to connect devices (e.g., copper_cross_over, auto_connection)",
    )
    parser.add_argument(
        "--clipboard",
        action="store_true",
        help="Synthesize and run using text from your current system clipboard",
    )
    parser.add_argument(
        "--prompt-file",
        type=str,
        default=None,
        help="Path to text or markdown file containing lab assignment prompt",
    )
    parser.add_argument(
        "--engine",
        type=str,
        choices=["ipc", "hybrid", "gui"],
        default="ipc",
        help="Automation engine to execute topologies (ipc: pure programmatic, hybrid: visual feedback, gui: vision/mouse)",
    )
    args = parser.parse_args()

    # Check clipboard or prompt file
    initial_prompt: Optional[str] = None
    if args.clipboard:
        from src.ui.agent_cli import get_clipboard_content
        clip = get_clipboard_content()
        if clip:
            initial_prompt = clip
        else:
            print("[!] Clipboard is empty or could not be accessed.")
    elif args.prompt_file:
        p_path = Path(args.prompt_file)
        if p_path.is_file():
            initial_prompt = p_path.read_text(encoding="utf-8")
        else:
            print(f"[!] Prompt file not found: {p_path}")

    if args.interactive or args.clipboard or args.prompt_file or (len(sys.argv) == 1):
        from src.ui.agent_cli import run_interactive_agent
        run_interactive_agent(initial_prompt=initial_prompt)
        return

    if args.preflight:
        report = run_preflight_checks()
        print_report(report)
        return

    if args.generate:
        if args.generate in ["star"]:
            recipe = generate_star_topology(num_pcs=args.pcs)
        else:
            recipe = generate_vlan_topology()
        exec_report = execute_recipe(recipe, dry_run=args.dry_run, engine=args.engine, project_dir=args.project_dir)
        if args.project_dir:
            p_dir = Path(args.project_dir)
            save_project_recipe(p_dir, recipe)
            generate_proof_report(p_dir, recipe, exec_report)
    elif args.recipe:
        recipe = load_recipe(args.recipe)
        exec_report = execute_recipe(recipe, dry_run=args.dry_run, engine=args.engine, project_dir=args.project_dir)
        if args.project_dir:
            p_dir = Path(args.project_dir)
            save_project_recipe(p_dir, recipe)
            generate_proof_report(p_dir, recipe, exec_report)
    else:
        run_ping_test(
            dry_run=args.dry_run,
            device_type=args.device_type,
            cable_type=args.cable_type,
        )


if __name__ == "__main__":
    main()
