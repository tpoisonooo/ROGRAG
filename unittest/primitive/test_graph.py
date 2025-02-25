import pytest
from huixiangdou.primitive import MemoryGraph, Vertex, Edge, Direction


def test_vertex_creation():
    """测试顶点创建"""
    v = Vertex("1", name="TestVertex")
    assert v.vid == "1"
    assert v.name == "TestVertex"


def test_edge_creation():
    """测试边创建"""
    e = Edge("1", "2", "LIKES")
    assert e.sid == "1"
    assert e.tid == "2"
    assert e.name == "LIKES"


def test_graph_upsert_vertex():
    """测试图谱添加顶点"""
    g = MemoryGraph()
    v = Vertex("1", name="TestVertex")
    g.upsert_vertex(v)
    assert g.has_vertex("1") is True


def test_graph_append_edge():
    """测试图谱添加边"""
    g = MemoryGraph()
    v1 = Vertex("1", name="TestVertex1")
    v2 = Vertex("2", name="TestVertex2")
    g.upsert_vertex(v1)
    g.upsert_vertex(v2)
    e = Edge("1", "2", "LIKES")
    assert g.append_edge(e) is True
    assert g.get_neighbor_edges("1") is not None


def test_graph_get_vertex():
    """测试获取顶点"""
    g = MemoryGraph()
    v = Vertex("1", name="TestVertex")
    g.upsert_vertex(v)
    retrieved_v = g.get_vertex("1")
    assert retrieved_v.vid == "1"
    assert retrieved_v.name == "TestVertex"


def test_graph_del_vertices():
    """测试删除顶点"""
    g = MemoryGraph()
    v = Vertex("1", name="TestVertex")
    g.upsert_vertex(v)
    g.del_vertices("1")
    assert g.has_vertex("1") is False


async def test_graph_del_edges():
    """测试删除边"""
    g = MemoryGraph()
    v1 = Vertex("1", name="TestVertex1")
    v2 = Vertex("2", name="TestVertex2")
    g.upsert_vertex(v1)
    g.upsert_vertex(v2)
    e = Edge("1", "2", "LIKES")
    g.append_edge(e)
    g.del_edges("1", "2", "LIKES")
    assert list(await g.get_neighbor_edges("1")) == []


async def test_graph_search():
    """测试图谱搜索"""
    g = MemoryGraph()
    v1 = Vertex("1", name="TestVertex1")
    v2 = Vertex("2", name="TestVertex2")
    v3 = Vertex("3", name="TestVertex3")
    g.upsert_vertex(v1)
    g.upsert_vertex(v2)
    g.upsert_vertex(v3)
    e1 = Edge("1", "2", "LIKES")
    e2 = Edge("2", "3", "LIKES")
    g.append_edge(e1)
    g.append_edge(e2)
    subgraph = await g.search(["1"], direct=Direction.OUT, depth=2)
    assert subgraph.vertex_count == 3
    assert subgraph.edge_count == 2


def test_graph_viz():
    g = MemoryGraph()
    v1 = Vertex("1", name="TestVertex1")
    v2 = Vertex("2", name="TestVertex2")
    v3 = Vertex("3", name="TestVertex3")
    g.upsert_vertex(v1)
    g.upsert_vertex(v2)
    g.upsert_vertex(v3)
    e1 = Edge("1", "2", "LIKES")
    e2 = Edge("2", "3", "LIKES")
    g.append_edge(e1)
    g.append_edge(e2)
    vis_content = g.graphviz()
    with open('/tmp/graph', 'w') as f:
        f.write(vis_content)


# 运行 pytest 测试
if __name__ == "__main__":
    pytest.main()
