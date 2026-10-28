"""Config loading, seeding and run metadata.

Every script calls load_config() so parameters live in one YAML file, and config_hash()
so cached artifacts are keyed by the parameters that produced them.
"""

from __future__ import annotations

import hashlib
import json
import random
import subprocess
from pathlib import Path

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "default.yaml"


def load_config(path: str | Path | None = None) -> dict:
    with open(path or DEFAULT_CONFIG) as f:
        cfg = yaml.safe_load(f)
    # Resolve every path relative to the repo root so scripts work from any cwd.
    cfg["paths"] = {k: str(REPO_ROOT / v) for k, v in cfg["paths"].items()}
    return cfg


def config_hash(section: dict) -> str:
    """Short stable hash of a config section, used to key cache files."""
    blob = json.dumps(section, sort_keys=True).encode()
    return hashlib.sha1(blob).hexdigest()[:10]


def set_seeds(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
    except ImportError:
        pass


def git_hash() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "nogit"
