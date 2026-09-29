"""Foundational UI automation primitives for Cisco Packet Tracer.

Provides OpenCV fuzzy template matching, canvas coordinate boundary mapping,
and safe keystroke execution.
"""

import logging
import time
from pathlib import Path
from typing import Optional, Tuple, Union

import cv2
import numpy as np
import pyautogui
from PIL import Image

from src.core.config import (
    ACTION_POST_DELAY_SECONDS,
    CLI_TYPING_INTERVAL_SECONDS,
)

DEFAULT_OPENCV_CONFIDENCE = 0.8
logger = logging.getLogger(__name__)

# Configure PyAutoGUI safety settings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


class AutomationPrimitiveError(Exception):
    """Base exception for automation primitives."""


class ElementNotFoundError(AutomationPrimitiveError):
    """Raised when a UI template image cannot be located on the screen."""


class CoordinateOutOfBoundsError(AutomationPrimitiveError):
    """Raised when target coordinates fall outside the allowable canvas bounds."""


def resolve_asset_path(asset_path: Union[str, Path]) -> Path:
    """Resolve an asset path if relative."""
    path = Path(asset_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Template asset does not exist: {path}")
    return path


def find_element_on_screen(
    template_path: Union[str, Path],
    confidence: float = DEFAULT_OPENCV_CONFIDENCE,
    region: Optional[Tuple[int, int, int, int]] = None,
    grayscale: bool = True,
) -> Optional[Tuple[int, int, float]]:
    """Locate a template image on the screen using OpenCV template matching.

    Args:
        template_path: Path to the template image file.
        confidence: Minimum matching correlation coefficient (0.0 to 1.0).
        region: Optional (left, top, width, height) bounding box to constrain search.
        grayscale: If True, performs matching in grayscale for speed and illumination tolerance.

    Returns:
        (center_x, center_y, match_score) if matched, otherwise None.
    """
    resolved_path = resolve_asset_path(template_path)

    # Capture screen region
    screenshot_pil = pyautogui.screenshot(region=region)
    screenshot_np = np.array(screenshot_pil)

    # Read template image
    template_cv = cv2.imread(str(resolved_path), cv2.IMREAD_COLOR)
    if template_cv is None:
        raise ValueError(f"Failed to read image at {resolved_path}")

    # Convert RGB/BGR formats
    screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    if grayscale:
        screen_proc = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
        template_proc = cv2.cvtColor(template_cv, cv2.COLOR_BGR2GRAY)
    else:
        screen_proc = screenshot_cv
        template_proc = template_cv

    th, tw = template_proc.shape[:2]
    sh, sw = screen_proc.shape[:2]

    if th > sh or tw > sw:
        logger.warning(
            "Template size (%dx%d) exceeds screen region (%dx%d)", tw, th, sw, sh
        )
        return None

    best_val = -1.0
    best_loc = None
    best_dims = (tw, th)

    # Multi-scale matching: 1.0 (native), plus scaled factors to bridge resolution differences
    candidate_scales = [1.0, 1.25, 1.5, 1.75, 1.875, 2.0, 0.8, 0.67]
    for scale in candidate_scales:
        if scale == 1.0:
            scaled_tmpl = template_proc
            curr_th, curr_tw = th, tw
        else:
            curr_tw = int(tw * scale)
            curr_th = int(th * scale)
            if curr_th > sh or curr_tw > sw or curr_tw < 8 or curr_th < 8:
                continue
            scaled_tmpl = cv2.resize(template_proc, (curr_tw, curr_th), interpolation=cv2.INTER_LINEAR)

        result = cv2.matchTemplate(screen_proc, scaled_tmpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > best_val:
            best_val = max_val
            best_loc = max_loc
            best_dims = (curr_tw, curr_th)

        if best_val >= 0.95:
            break

    if best_val >= confidence and best_loc is not None:
        match_tw, match_th = best_dims
        offset_x = region[0] if region else 0
        offset_y = region[1] if region else 0
        match_x = best_loc[0] + offset_x
        match_y = best_loc[1] + offset_y
        center_x = match_x + match_tw // 2
        center_y = match_y + match_th // 2
        logger.debug(
            "Found '%s' at (%d, %d) with confidence %.3f (threshold: %.3f)",
            resolved_path.name,
            center_x,
            center_y,
            best_val,
            confidence,
        )
        return center_x, center_y, float(best_val)

    logger.debug(
        "Template '%s' max score %.3f below threshold %.3f",
        resolved_path.name,
        best_val,
        confidence,
    )
    return None


def find_and_click_element(
    template_path: Union[str, Path],
    confidence: float = DEFAULT_OPENCV_CONFIDENCE,
    retries: int = 3,
    delay_between_retries: float = 0.5,
    double_click: bool = False,
    region: Optional[Tuple[int, int, int, int]] = None,
) -> Tuple[int, int]:
    """Locate a template on screen and click its center point with retries.

    Args:
        template_path: Path to the reference template image.
        confidence: Minimum matching confidence threshold.
        retries: Number of retry attempts before raising ElementNotFoundError.
        delay_between_retries: Seconds to sleep between retries.
        double_click: Whether to perform a double-click instead of a single click.
        region: Optional screen region to restrict search.

    Returns:
        Tuple of (clicked_x, clicked_y).

    Raises:
        ElementNotFoundError: If template is not found after all retries.
    """
    resolved_path = resolve_asset_path(template_path)

    for attempt in range(1, retries + 1):
        match = find_element_on_screen(
            template_path=resolved_path,
            confidence=confidence,
            region=region,
        )
        if match:
            cx, cy, score = match
            if double_click:
                pyautogui.doubleClick(cx, cy)
            else:
                pyautogui.click(cx, cy)

            time.sleep(ACTION_POST_DELAY_SECONDS)
            logger.info(
                "Clicked element '%s' at (%d, %d) [score: %.2f]",
                resolved_path.name,
                cx,
                cy,
                score,
            )
            return cx, cy

        if attempt < retries:
            time.sleep(delay_between_retries)

    msg = f"Failed to find element '{resolved_path.name}' after {retries} attempts."
    logger.error(msg)
    raise ElementNotFoundError(msg)


class CanvasCoordinateMapper:
    """Maps and validates logical canvas coordinates within the Packet Tracer window."""

    def __init__(
        self,
        window_box: Tuple[int, int, int, int],
        top_offset: int = 110,
        bottom_offset: int = 90,
        left_offset: int = 40,
        right_offset: int = 30,
    ) -> None:
        """Initialize the canvas boundary mapper.

        Args:
            window_box: Tuple of (win_left, win_top, win_width, win_height).
            top_offset: Pixels occupied by top menus and toolbars.
            bottom_offset: Pixels occupied by bottom device dock and status bar.
            left_offset: Pixels occupied by the left tool palette.
            right_offset: Pixels reserved for right scrollbars / simulation window dock.
        """
        win_left, win_top, win_width, win_height = window_box

        self.canvas_left = win_left + left_offset
        self.canvas_top = win_top + top_offset
        self.canvas_width = max(100, win_width - (left_offset + right_offset))
        self.canvas_height = max(100, win_height - (top_offset + bottom_offset))
        self.canvas_right = self.canvas_left + self.canvas_width
        self.canvas_bottom = self.canvas_top + self.canvas_height

        logger.info(
            "Canvas region initialized: X=[%d to %d], Y=[%d to %d] (size %dx%d)",
            self.canvas_left,
            self.canvas_right,
            self.canvas_top,
            self.canvas_bottom,
            self.canvas_width,
            self.canvas_height,
        )

    def is_within_bounds(self, screen_x: int, screen_y: int) -> bool:
        """Check if an absolute screen coordinate is inside the usable canvas."""
        return (
            self.canvas_left <= screen_x <= self.canvas_right
            and self.canvas_top <= screen_y <= self.canvas_bottom
        )

    def to_screen_coords(self, normalized_x: float, normalized_y: float) -> Tuple[int, int]:
        """Convert normalized (0.0 to 1.0) canvas coordinates to absolute screen pixels.

        Args:
            normalized_x: Horizontal position ratio (0.0=left edge, 1.0=right edge).
            normalized_y: Vertical position ratio (0.0=top edge, 1.0=bottom edge).

        Returns:
            Tuple of (screen_x, screen_y).

        Raises:
            CoordinateOutOfBoundsError: If ratios are not within [0.0, 1.0].
        """
        if not (0.0 <= normalized_x <= 1.0 and 0.0 <= normalized_y <= 1.0):
            raise CoordinateOutOfBoundsError(
                f"Normalized coordinates ({normalized_x}, {normalized_y}) must be between 0.0 and 1.0"
            )

        screen_x = int(self.canvas_left + normalized_x * self.canvas_width)
        screen_y = int(self.canvas_top + normalized_y * self.canvas_height)
        return screen_x, screen_y

    def validate_or_clamp(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """Clamp absolute screen coordinates to the safe canvas boundary."""
        clamped_x = max(self.canvas_left, min(self.canvas_right, screen_x))
        clamped_y = max(self.canvas_top, min(self.canvas_bottom, screen_y))
        return clamped_x, clamped_y


def type_text_payload(
    text: str,
    interval: float = CLI_TYPING_INTERVAL_SECONDS,
    press_enter: bool = True,
) -> None:
    """Safely type text payload into the currently active window or CLI prompt.

    Args:
        text: String of commands or text to type.
        interval: Keystroke delay in seconds.
        press_enter: Whether to append an Enter key press at the end.
    """
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line:
            pyautogui.write(line, interval=interval)
        # Handle line breaks
        if index < len(lines) - 1 or press_enter:
            pyautogui.press("enter")
            time.sleep(ACTION_POST_DELAY_SECONDS)
