"""Configuration settings for Cisco Packet Tracer automation."""

from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Window Target
# Cisco Packet Tracer typically displays titles like "Cisco Packet Tracer" or "Cisco Packet Tracer - [FileName]"
CPT_WINDOW_TITLE_KEYWORDS = ["Cisco Packet Tracer", "Packet Tracer"]

# IPC Socket Configuration
DEFAULT_IPC_HOST = "127.0.0.1"
DEFAULT_IPC_PORT = 7531
DEFAULT_IPC_TIMEOUT = 15.0

# Automation Delays and Thresholds
WINDOW_FOCUS_TIMEOUT_SECONDS = 5.0
ACTION_POST_DELAY_SECONDS = 0.5
CLI_TYPING_INTERVAL_SECONDS = 0.05

