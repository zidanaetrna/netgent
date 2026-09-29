"""PC configuration and desktop application automation for Cisco Packet Tracer.

Handles PC Desktop tab navigation, IP address and subnet configuration,
and Command Prompt network connectivity testing (ping).
"""

import logging
from pathlib import Path
import time
from typing import Optional, Tuple, Union

import numpy as np
import pyautogui
import pygetwindow as gw

from src.core.config import (
    ACTION_POST_DELAY_SECONDS,
    CLI_TYPING_INTERVAL_SECONDS,
)
from src.core.primitives import (
    AutomationPrimitiveError,
    find_and_click_element,
    find_element_on_screen,
    type_text_payload,
)

logger = logging.getLogger(__name__)


class PCManagerError(AutomationPrimitiveError):
    """Base exception for PC automation operations."""


def _get_active_pc_window() -> Optional[gw.Window]:
    """Retrieve the active PC configuration modal window."""
    try:
        active = gw.getActiveWindow()
        if active and active.title and ("Packet Tracer" not in active.title or "PC" in active.title or "Server" in active.title):
            return active
    except Exception as exc:
        logger.debug("Error checking active PC window: %s", exc)
    return None


def ensure_pc_power_on(modal: Optional[gw.Window] = None) -> bool:
    """Ensure the PC is powered on. If the power LED is dark or button is off, turn it on."""
    if not modal:
        modal = _get_active_pc_window()
    if not modal:
        return False

    # Standard PC window coordinates: x ~ 370, y ~ 297 from modal top-left
    btn_x = modal.left + 370
    btn_y = modal.top + 297

    # Check if LED right above the power button is lit (green)
    is_lit = False
    try:
        led_screenshot = pyautogui.screenshot(region=(btn_x - 3, btn_y - 15, 6, 6))
        led_np = np.array(led_screenshot)
        mean_g = float(np.mean(led_np[:, :, 1]))
        mean_r = float(np.mean(led_np[:, :, 0]))
        is_lit = (mean_g > 150) and (mean_g > mean_r + 30)
    except Exception as exc:
        logger.debug("Could not inspect LED pixel color: %s", exc)

    if not is_lit:
        logger.info("PC power is OFF (LED dark). Turning PC ON at (%d, %d)...", btn_x, btn_y)
        pyautogui.click(btn_x, btn_y)
        time.sleep(1.0)
        return True
    else:
        logger.info("PC is already powered ON.")
        return True


def open_pc_desktop(
    device_x: int,
    device_y: int,
    timeout: float = 5.0,
) -> Optional[gw.Window]:
    """Open the PC modal window, ensure power is ON, and switch to the 'Desktop' tab.

    Args:
        device_x: Screen X coordinate of the PC icon on the canvas.
        device_y: Screen Y coordinate of the PC icon on the canvas.
        timeout: Maximum seconds to wait for modal window.

    Returns:
        The matched modal Window object if found, or None.

    Raises:
        PCManagerError: If the device window cannot be opened.
    """
    logger.info("Opening PC window at (%d, %d)...", device_x, device_y)

    # Double-click the PC icon on the canvas
    pyautogui.doubleClick(device_x, device_y)
    time.sleep(1.0)

    modal = _get_active_pc_window()
    if not modal:
        logger.warning("Could not determine modal window for PC at (%d, %d)", device_x, device_y)
        return None

    # Step 1: Ensure PC is powered ON before navigating away from Physical tab
    ensure_pc_power_on(modal)

    # In the PC dialog, tabs are along the top:
    # Physical (~55px), Config (~135px), Desktop (~205px) from modal.left, ~72px from modal.top
    desktop_tab_x = modal.left + 205
    desktop_tab_y = modal.top + 72
    logger.info("Clicking Desktop tab at offset (%d, %d)", desktop_tab_x, desktop_tab_y)
    pyautogui.click(desktop_tab_x, desktop_tab_y)

    time.sleep(ACTION_POST_DELAY_SECONDS)

    # Step 3: Dismiss any warning prompt ("Device must be powered on") if it appeared
    pyautogui.press("enter")
    time.sleep(0.2)

    return modal


