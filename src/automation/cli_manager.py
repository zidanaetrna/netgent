"""CLI configuration management skills for Cisco Packet Tracer devices.

Handles opening device configuration windows, selecting the CLI tab, and executing
Cisco IOS command sequences.
"""

import logging
import time
from typing import List, Optional, Tuple, Union

import pyautogui
import pygetwindow as gw

import pyperclip

from src.core.config import (
    ACTION_POST_DELAY_SECONDS,
    CLI_TYPING_INTERVAL_SECONDS,
)
from src.core.primitives import (
    AutomationPrimitiveError,
    find_and_click_element,
    type_text_payload,
)

logger = logging.getLogger(__name__)


class CLIError(AutomationPrimitiveError):
    """Base exception for CLI automation operations."""


def _get_active_modal_window() -> Optional[gw.Window]:
    """Retrieve the currently focused device modal dialog window."""
    try:
        active = gw.getActiveWindow()
        if active and active.title and ("Packet Tracer" not in active.title or "Router" in active.title or "Switch" in active.title):
            return active
    except Exception as exc:
        logger.debug("Could not inspect active window: %s", exc)
    return None


def open_cli_tab(
    device_x: int,
    device_y: int,
    timeout: float = 5.0,
) -> None:
    """Open the configuration modal for a device and activate the CLI tab.

    Args:
        device_x: Canvas screen X coordinate of the target device.
        device_y: Canvas screen Y coordinate of the target device.
        timeout: Seconds to wait for modal window and CLI tab to appear.

    Raises:
        CLIError: If unable to open the device window or switch to the CLI tab.
    """
    logger.info("Opening device window at (%d, %d)...", device_x, device_y)

    # Double-click the device icon on the canvas
    pyautogui.doubleClick(device_x, device_y)
    time.sleep(1.0)  # Wait for modal window to render

    # Use modal window coordinates to switch to CLI tab:
    # In Cisco Packet Tracer device windows, the CLI tab is typically the 3rd tab:
    # Physical (~45px), Config (~95px), CLI (~145px) from window left, ~55px from window top.
    # Physical (~45px), Config (~95px), CLI (~145px) from window left, ~55px from window top.
    modal_window = _get_active_modal_window()
    if modal_window:
        cli_tab_x = modal_window.left + 145
        cli_tab_y = modal_window.top + 55
        terminal_x = modal_window.left + int(modal_window.width * 0.5)
        terminal_y = modal_window.top + int(modal_window.height * 0.6)

        logger.info(
            "Targeting CLI tab via modal window '%s' at (%d, %d)",
            modal_window.title,
            cli_tab_x,
            cli_tab_y,
        )
        pyautogui.click(cli_tab_x, cli_tab_y)
        time.sleep(0.5)
        # Click terminal area to focus prompt
        pyautogui.click(terminal_x, terminal_y)
        time.sleep(0.3)
    else:
        # Fallback to wake-up click in canvas area
        pyautogui.press("enter")
        time.sleep(0.3)

    logger.info("CLI window opened and focused.")


def close_cli_window(modal_window: Optional[gw.Window] = None) -> None:
    """Close the active device modal window and return focus to the main canvas.

    Essential for heavy topologies to prevent accumulated modal dialogs from
    obscuring underlying canvas devices.
    """
    target_modal = modal_window or _get_active_modal_window()
    if target_modal:
        logger.info("Closing device modal window '%s'...", getattr(target_modal, "title", "Device"))
        try:
            target_modal.close()
            time.sleep(0.4)
            return
        except Exception as exc:
            logger.debug("modal.close() failed (%s), attempting Alt+F4 fallback...", exc)

    # Hotkey fallback to dismiss focused device window
    pyautogui.hotkey("alt", "f4")
    time.sleep(0.4)


def wait_for_ios_ready(timeout_seconds: float = 25.0, poll_interval: float = 1.0) -> bool:
    """Poll the active CLI terminal until Cisco IOS finishes booting and displays a prompt.

    In heavy topologies with multiple routers, routers take 15-25 seconds to boot.
    Returns True when prompt ('>', '#', or '[yes/no]') is detected, or False on timeout.
    """
    start_time = time.time()
    logger.info("Waiting for Cisco IOS boot sequence to complete (up to %.1fs)...", timeout_seconds)

    while time.time() - start_time < timeout_seconds:
        pyautogui.press("enter")
        time.sleep(0.3)
        output = read_cli_output(timeout=0.5)

        if any(marker in output for marker in [">", "#", "[yes/no]:", "[yes/no]", "Press RETURN"]):
            logger.info("IOS terminal prompt detected and ready for commands.")
            return True

        logger.debug("Waiting for IOS boot... (%.1fs elapsed)", time.time() - start_time)
        time.sleep(poll_interval)

    logger.warning("IOS boot wait timed out after %.1fs. Proceeding with commands.", timeout_seconds)
    return False


