"""Compatibility entrypoint that runs the root-level app.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT_APP_PATH = PROJECT_ROOT / "app.py"

# Ensure root-level modules (data_loader, metrics_engine, etc.) are importable.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

spec = importlib.util.spec_from_file_location("root_streamlit_app", ROOT_APP_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.render()
