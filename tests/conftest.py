import sqlite3
from pathlib import Path

import pytest


@pytest.fixture
def test_db(tmp_path):
    """Create a test org-roam SQLite database with sample data."""
    db_path = tmp_path / "org-roam.db"
    roam_dir = tmp_path / "roam"
    roam_dir.mkdir()
    (roam_dir / "ws1").mkdir()
    (roam_dir / "ws2").mkdir()

    conn = sqlite3.connect(str(db_path))

    conn.executescript("""
        CREATE TABLE files (file UNIQUE PRIMARY KEY, title, hash NOT NULL, atime NOT NULL, mtime NOT NULL);
        CREATE TABLE nodes (id NOT NULL PRIMARY KEY, file NOT NULL, level NOT NULL, pos NOT NULL, todo, priority, scheduled text, deadline text, title, properties, olp, FOREIGN KEY (file) REFERENCES files (file) ON DELETE CASCADE);
        CREATE TABLE aliases (node_id NOT NULL, alias, FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE);
        CREATE TABLE citations (node_id NOT NULL, cite_key NOT NULL, pos NOT NULL, properties, FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE);
        CREATE TABLE refs (node_id NOT NULL, ref NOT NULL, type NOT NULL, FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE);
        CREATE TABLE tags (node_id NOT NULL, tag, FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE);
        CREATE TABLE links (pos NOT NULL, source NOT NULL, dest NOT NULL, type NOT NULL, properties NOT NULL, FOREIGN KEY (source) REFERENCES nodes (id) ON DELETE CASCADE);
    """)

    # Use elisp-quoted strings like the real DB
    ws1 = str(roam_dir / "ws1")
    ws2 = str(roam_dir / "ws2")

    files = [
        (f'"{ws1}/file_a.org"', '"File A"', "hash1", 1000, 1000),
        (f'"{ws1}/file_b.org"', '"File B"', "hash2", 1000, 1000),
        (f'"{ws2}/file_c.org"', '"File C"', "hash3", 1000, 1000),
    ]
    conn.executemany("INSERT INTO files VALUES (?,?,?,?,?)", files)

    nodes = [
        ('"node-aaa"', f'"{ws1}/file_a.org"', 0, 1, None, None, None, None, '"Alpha Node"', '(("ID" . "node-aaa") ("CATEGORY" . "alpha"))', None),
        ('"node-bbb"', f'"{ws1}/file_b.org"', 0, 1, None, None, None, None, '"Beta Node"', '(("ID" . "node-bbb"))', None),
        ('"node-ccc"', f'"{ws2}/file_c.org"', 0, 1, None, None, None, None, '"Gamma Node"', '(("ID" . "node-ccc"))', None),
        ('"node-ddd"', f'"{ws1}/file_a.org"', 1, 100, None, None, None, None, '"Delta Heading"', '(("ID" . "node-ddd"))', '("Alpha Node")'),
    ]
    conn.executemany("INSERT INTO nodes VALUES (?,?,?,?,?,?,?,?,?,?,?)", nodes)

    tags = [
        ('"node-aaa"', '"crypto"'),
        ('"node-aaa"', '"math"'),
        ('"node-bbb"', '"crypto"'),
        ('"node-ccc"', '"systems"'),
    ]
    conn.executemany("INSERT INTO tags VALUES (?,?)", tags)

    aliases = [
        ('"node-aaa"', '"The Alpha"'),
        ('"node-bbb"', '"B Node"'),
    ]
    conn.executemany("INSERT INTO aliases VALUES (?,?)", aliases)

    refs = [
        ('"node-aaa"', '"https://example.com"', '"url"'),
    ]
    conn.executemany("INSERT INTO refs VALUES (?,?,?)", refs)

    links = [
        (10, '"node-aaa"', '"node-bbb"', '"id"', '(:outline nil)'),
        (20, '"node-aaa"', '"node-ccc"', '"id"', '(:outline nil)'),
        (30, '"node-bbb"', '"node-ccc"', '"id"', '(:outline nil)'),
        (40, '"node-ddd"', '"node-aaa"', '"id"', '(:outline nil)'),
    ]
    conn.executemany("INSERT INTO links VALUES (?,?,?,?,?)", links)

    conn.commit()
    conn.close()

    return db_path, roam_dir
