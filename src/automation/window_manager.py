"""Window management module for Cisco Packet Tracer.

Handles discovering, activating, focusing, and maximizing the Cisco Packet Tracer window.
"""

import logging
import time
from typing import Optional, Tuple

import pygetwindow as gw

from src.core.config import CPT_WINDOW_TITLE_KEYWORDS, WINDOW_FOCUS_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


class WindowManagerError(Exception):
    """Base exception for window management operations."""


class WindowNotFoundError(WindowManagerError):
    """Raised when the target application window cannot be found."""


def find_cpt_window() -> Optional[gw.Window]:
    """Search for the active Cisco Packet Tracer window by title.

    Returns:
        The matched pygetwindow Window object, or None if not found.
    """
    all_titles = gw.getAllTitles()
    for keyword in CPT_WINDOW_TITLE_KEYWORDS:
        for title in all_titles:
            if keyword.lower() in title.lower():
                windows = gw.getWindowsWithTitle(title)
                if windows:
                    # Return the first matching non-empty window
                    for win in windows:
                        if win.width > 0 and win.height > 0:
                            return win
    return None


def focus_and_maximize_cpt(timeout: float = WINDOW_FOCUS_TIMEOUT_SECONDS) -> Tuple[int, int, int, int]:
    """Locate, restore, focus, and maximize the Cisco Packet Tracer window.

    Args:
        timeout: Maximum duration in seconds to attempt window acquisition.

    Returns:
        Tuple of (left, top, width, height) of the maximized window.

    Raises:
        WindowNotFoundError: If the Cisco Packet Tracer window is not found within timeout.
        WindowManagerError: If unable to activate or maximize the window.
    """
    deadline = time.time() + timeout
    target_window = None

    logger.info("Searching for Cisco Packet Tracer window...")
    while time.time() < deadline:
        target_window = find_cpt_window()
        if target_window:
            break
        time.sleep(0.5)

    if not target_window:
        msg = (
            f"Could not find a window matching any of: {CPT_WINDOW_TITLE_KEYWORDS}. "
            "Please ensure Cisco Packet Tracer is running."
        )
        logger.error(msg)
        raise WindowNotFoundError(msg)

    logger.info("Found window: '%s'", target_window.title)

    try:
        # Restore if minimized
        if target_window.isMinimized:
            target_window.restore()
            time.sleep(0.3)

        # Maximize window
        if not target_window.isMaximized:
            target_window.maximize()
            time.sleep(0.5)

        # Bring to foreground and activate
        try:
            target_window.activate()
        except Exception as act_err:
            # pygetwindow on Windows often raises an exception even when errorCode is 0 ("The operation completed successfully")
            # or when Windows foreground lock restricts stealing focus. Fallback to Win32 ShowWindow / SetForegroundWindow.
            try:
                import ctypes
                hwnd = getattr(target_window, "_hWnd", None)
                if hwnd:
                    ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass
            logger.debug("Window activate fallback used: %s", act_err)
        time.sleep(0.3)

    except Exception as exc:
        msg = f"Failed to activate and maximize window '{target_window.title}': {exc}"
        logger.warning(msg)
        # If window object exists, proceed with current bounding box rather than aborting
        pass

    box = (target_window.left, target_window.top, target_window.width, target_window.height)
    logger.info("Cisco Packet Tracer is ready. Window geometry: %s", box)
    return box


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    try:
        geometry = focus_and_maximize_cpt()
        print(f"Successfully focused CPT at {geometry}")
    except WindowNotFoundError as e:
        print(f"Packet Tracer not detected: {e}")
