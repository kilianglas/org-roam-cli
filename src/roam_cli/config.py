from __future__ import annotations

import sys
from pathlib import Path

import tomli_w

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


CONFIG_DIR = Path.home() / ".config" / "roam-cli"
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULT_DB_PATH = Path.home() / ".emacs.d" / ".local" / "cache" / "org-roam.db"
DEFAULT_ROAM_DIR = Path.home() / "org" / "roam"


def load_config() -> dict:
    if CONFIG_FILE.exists():
        return tomllib.loads(CONFIG_FILE.read_text())
    return {}


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(tomli_w.dumps(config))


def get_db_path(override: str | None = None) -> Path:
    if override:
        return Path(override)
    config = load_config()
    if "db_path" in config:
        return Path(config["db_path"])
    return DEFAULT_DB_PATH


def get_roam_dir(override: str | None = None) -> Path:
    if override:
        return Path(override)
    config = load_config()
    if "roam_dir" in config:
        return Path(config["roam_dir"])
    return DEFAULT_ROAM_DIR


def interactive_config() -> dict:
    config = load_config()

    db_path = input(f"org-roam database path [{config.get('db_path', DEFAULT_DB_PATH)}]: ").strip()
    if db_path:
        config["db_path"] = db_path
    elif "db_path" not in config:
        config["db_path"] = str(DEFAULT_DB_PATH)

    roam_dir = input(f"org-roam root directory [{config.get('roam_dir', DEFAULT_ROAM_DIR)}]: ").strip()
    if roam_dir:
        config["roam_dir"] = roam_dir
    elif "roam_dir" not in config:
        config["roam_dir"] = str(DEFAULT_ROAM_DIR)

    save_config(config)
    return config