def execute_ios_commands(
    command_list: List[str],
    typing_interval: float = CLI_TYPING_INTERVAL_SECONDS,
    command_delay: float = ACTION_POST_DELAY_SECONDS,
    dismiss_initial_dialog: bool = True,
    wait_for_boot: bool = False,
    close_window_after: bool = False,
) -> None:
    """Execute a list of Cisco IOS commands sequentially in the active CLI terminal.

    Args:
        command_list: List of command strings (e.g. ['enable', 'configure terminal', 'hostname R1']).
        typing_interval: Delay between keystrokes.
        command_delay: Delay between successive commands to allow prompt response.
        dismiss_initial_dialog: If True, sends 'no' and Enter to dismiss CPT initial configuration prompt.
        wait_for_boot: If True, polls terminal until IOS prompt is ready before sending commands.
        close_window_after: If True, closes the device modal window when finished.
    """
    if wait_for_boot:
        wait_for_ios_ready()

    logger.info("Executing %d IOS commands (dismiss_initial_dialog=%s)...", len(command_list), dismiss_initial_dialog)

    # Send initial Enter to ensure terminal prompt is awake
    pyautogui.press("enter")
    time.sleep(0.3)

    if dismiss_initial_dialog:
        # Dismiss 'Would you like to enter the initial configuration dialog? [yes/no]:'
        type_text_payload("no", interval=typing_interval, press_enter=True)
        time.sleep(0.5)
        pyautogui.press("enter")
        time.sleep(0.3)

    for idx, command in enumerate(command_list, start=1):
        clean_command = command.strip()
        logger.debug("Running command [%d/%d]: '%s'", idx, len(command_list), clean_command)
        type_text_payload(clean_command, interval=typing_interval, press_enter=True)
        time.sleep(command_delay)

    logger.info("Successfully executed all IOS commands.")

    if close_window_after:
        close_cli_window()


def read_cli_output(timeout: float = 1.0) -> str:
    """Read and return the text currently displayed in the active CLI terminal window.

    Extracts text using the CPT 'Copy' button or clipboard buffer.

    Args:
        timeout: Maximum seconds to wait for clipboard response.

    Returns:
        The string text contents of the terminal buffer.
    """
    modal = _get_active_modal_window()
    if modal:
        # Click terminal area to focus
        term_x = modal.left + int(modal.width * 0.5)
        term_y = modal.top + int(modal.height * 0.6)
        pyautogui.click(term_x, term_y)
        time.sleep(0.2)

        # In Packet Tracer CLI tab, the 'Copy' button is located near bottom right
        copy_btn_x = modal.left + modal.width - 65
        copy_btn_y = modal.top + modal.height - 35
        pyautogui.click(copy_btn_x, copy_btn_y)
        time.sleep(0.3)

    try:
        content = pyperclip.paste()
        logger.debug("Read %d characters from CLI clipboard buffer.", len(content))
        return content
    except Exception as exc:
        logger.warning("Could not read clipboard buffer: %s", exc)
        return ""


def verify_cli_command(
    command: str,
    expected_snippet: Optional[str] = None,
) -> Tuple[bool, str]:
    """Execute a single IOS command and verify that it succeeded without errors.

    Args:
        command: IOS command to verify (e.g. 'show ip interface brief').
        expected_snippet: Optional substring that must be present in the output.

    Returns:
        Tuple of (is_successful, output_text).
    """
    execute_ios_commands([command], dismiss_initial_dialog=False)
    time.sleep(0.5)
    output = read_cli_output()

    # Cisco IOS error signatures
    error_patterns = [
        "% Invalid input detected",
        "% Incomplete command",
        "% Ambiguous command",
        "% Unknown command",
    ]
    for pattern in error_patterns:
        if pattern.lower() in output.lower():
            logger.warning("Command '%s' produced IOS error: %s", command, pattern)
            return False, output

    if expected_snippet and expected_snippet.lower() not in output.lower():
        logger.warning(
            "Command '%s' output did not contain expected snippet '%s'",
            command,
            expected_snippet,
        )
        return False, output

    return True, output


def configure_interface_ip(
    interface_name: str,
    ip_address: str,
    subnet_mask: str,
) -> List[str]:
    """Helper to generate IOS commands to configure an IP address on an interface."""
    return [
        "enable",
        "configure terminal",
        f"interface {interface_name}",
        f"ip address {ip_address} {subnet_mask}",
        "no shutdown",
        "exit",
        "exit",
        "write memory",
    ]


def configure_vlan(
    vlan_id: int,
    vlan_name: str,
    interfaces: Optional[List[str]] = None,
) -> List[str]:
    """Helper to generate IOS commands to create a VLAN and assign switchports.

    Args:
        vlan_id: VLAN ID number (1-4094).
        vlan_name: Descriptive name for the VLAN.
        interfaces: Optional list of switch interface names to assign to this VLAN.
    """
    commands = [
        "enable",
        "configure terminal",
        f"vlan {vlan_id}",
        f"name {vlan_name}",
        "exit",
    ]
    if interfaces:
        for intf in interfaces:
            commands.extend([
                f"interface {intf}",
                "switchport mode access",
                f"switchport access vlan {vlan_id}",
                "no shutdown",
                "exit",
            ])
    commands.extend(["exit", "write memory"])
    return commands


def configure_trunk(interface_name: str) -> List[str]:
    """Helper to generate IOS commands to configure an 802.1Q trunk port."""
    return [
        "enable",
        "configure terminal",
        f"interface {interface_name}",
        "switchport mode trunk",
        "no shutdown",
        "exit",
        "exit",
        "write memory",
    ]
