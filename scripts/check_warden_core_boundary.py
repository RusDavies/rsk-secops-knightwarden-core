#!/usr/bin/env python3
"""Compatibility entry point for the Warden core boundary check."""

from __future__ import annotations

import runpy
from pathlib import Path

SCRIPT = Path(__file__).with_name("check_core_boundary.py")

if __name__ == "__main__":
    runpy.run_path(str(SCRIPT), run_name="__main__")
