"""Compatibility package for local ARG-Designer dataset adapters.

This repository historically imports local adapters as ``datasets.foo`` while
some dependencies import HuggingFace ``datasets``.  The module proxies the
external package when available and also exposes this directory for local
submodules such as ``datasets.mmlu_dataset``.
"""

from __future__ import annotations

import importlib
import os
import sys


_LOCAL_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.dirname(_LOCAL_DIR)
_THIS_MODULE = sys.modules[__name__]


def _is_repo_path(path: str) -> bool:
    resolved = os.path.abspath(path or os.getcwd())
    return resolved == _REPO_ROOT or resolved.startswith(_REPO_ROOT + os.sep)


def _load_external_datasets():
    saved_module = sys.modules.pop(__name__, None)
    saved_path = list(sys.path)
    try:
        sys.path = [path for path in sys.path if not _is_repo_path(path)]
        return importlib.import_module(__name__)
    except Exception:
        return None
    finally:
        sys.path = saved_path
        sys.modules[__name__] = _THIS_MODULE if saved_module is None else saved_module


_external = _load_external_datasets()
if _external is not None:
    for _name, _value in _external.__dict__.items():
        if _name in {"__name__", "__package__", "__loader__", "__spec__", "__path__", "__file__"}:
            continue
        globals()[_name] = _value
    __path__ = [_LOCAL_DIR] + [path for path in getattr(_external, "__path__", []) if path != _LOCAL_DIR]
else:
    __path__ = [_LOCAL_DIR]

