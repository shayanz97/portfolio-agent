from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from portfolio_agent.config.models import RuntimeConfig


class ConfigError(RuntimeError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"Config file must contain a mapping: {path}")
    return data


def load_config(config_dir: str | Path = "config") -> RuntimeConfig:
    config_dir = Path(config_dir)
    master = _load_yaml(config_dir / "config.yaml")

    merged: dict[str, Any] = {
        "version": master["version"],
        "environment": master["environment"],
    }

    for include in master.get("includes", []):
        child = _load_yaml(config_dir / include)
        overlap = set(merged).intersection(child)
        if overlap:
            raise ConfigError(
                f"Duplicate top-level config keys {sorted(overlap)} in {include}"
            )
        merged.update(child)

    return RuntimeConfig.model_validate(merged)


def config_hash(config: RuntimeConfig) -> str:
    canonical = json.dumps(
        config.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