def configure_pc_ip(
    device_x: int,
    device_y: int,
    ip_address: str,
    subnet_mask: str = "255.255.255.0",
    default_gateway: Optional[str] = None,
    close_window_after: bool = True,
) -> None:
    """Configure static IP address settings on a PC via its Desktop IP Configuration app.

    Args:
        device_x: Screen X coordinate of the PC on the canvas.
        device_y: Screen Y coordinate of the PC on the canvas.
        ip_address: IPv4 address to assign (e.g., '192.168.1.1').
        subnet_mask: Subnet mask (default '255.255.255.0').
        default_gateway: Optional default gateway address.
        close_window_after: Whether to close the PC modal window when finished.
    """
    logger.info(
        "Configuring PC at (%d, %d) with IP %s, Mask %s, Gateway %s...",
        device_x,
        device_y,
        ip_address,
        subnet_mask,
        default_gateway,
    )

    modal = open_pc_desktop(device_x, device_y)

    if modal:
        # Exact measured center of Tile 1 (Row 1, Col 1) on Desktop grid
        ip_config_tile_x = modal.left + 100
        ip_config_tile_y = modal.top + 138
        logger.info("Clicking IP Configuration tile at offset (%d, %d)", ip_config_tile_x, ip_config_tile_y)
        pyautogui.click(ip_config_tile_x, ip_config_tile_y)

    time.sleep(ACTION_POST_DELAY_SECONDS)

    # 2. Click IPv4 Address field inside IP Configuration dialog
    # Measured exact center of IPv4 input box: x=modal.left + 450, y=modal.top + 215
    if modal:
        ip_field_x = modal.left + 450
        ip_field_y = modal.top + 215
        pyautogui.click(ip_field_x, ip_field_y)
    else:
        pyautogui.press("tab")

    time.sleep(0.2)

    # Type IP address
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.press("backspace")
    pyautogui.write(ip_address, interval=CLI_TYPING_INTERVAL_SECONDS)
    time.sleep(0.2)

    # Tab or click Subnet Mask field (y=modal.top + 248)
    if modal:
        mask_field_x = modal.left + 450
        mask_field_y = modal.top + 248
        pyautogui.click(mask_field_x, mask_field_y)
    else:
        pyautogui.press("tab")

    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.press("backspace")
    pyautogui.write(subnet_mask, interval=CLI_TYPING_INTERVAL_SECONDS)
    time.sleep(0.2)

    # Default Gateway field if provided (y=modal.top + 278)
    if default_gateway:
        if modal:
            gw_field_x = modal.left + 450
            gw_field_y = modal.top + 278
            pyautogui.click(gw_field_x, gw_field_y)
        else:
            pyautogui.press("tab")
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.1)
        pyautogui.press("backspace")
        pyautogui.write(default_gateway, interval=CLI_TYPING_INTERVAL_SECONDS)
        time.sleep(0.2)

    # 3. Close IP Configuration inner window
    if modal:
        # Top-right 'X' button of IP Configuration inner window
        close_inner_x = modal.left + modal.width - 25
        close_inner_y = modal.top + 83
        pyautogui.click(close_inner_x, close_inner_y)
    pyautogui.press("esc")
    time.sleep(0.3)

    # 4. Close PC modal window to return cleanly to canvas
    if close_window_after:
        if modal:
            try:
                modal.close()
            except Exception:
                pyautogui.hotkey("alt", "f4")
        else:
            pyautogui.hotkey("alt", "f4")
        time.sleep(ACTION_POST_DELAY_SECONDS)

    logger.info("Successfully configured IP for PC at (%d, %d)", device_x, device_y)


def run_pc_ping(
    device_x: int,
    device_y: int,
    target_ip: str,
    ping_count: int = 4,
    close_window_after: bool = True,
    screenshot_path: Optional[Union[str, Path]] = None,
) -> None:
    """Open PC Command Prompt and execute a ping test against target IP.

    Args:
        device_x: Screen X coordinate of the source PC on the canvas.
        device_y: Screen Y coordinate of the source PC on the canvas.
        target_ip: IP address to ping (e.g. '192.168.1.2').
        ping_count: Number of ping echo requests (default 4).
        close_window_after: Whether to close the PC modal window when finished.
        screenshot_path: Optional file path to save a proof screenshot of the ping result.
    """
    logger.info("Running ping from PC at (%d, %d) to %s...", device_x, device_y, target_ip)

    modal = open_pc_desktop(device_x, device_y)

    if modal:
        # Exact measured center of Tile 4 (Row 1, Col 4) on Desktop grid
        cmd_tile_x = modal.left + 585
        cmd_tile_y = modal.top + 138
        logger.info("Clicking Command Prompt tile at offset (%d, %d)", cmd_tile_x, cmd_tile_y)
        pyautogui.click(cmd_tile_x, cmd_tile_y)

    time.sleep(ACTION_POST_DELAY_SECONDS)

    # Ensure terminal focus
    if modal:
        term_x = modal.left + int(modal.width * 0.5)
        term_y = modal.top + int(modal.height * 0.55)
        pyautogui.click(term_x, term_y)

    time.sleep(0.2)

    # Send ping command
    ping_command = f"ping {target_ip} -n {ping_count}"
    logger.info("Sending command: '%s'", ping_command)
    type_text_payload(ping_command, interval=CLI_TYPING_INTERVAL_SECONDS, press_enter=True)

    # Allow time for ICMP replies (e.g., ARP resolution + 4 pings)
    time.sleep(ping_count + 1.5)

    # Capture proof screenshot if requested
    if screenshot_path:
        try:
            target_file = Path(screenshot_path)
            target_file.parent.mkdir(parents=True, exist_ok=True)
            if modal and modal.width > 0 and modal.height > 0:
                grab_region = (modal.left, modal.top, modal.width, modal.height)
                shot = pyautogui.screenshot(region=grab_region)
            else:
                shot = pyautogui.screenshot()
            shot.save(str(target_file))
            logger.info("Saved ping proof screenshot to '%s'", target_file)
        except Exception as shot_err:
            logger.warning("Failed to capture ping proof screenshot: %s", shot_err)

    if close_window_after:
        # Close Command Prompt inner window
        if modal:
            close_inner_x = modal.left + modal.width - 25
            close_inner_y = modal.top + 83
            pyautogui.click(close_inner_x, close_inner_y)
        pyautogui.press("esc")
        time.sleep(0.3)

        # Close PC modal window
        if modal:
            try:
                modal.close()
            except Exception:
                pyautogui.hotkey("alt", "f4")
        else:
            pyautogui.hotkey("alt", "f4")
        time.sleep(ACTION_POST_DELAY_SECONDS)

    logger.info("Ping test completed from PC at (%d, %d) to %s", device_x, device_y, target_ip)
