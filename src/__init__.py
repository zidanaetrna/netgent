"""NetGent: Autonomous AI Network Engineering Agent for Cisco Packet Tracer.

Package Architecture:
    - netgent.core: Foundational configuration, primitives, recipe orchestration, and proof collection.
    - netgent.automation: Low-level IPC Socket.IO bridge, CV template matching, CLI, PC, and simulation drivers.
    - netgent.ui: Interactive Claude Code-style terminal CLI, native desktop GUI, and web server.
    - netgent.ai: LLM client and Model Context Protocol (MCP) server.
"""

__version__ = "1.0.0"
__author__ = "zidanaetrna"

from src import core
from src import automation
from src import ui
from src import ai

__all__ = ["core", "automation", "ui", "ai", "__version__", "__author__"]
