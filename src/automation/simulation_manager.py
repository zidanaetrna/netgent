"""Simulation and time acceleration controls for Cisco Packet Tracer.

Handles fast-forwarding simulation time to quickly converge Spanning Tree Protocol (STP)
and link states, as well as switching between Realtime and Simulation modes.
"""

import logging
import time
from typing import Optional

import pyautogui

from src.core.config import ACTION_POST_DELAY_SECONDS
from src.core.primitives import AutomationPrimitiveError

logger = logging.getLogger(__name__)


class SimulationManagerError(AutomationPrimitiveError):
    """Base exception for simulation control operations."""


def fast_forward_time(clicks: int = 4, delay: float = 0.2) -> None:
    """Fast-forward simulation time to accelerate network protocol convergence.

    In Cisco Packet Tracer, Spanning Tree Protocol takes 30-50 seconds to transition
    ports from listening/learning to forwarding (green lights). Triggering Fast Forward
    Time (Alt+D) accelerates convergence instantly.

    Args:
        clicks: Number of times to trigger fast forward time (default 4).
        delay: Seconds to wait between successive keystrokes.
    """
    logger.info("Fast-forwarding simulation time (%d iterations)...", clicks)

    prev_failsafe = pyautogui.FAILSAFE
    pyautogui.FAILSAFE = False
    try:
        for _ in range(clicks):
            pyautogui.hotkey("alt", "d")
            time.sleep(delay)
    finally:
        pyautogui.FAILSAFE = prev_failsafe

    time.sleep(ACTION_POST_DELAY_SECONDS)
    logger.info("Fast-forward time completed. Network convergence accelerated.")


def switch_to_realtime_mode() -> None:
    """Switch Cisco Packet Tracer to Realtime simulation mode."""
    logger.info("Switching to Realtime simulation mode...")
    pyautogui.hotkey("alt", "r")
    time.sleep(ACTION_POST_DELAY_SECONDS)
    logger.info("Switched to Realtime mode.")


def switch_to_simulation_mode() -> None:
    """Switch Cisco Packet Tracer to Event/Simulation mode."""
    logger.info("Switching to Simulation mode...")
    pyautogui.hotkey("alt", "s")
    time.sleep(ACTION_POST_DELAY_SECONDS)
    logger.info("Switched to Simulation mode.")
