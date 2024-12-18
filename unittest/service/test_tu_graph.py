import pytest
from huixiangdou.primitive import MemoryGraph, Vertex, Edge, Direction
from huixiangdou.service import TuGraphStore

def test_graph_search():
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
    
    store = TuGraphStore(config_path='config.ini')
    store.insert_graph(g)
    store.drop()
