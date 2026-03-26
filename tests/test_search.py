from roam_cli.db import RoamDB
from roam_cli.search import fuzzy_search


def test_fuzzy_search_exact(test_db):
    db_path, roam_dir = test_db
    with RoamDB(db_path, roam_dir) as db:
        nodes = db.search_nodes()
        results = fuzzy_search("Alpha", nodes)
        assert len(results) > 0
        assert results[0].node.title == "Alpha Node"
        assert results[0].score >= 90


def test_fuzzy_search_partial(test_db):
    db_path, roam_dir = test_db
    with RoamDB(db_path, roam_dir) as db:
        nodes = db.search_nodes()
        results = fuzzy_search("Beta", nodes)
        assert len(results) > 0
        assert any(r.node.title == "Beta Node" for r in results)


def test_fuzzy_search_alias(test_db):
    db_path, roam_dir = test_db
    with RoamDB(db_path, roam_dir) as db:
        nodes = db.search_nodes()
        results = fuzzy_search("The Alpha", nodes)
        assert len(results) > 0
        assert results[0].node.id == "node-aaa"


def test_fuzzy_search_no_match(test_db):
    db_path, roam_dir = test_db
    with RoamDB(db_path, roam_dir) as db:
        nodes = db.search_nodes()
        results = fuzzy_search("xyznonexistent", nodes, threshold=80)
        assert len(results) == 0


def test_fuzzy_search_limit(test_db):
    db_path, roam_dir = test_db
    with RoamDB(db_path, roam_dir) as db:
        nodes = db.search_nodes()
        results = fuzzy_search("Node", nodes, limit=2)
        assert len(results) <= 2
