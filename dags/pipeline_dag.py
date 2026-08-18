"""Airflow DAG entry point.

This project sits in Airflow's DAGs folder but its own modules are not on
the Python path. The bootstrap below fixes that, so `from src... import ...`
resolves once you create those modules.

Everything below the bootstrap is yours to design. Decide your module
structure, your tasks, and your schedule — that is part of the work.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# TODO: define your DAG below.
