# roam-cli

CLI tool for querying [org-roam](https://www.orgroam.com/) SQLite databases. Designed for use by Claude Code and other programmatic consumers.

## Install

```
uv sync
```

## Usage

```
roam-cli get <id>                          # resolve node by ID
roam-cli backlinks <id>                    # nodes linking to ID
roam-cli links <id>                        # forward links from ID
roam-cli graph [--id <id>] [--depth N]     # subgraph or full graph
roam-cli search <query> [--tags t1,t2]     # fuzzy search titles/aliases
roam-cli tags                              # list all tags
roam-cli config                            # configure db path and roam root
```

Global options: `--workspace/-w`, `--format json|table`, `--db`, `--roam-dir`

## Config

Stored in `~/.config/roam-cli/config.toml`. Defaults:

- **db_path**: `~/.emacs.d/.local/cache/org-roam.db`
- **roam_dir**: `~/org/roam`
