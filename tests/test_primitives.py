"""Unit tests for automation primitives and canvas mapping."""

import unittest
from pathlib import Path

from src.core.primitives import (
    CanvasCoordinateMapper,
    CoordinateOutOfBoundsError,
)
from src.core.config import PROJECT_ROOT


class TestCanvasCoordinateMapper(unittest.TestCase):
    def setUp(self):
        # Window box: left=0, top=0, width=1920, height=1080
        self.window_box = (0, 0, 1920, 1080)
        self.mapper = CanvasCoordinateMapper(
            self.window_box,
            top_offset=110,
            bottom_offset=90,
            left_offset=40,
            right_offset=30,
        )

    def test_bounds_calculation(self):
        self.assertEqual(self.mapper.canvas_left, 40)
        self.assertEqual(self.mapper.canvas_top, 110)
        self.assertEqual(self.mapper.canvas_width, 1920 - 70)
        self.assertEqual(self.mapper.canvas_height, 1080 - 200)

    def test_normalized_mapping(self):
        # Center mapping (0.5, 0.5)
        cx, cy = self.mapper.to_screen_coords(0.5, 0.5)
        expected_x = 40 + int(0.5 * (1920 - 70))
        expected_y = 110 + int(0.5 * (1080 - 200))
        self.assertEqual((cx, cy), (expected_x, expected_y))
        self.assertTrue(self.mapper.is_within_bounds(cx, cy))

    def test_out_of_bounds(self):
        with self.assertRaises(CoordinateOutOfBoundsError):
            self.mapper.to_screen_coords(1.5, 0.5)

    def test_clamping(self):
        clamped_x, clamped_y = self.mapper.validate_or_clamp(-100, 2000)
        self.assertEqual(clamped_x, self.mapper.canvas_left)
        self.assertEqual(clamped_y, self.mapper.canvas_bottom)


if __name__ == "__main__":
    unittest.main()
