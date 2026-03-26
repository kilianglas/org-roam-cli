from __future__ import annotations

import sqlite3
from collections import deque
from pathlib import Path

from .models import Link, Node, _strip_elisp_quotes


class RoamDB:
    def __init__(self, db_path: Path, roam_dir: Path | None = None):
        self.db_path = db_path
        self.roam_dir = roam_dir
        uri = f"file:{db_path}?mode=ro"
        self.conn = sqlite3.connect(uri, uri=True)
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _workspace_prefix(self, workspace: str | None) -> str | None:
        """Build a file prefix for workspace filtering.

        Handles both plain and elisp-quoted file paths in the DB.
        """
        if workspace and self.roam_dir:
            return str(self.roam_dir / workspace)
        return None

    def _file_like_conditions(self, prefix: str) -> tuple[str, list[str]]:
        """Return SQL condition and params matching files with or without elisp quotes."""
        return "(n.file LIKE ? || '%' OR n.file LIKE ? || '%')", [prefix, f'"{prefix}']

    def get_node(self, node_id: str) -> Node | None:
        row = self.conn.execute(
            """
            SELECT n.id, n.file, n.level, n.title, n.todo, n.properties, n.olp,
                   f.title as file_title
            FROM nodes n
            JOIN files f ON n.file = f.file
            WHERE n.id = ? OR n.id = ?
            """,
            (node_id, f'"{node_id}"'),
        ).fetchone()
        if not row:
            return None

        node_id_clean = _strip_elisp_quotes(row["id"])
        tags = [
            _strip_elisp_quotes(r["tag"])
            for r in self.conn.execute(
                "SELECT tag FROM tags WHERE node_id = ? OR node_id = ?",
                (row["id"], f'"{node_id_clean}"'),
            )
        ]
        aliases = [
            _strip_elisp_quotes(r["alias"])
            for r in self.conn.execute(
                "SELECT alias FROM aliases WHERE node_id = ? OR node_id = ?",
                (row["id"], f'"{node_id_clean}"'),
            )
        ]
        refs = [
            _strip_elisp_quotes(r["ref"])
            for r in self.conn.execute(
                "SELECT ref FROM refs WHERE node_id = ? OR node_id = ?",
                (row["id"], f'"{node_id_clean}"'),
            )
        ]
        return Node(
            id=row["id"],
            file=row["file"],
            level=row["level"],
            title=row["title"],
            todo=row["todo"],
            properties=row["properties"],
            olp=row["olp"],
            file_title=row["file_title"],
            tags=tags,
            aliases=aliases,
            refs=refs,
        )

    def get_backlinks(self, node_id: str) -> list[Link]:
        rows = self.conn.execute(
            """
            SELECT n.id as source_id, n.title as source_title, n.file as source_file,
                   l.dest as dest_id, l.type as link_type
            FROM links l
            JOIN nodes n ON l.source = n.id
            WHERE l.dest = ? OR l.dest = ?
            """,
            (node_id, f'"{node_id}"'),
        ).fetchall()
        return [
            Link(
                source_id=r["source_id"],
                source_title=r["source_title"],
                source_file=r["source_file"],
                dest_id=r["dest_id"],
                link_type=r["link_type"],
            )
            for r in rows
        ]

    def get_forward_links(self, node_id: str) -> list[Link]:
        rows = self.conn.execute(
            """
            SELECT l.source as source_id, n.id as dest_id, n.title as dest_title,
                   n.file as dest_file, l.type as link_type
            FROM links l
            JOIN nodes n ON l.dest = n.id
            WHERE l.source = ? OR l.source = ?
            """,
            (node_id, f'"{node_id}"'),
        ).fetchall()
        return [
            Link(
                source_id=r["source_id"],
                dest_id=r["dest_id"],
                dest_title=r["dest_title"],
                dest_file=r["dest_file"],
                link_type=r["link_type"],
            )
            for r in rows
        ]

    def get_graph(
        self, node_id: str | None = None, depth: int = 2, workspace: str | None = None
    ) -> dict[str, list[str]]:
        """Return adjacency list. If node_id given, BFS to depth. Otherwise full workspace graph."""
        if node_id:
            return self._bfs_graph(node_id, depth)
        return self._full_graph(workspace)

    def _bfs_graph(self, start_id: str, depth: int) -> dict[str, list[str]]:
        graph: dict[str, list[str]] = {}
        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque([(start_id, 0)])
        visited.add(start_id)

        while queue:
            current_id, current_depth = queue.popleft()
            if current_depth > depth:
                break

            neighbors = []
            rows = self.conn.execute(
                """
                SELECT dest FROM links WHERE source = ? OR source = ?
                UNION
                SELECT source FROM links WHERE dest = ? OR dest = ?
                """,
                (current_id, f'"{current_id}"', current_id, f'"{current_id}"'),
            ).fetchall()

            for r in rows:
                neighbor = _strip_elisp_quotes(r[0])
                neighbors.append(neighbor)
                if neighbor not in visited and current_depth < depth:
                    visited.add(neighbor)
                    queue.append((neighbor, current_depth + 1))

            graph[current_id] = neighbors
        return graph

    def _full_graph(self, workspace: str | None) -> dict[str, list[str]]:
        prefix = self._workspace_prefix(workspace)
        if prefix:
            cond, p = self._file_like_conditions(prefix)
            rows = self.conn.execute(
                f"""
                SELECT l.source, l.dest
                FROM links l
                JOIN nodes n ON l.source = n.id
                WHERE {cond}
                """,
                p,
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT source, dest FROM links").fetchall()

        graph: dict[str, list[str]] = {}
        for r in rows:
            src = _strip_elisp_quotes(r[0])
            dst = _strip_elisp_quotes(r[1])
            graph.setdefault(src, []).append(dst)
        return graph

    def search_nodes(
        self,
        workspace: str | None = None,
        tags: list[str] | None = None,
        dir_prefix: str | None = None,
    ) -> list[Node]:
        """Fetch nodes filtered by workspace, tags, and directory prefix.

        Fuzzy matching is applied separately in search.py.
        """
        conditions = []
        params: list[str] = []

        prefix = self._workspace_prefix(workspace)
        if prefix:
            cond, p = self._file_like_conditions(prefix)
            conditions.append(cond)
            params.extend(p)

        if dir_prefix and self.roam_dir:
            full_prefix = str(self.roam_dir / dir_prefix)
            cond, p = self._file_like_conditions(full_prefix)
            conditions.append(cond)
            params.extend(p)

        if tags:
            # Tags may be stored plain or with elisp quotes
            all_tags = tags + [f'"{t}"' for t in tags]
            placeholders = ",".join("?" for _ in all_tags)
            conditions.append(
                f"n.id IN (SELECT node_id FROM tags WHERE tag IN ({placeholders}))"
            )
            params.extend(all_tags)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT n.id, n.file, n.level, n.title, n.todo, n.properties, n.olp,
                   f.title as file_title,
                   GROUP_CONCAT(DISTINCT a.alias) as aliases_str,
                   GROUP_CONCAT(DISTINCT t.tag) as tags_str
            FROM nodes n
            JOIN files f ON n.file = f.file
            LEFT JOIN aliases a ON n.id = a.node_id
            LEFT JOIN tags t ON n.id = t.node_id
            {where}
            GROUP BY n.id
        """
        rows = self.conn.execute(query, params).fetchall()

        nodes = []
        for r in rows:
            aliases_raw = r["aliases_str"] or ""
            tags_raw = r["tags_str"] or ""
            nodes.append(
                Node(
                    id=r["id"],
                    file=r["file"],
                    level=r["level"],
                    title=r["title"],
                    todo=r["todo"],
                    properties=r["properties"],
                    olp=r["olp"],
                    file_title=r["file_title"],
                    aliases=[_strip_elisp_quotes(a) for a in aliases_raw.split(",") if a],
                    tags=[_strip_elisp_quotes(t) for t in tags_raw.split(",") if t],
                )
            )
        return nodes

    def list_tags(self, workspace: str | None = None) -> list[str]:
        prefix = self._workspace_prefix(workspace)
        if prefix:
            cond, p = self._file_like_conditions(prefix)
            rows = self.conn.execute(
                f"""
                SELECT DISTINCT t.tag
                FROM tags t
                JOIN nodes n ON t.node_id = n.id
                WHERE {cond}
                ORDER BY t.tag
                """,
                p,
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT DISTINCT tag FROM tags ORDER BY tag"
            ).fetchall()
        return [_strip_elisp_quotes(r["tag"]) for r in rows]
