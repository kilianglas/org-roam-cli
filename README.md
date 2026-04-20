# roam-cli

CLI tool for querying org-roam databases.

## Install

```sh
uv tool install /path/to/org-roam-cli
```

## Configure

```sh
roam-cli config
```

Sets the path to the org-roam SQLite database and the org-roam root directory. Configuration can also be overridden per-invocation with `--db` and `--roam-dir`.

## Commands

| Command | Description |
|---|---|
| `roam-cli get <id>` | Resolve a node ID to its file path and metadata. |
| `roam-cli backlinks <id>` | List nodes linking to this ID. |
| `roam-cli links <id>` | List forward links from this ID. |
| `roam-cli graph [--id <id>] [--depth N]` | Adjacency subgraph around a node, or the full workspace graph. |
| `roam-cli search <query> [--tags t1,t2] [--dir prefix] [--threshold N]` | Fuzzy search over titles and aliases. |
| `roam-cli tags` | List all tags in scope. |

## Global flags

- `--workspace/-w <subdir>` — scope queries to a workspace subdirectory.
- `--format json|table` — output format (default `json`).

## Development

```sh
uv sync
uv run pytest
```
