import json

from click.testing import CliRunner

from roam_cli.cli import cli


def test_cli_get(test_db):
    db_path, roam_dir = test_db
    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "--roam-dir", str(roam_dir), "get", "node-aaa"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "node-aaa"
    assert data["title"] == "Alpha Node"


def test_cli_get_not_found(test_db):
    db_path, roam_dir = test_db
    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "--roam-dir", str(roam_dir), "get", "nonexistent"])
    assert result.exit_code != 0


def test_cli_backlinks(test_db):
    db_path, roam_dir = test_db
    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "--roam-dir", str(roam_dir), "backlinks", "node-bbb"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["source_id"] == "node-aaa"


def test_cli_links(test_db):
    db_path, roam_dir = test_db
    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "--roam-dir", str(roam_dir), "links", "node-aaa"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) >= 2


def test_cli_search(test_db):
    db_path, roam_dir = test_db
    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "--roam-dir", str(roam_dir), "search", "Alpha"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) > 0
    assert data[0]["title"] == "Alpha Node"


def test_cli_tags(test_db):
    db_path, roam_dir = test_db
    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "--roam-dir", str(roam_dir), "tags"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "crypto" in data


def test_cli_graph(test_db):
    db_path, roam_dir = test_db
    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "--roam-dir", str(roam_dir), "graph", "--id", "node-aaa", "--depth", "1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "node-aaa" in data


def test_cli_workspace_filter(test_db):
    db_path, roam_dir = test_db
    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "--roam-dir", str(roam_dir), "-w", "ws1", "search", "Node"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    for item in data:
        assert "ws1" in item["file"]
