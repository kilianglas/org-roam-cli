from roam_cli.db import RoamDB


def test_get_node(test_db):
    db_path, roam_dir = test_db
    with RoamDB(db_path, roam_dir) as db:
        node = db.get_node("node-aaa")
        assert node is not None
        assert node.id == "node-aaa"
        assert node.title == "Alpha Node"
        assert "crypto" in node.tags
        assert "math" in node.tags
        assert "The Alpha" in node.aliases
        assert node.properties["ID"] == "node-aaa"
        assert node.properties["CATEGORY"] == "alpha"


def test_get_node_not_found(test_db):
    db_path, roam_dir = test_db
    with RoamDB(db_path, roam_dir) as db:
        node = db.get_node("nonexistent")
        assert node is None


def test_get_backlinks(test_db):
    db_path, roam_dir = test_db
    with RoamDB(db_path, roam_dir) as db:
        links = db.get_backlinks("node-bbb")
        assert len(links) == 1
        assert links[0].source_id == "node-aaa"


def test_get_forward_links(test_db):
    db_path, roam_dir = test_db
    with RoamDB(db_path, roam_dir) as db:
        links = db.get_forward_links("node-aaa")
        dest_ids = {l.dest_id for l in links}
        assert "node-bbb" in dest_ids
        assert "node-ccc" in dest_ids


def test_get_graph_bfs(test_db):
    db_path, roam_dir = test_db
    with RoamDB(db_path, roam_dir) as db:
        graph = db.get_graph("node-aaa", depth=1)
        assert "node-aaa" in graph
        neighbors = graph["node-aaa"]
        assert "node-bbb" in neighbors
        assert "node-ccc" in neighbors


def test_get_graph_full(test_db):
    db_path, roam_dir = test_db
    with RoamDB(db_path, roam_dir) as db:
        graph = db.get_graph()
        assert len(graph) > 0


def test_search_nodes_all(test_db):
    db_path, roam_dir = test_db
    with RoamDB(db_path, roam_dir) as db:
        nodes = db.search_nodes()
        assert len(nodes) == 4


def test_search_nodes_workspace(test_db):
    db_path, roam_dir = test_db
    with RoamDB(db_path, roam_dir) as db:
        nodes = db.search_nodes(workspace="ws1")
        titles = {n.title for n in nodes}
        assert "Alpha Node" in titles
        assert "Beta Node" in titles
        assert "Gamma Node" not in titles


def test_search_nodes_tags(test_db):
    db_path, roam_dir = test_db
    with RoamDB(db_path, roam_dir) as db:
        nodes = db.search_nodes(tags=["crypto"])
        ids = {n.id for n in nodes}
        assert "node-aaa" in ids
        assert "node-bbb" in ids
        assert "node-ccc" not in ids


def test_list_tags(test_db):
    db_path, roam_dir = test_db
    with RoamDB(db_path, roam_dir) as db:
        tags = db.list_tags()
        assert "crypto" in tags
        assert "math" in tags
        assert "systems" in tags


def test_list_tags_workspace(test_db):
    db_path, roam_dir = test_db
    with RoamDB(db_path, roam_dir) as db:
        tags = db.list_tags(workspace="ws2")
        assert "systems" in tags
        assert "crypto" not in tags
