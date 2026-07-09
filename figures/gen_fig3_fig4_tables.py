#!/usr/bin/env python3
"""Regenerate AQuA first200 paper figures and tables."""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.paper_figure_artifacts import main


if __name__ == "__main__":
    main()
