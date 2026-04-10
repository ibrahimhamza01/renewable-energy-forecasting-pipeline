import os
import yaml
from pathlib import Path
from copy import deepcopy


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge two dictionaries."""
    result = deepcopy(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


class Config:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]

        # Load shared configs
        self.project = _load_yaml(self.project_root / "configs/project_config.yaml")
        self.runtime = _load_yaml(self.project_root / "configs/runtime_config.yaml")
        self.paths = _load_yaml(self.project_root / "configs/paths.yaml")
        self.spark = _load_yaml(self.project_root / "configs/spark_config.yaml")
        self.airflow = _load_yaml(self.project_root / "configs/airflow_config.yaml")

        # Load user config
        user_config_path = os.getenv("PROJECT_USER_CONFIG")
        if not user_config_path:
            raise ValueError("PROJECT_USER_CONFIG environment variable is not set")

        user_config = _load_yaml(self.project_root / user_config_path)

        # Merge user config into runtime
        self.user = user_config.get("user", {})
        self.aws = user_config.get("aws", {})
        self.ec2 = user_config.get("ec2", {})

        self.runtime = _deep_merge(self.runtime, user_config.get("runtime", {}))

    def __repr__(self):
        return f"<Config user={self.user.get('name')}>"


# Singleton config object
config = Config()
