"""TuGraph store."""
import json
import pytoml
import pdb
from abc import ABC
from typing import Any, Generator, Iterator, List, Optional, Tuple
from ..primitive import Direction, Edge, MemoryGraph, Graph, Vertex
from loguru import logger
"""TuGraph Connector."""
from typing import Dict, Generator, cast


def escape_quotes(value: str) -> str:
    """Escape single and double quotes in a string for queries."""
    if value is not None:
        value = value.replace("'", "").replace('"', "").replace("\\", "")
        return value
    return ""


class TuGraphConnector:
    """TuGraph connector."""

    db_type: str = "tugraph"
    driver: str = "bolt"
    dialect: str = "tugraph"

    def __init__(self, driver, graph):
        """Initialize the connector with a Neo4j driver."""
        self._driver = driver
        self._schema = None
        self._graph = graph
        self._session = None

    def create_graph(self, graph_name: str) -> None:
        """Create a new graph."""
        # run the query to get vertex labels
        try:
            with self._driver.session(database="default") as session:
                graph_list = session.run("CALL dbms.graph.listGraphs()").data()
                exists = any(item["graph_name"] == graph_name
                             for item in graph_list)
                if not exists:
                    session.run(
                        f"CALL dbms.graph.createGraph('{graph_name}', '', 2048)"
                    )
        except Exception as e:
            raise Exception(f"Failed to create graph '{graph_name}': {str(e)}")

    def delete_graph(self, graph_name: str) -> None:
        """Delete a graph."""
        with self._driver.session(database="default") as session:
            graph_list = session.run("CALL dbms.graph.listGraphs()").data()
            exists = any(item["graph_name"] == graph_name
                         for item in graph_list)
            if exists:
                session.run(f"Call dbms.graph.deleteGraph('{graph_name}')")

    @classmethod
    def from_uri_db(cls, host: str, port: int, user: str, pwd: str,
                    db_name: str) -> "TuGraphConnector":
        """Create a new TuGraphConnector from host, port, user, pwd, db_name."""
        try:
            from neo4j import GraphDatabase

            db_url = f"{cls.driver}://{host}:{str(port)}"
            driver = GraphDatabase.driver(db_url, auth=(user, pwd))
            driver.verify_connectivity()
            return cast(TuGraphConnector, cls(driver=driver, graph=db_name))

        except ImportError as err:
            raise ImportError(
                "neo4j package is not installed, please install it with "
                "`pip install neo4j`") from err

    def get_table_names(self) -> Dict[str, List[str]]:
        """Get all table names from the TuGraph by Neo4j driver."""
        # run the query to get vertex labels
        with self._driver.session(database=self._graph) as session:
            v_result = session.run("CALL db.vertexLabels()").data()
            v_data = [table_name["label"] for table_name in v_result]

            # run the query to get edge labels
            e_result = session.run("CALL db.edgeLabels()").data()
            e_data = [table_name["label"] for table_name in e_result]
            return {"vertex_tables": v_data, "edge_tables": e_data}

    def get_grants(self):
        """Get grants."""
        return []

    def get_collation(self):
        """Get collation."""
        return "UTF-8"

    def get_charset(self):
        """Get character_set of current database."""
        return "UTF-8"

    def table_simple_info(self):
        """Get table simple info."""
        return []

    def close(self):
        """Close the Neo4j driver."""
        self._driver.close()

    def run(self, query: str, fetch: str = "all") -> List:
        """Run query."""
        with self._driver.session(database=self._graph) as session:
            try:
                result = session.run(query)
                return list(result)
            except Exception as e:
                raise Exception(f"Query execution failed: {e} {query}")

    def run_stream(self, query: str) -> Generator:
        """Run GQL."""
        with self._driver.session(database=self._graph) as session:
            result = session.run(query)
            yield from result

    def get_columns(self,
                    table_name: str,
                    table_type: str = "vertex") -> List[Dict]:
        """Get fields about specified graph.

        Args:
            table_name (str): table name (graph name)
            table_type (str): table type (vertex or edge)
        Returns:
            columns: List[Dict], which contains name: str, type: str,
                default_expression: str, is_in_primary_key: bool, comment: str
                eg:[{'name': 'id', 'type': 'int', 'default_expression': '',
                'is_in_primary_key': True, 'comment': 'id'}, ...]
        """
        with self._driver.session(database=self._graph) as session:
            data = []
            result = None
            if table_type == "vertex":
                result = session.run(
                    f"CALL db.getVertexSchema('{table_name}')").data()
            else:
                result = session.run(
                    f"CALL db.getEdgeSchema('{table_name}')").data()
            schema_info = json.loads(result[0]["schema"])
            for prop in schema_info.get("properties", []):
                prop_dict = {
                    "name":
                    prop["name"],
                    "type":
                    prop["type"],
                    "default_expression":
                    "",
                    "is_in_primary_key":
                    bool("primary" in schema_info
                         and prop["name"] == schema_info["primary"]),
                    "comment":
                    prop["name"],
                }
                data.append(prop_dict)
            return data

    def get_indexes(self,
                    table_name: str,
                    table_type: str = "vertex") -> List[Dict]:
        """Get table indexes about specified table.

        Args:
            table_name:(str) table name
            table_type:(str）'vertex' | 'edge'
        Returns:
            List[Dict]:eg:[{'name': 'idx_key', 'column_names': ['id']}]
        """
        # [{'name':'id','column_names':['id']}]
        with self._driver.session(database=self._graph) as session:
            result = session.run(
                f"CALL db.listLabelIndexes('{table_name}','{table_type}')"
            ).data()
            transformed_data = []
            for item in result:
                new_dict = {
                    "name": item["field"],
                    "column_names": [item["field"]]
                }
                transformed_data.append(new_dict)
            return transformed_data

    @classmethod
    def is_graph_type(cls) -> bool:
        """Return whether the connector is a graph database connector."""
        return True


class GraphStore(ABC):

    def __init__(self):
        pass


class TuGraphStore(GraphStore):
    """TuGraph graph store."""

    def __init__(self, config_path: str) -> None:
        """Initialize the TuGraphStore with connection details."""
        # utf-8
        with open(config_path, encoding="utf-8") as f:
            config = pytoml.load(f)['tugraph']
            self.host = config.get('host', '127.0.0.1')
            self.port = config.get('port', 7072)
            self.username = config.get('username', 'admin')
            self.password = config.get('password', '73@TuGraph')
            self.name = config.get('name', 'HuixiangDou')
        self._summary_enabled = True
        self._vertex_type = "entity"
        self._edge_type = "relation"

        self.conn = TuGraphConnector.from_uri_db(host=self.host,
                                                 port=self.port,
                                                 user=self.username,
                                                 pwd=self.password,
                                                 db_name=self.name)
        self._create_graph(self.name)

    def get_vertex_type(self) -> str:
        """Get the vertex type."""
        return self._vertex_type

    def get_edge_type(self) -> str:
        """Get the edge type."""
        return self._edge_type

    def _create_graph(self, graph_name: str):
        self.conn.create_graph(graph_name=graph_name)
        self._create_schema()

    def _check_label(self, elem_type: str):
        result = self.conn.get_table_names()
        if elem_type == "vertex":
            return self._vertex_type in result["vertex_tables"]
        if elem_type == "edge":
            return self._edge_type in result["edge_tables"]

    def _add_vertex_index(self, field_name):
        gql = f"CALL db.addIndex('{self._vertex_type}', '{field_name}', false)"
        self.conn.run(gql)

    def _create_schema(self):
        if not self._check_label("vertex"):
            create_vertex_gql = (
                f"CALL db.createLabel("
                f"'vertex', '{self._vertex_type}', "
                f"'id', ['id','string',false],"
                f"['name','string',false],"
                f"['entity_type','string',false],"
                # f"['_document_id','string',true],"
                f"['source_id','string',true],"
                f"['community_id','string',true],"
                f"['description','string',true])")
            logger.info(create_vertex_gql)
            self.conn.run(create_vertex_gql)
            self._add_vertex_index("community_id")

        if not self._check_label("edge"):
            create_edge_gql = f"""CALL db.createLabel(
                'edge', '{self._edge_type}',
                '[["{self._vertex_type}",
                "{self._vertex_type}"]]',
                ["id",'STRING',false],
                ["name",'STRING',false],
                ["source_id",'STRING',true],
                ["description",'STRING',true],
                ["weight",'INT32',false])"""
            logger.info(create_edge_gql)
            self.conn.run(create_edge_gql)

    def _format_query_data(self, data, white_prop_list: List[str]):
        nodes_list = []
        rels_list: List[Any] = []
        _white_list = white_prop_list
        from neo4j import graph

        def get_filtered_properties(properties, white_list):
            return {
                key: value
                for key, value in properties.items()
                if (not key.startswith("_") and key not in ["id", "name"])
                or key in white_list
            }

        def process_node(node: graph.Node):
            node_id = node._properties.get("id")
            node_name = node._properties.get("name")

            node_properties = get_filtered_properties(node._properties,
                                                      _white_list)
            nodes_list.append({
                "id": node_id,
                "name": node_name,
                "properties": node_properties
            })

        def process_relationship(rel: graph.Relationship):
            name = rel._properties.get("name", "")
            rel_nodes = rel.nodes
            src_id = rel_nodes[0]._properties.get("id")
            tgt_id = rel_nodes[1]._properties.get("id")
            for node in rel_nodes:
                process_node(node)
            edge_properties = get_filtered_properties(rel._properties,
                                                      _white_list)
            if not any(
                    existing_edge.get("name") == name
                    and existing_edge.get("src_id") == src_id
                    and existing_edge.get("tgt_id") == tgt_id
                    for existing_edge in rels_list):
                rels_list.append({
                    "src_id": src_id,
                    "tgt_id": tgt_id,
                    "name": name,
                    "properties": edge_properties,
                })

        def process_path(path: graph.Path):
            for rel in path.relationships:
                process_relationship(rel)

        def process_other(value):
            if not any(
                    existing_node.get("id") == "json_node"
                    for existing_node in nodes_list):
                nodes_list.append({
                    "id": "json_node",
                    "name": "json_node",
                    "properties": {
                        "description": value
                    },
                })

        for record in data:
            for key in record.keys():
                value = record[key]
                if isinstance(value, graph.Node):
                    process_node(value)
                elif isinstance(value, graph.Relationship):
                    process_relationship(value)
                elif isinstance(value, graph.Path):
                    process_path(value)
                else:
                    process_other(value)
        nodes = [
            Vertex(node["id"], node["name"], **node["properties"])
            for node in nodes_list
        ]
        rels = [
            Edge(edge["src_id"], edge["tgt_id"], edge["name"],
                 **edge["properties"]) for edge in rels_list
        ]
        return {"nodes": nodes, "edges": rels}

    def get_config(self):
        """Get the graph store config."""
        return self._config

    def get_triplets(self, subj: str) -> List[Tuple[str, str]]:
        """Get triplets."""
        query = (
            f"MATCH (n1:{self._vertex_type})-[r]->(n2:{self._vertex_type}) "
            f'WHERE n1.id = "{subj}" RETURN r.id as rel, n2.id as obj;')
        data = self.conn.run(query)
        return [(record["rel"], record["obj"]) for record in data]

    def insert_triplet(self, subj: str, rel: str, obj: str) -> None:
        """Add triplet."""
        subj_escaped = escape_quotes(subj)
        rel_escaped = escape_quotes(rel)
        obj_escaped = escape_quotes(obj)

        node_query = f"""CALL db.upsertVertex(
            '{self._vertex_type}',
            [{{id:'{subj_escaped}',name:'{subj_escaped}'}},
            {{id:'{obj_escaped}',name:'{obj_escaped}'}}])"""
        edge_query = f"""CALL db.upsertEdge(
            '{self._edge_type}',
            {{type:"{self._vertex_type}",key:"src_id"}},
            {{type:"{self._vertex_type}", key:"tgt_id"}},
            [{{sid:"{subj_escaped}",
            tid: "{obj_escaped}",
            id:"{rel_escaped}",
            name: "{rel_escaped}"}}])"""
        self.conn.run(query=node_query)
        self.conn.run(query=edge_query)

    def insert_graph(self, graph: Graph) -> None:
        """Add graph."""
        logger.info('insert {} edges'.format(str(graph.edge_count)))
        logger.info('insert {} nodes'.format(str(graph.vertex_count)))

        nodes: Iterator[Vertex] = graph.vertices()
        edges: Iterator[Edge] = graph.edges()
        node_list = []
        edge_list = []

        def escape_string(s):
            s = s.replace('\\', '\\\\')
            s = s.replace('"', '\\"')
            s = s.replace('\n', '\\n')
            s = s.replace('\t', '\\t')
            return s

        def parser(node_list):
            formatted_nodes = [
                "{" + ", ".join(f'{k}: "{escape_string(v)}"' if isinstance(
                    v, str) else f"{k}: {v}" for k, v in node.items()) + "}"
                for node in node_list
            ]
            return f"""{', '.join(formatted_nodes)}"""

        def insert_node(nodes: List):
            try:
                node_query = (
                    f"""CALL db.upsertVertex("{self._vertex_type}", [{parser(nodes)}])"""
                )
                self.conn.run(query=node_query)
            except Exception as e1:
                logger.error(e1)
                micro_query = ''
                for index, node in enumerate(nodes):
                    try:
                        micro_query = f"""CALL db.upsertVertex("{self._vertex_type}", [{parser([node])}])"""
                        logger.info(f'{index}, {micro_query}')
                        self.conn.run(query=micro_query)
                    except Exception as e2:
                        logger.error(micro_query)
                        with open('errornode.txt', 'a') as f:
                            f.write(micro_query)
                            f.write(str(e2))
                            f.write('\n')
                        continue

        for node in nodes:
            node_list.append({
                "id":
                escape_quotes(node.vid),
                "name":
                escape_quotes(node.name),
                "description":
                escape_quotes(node.get_prop("description")),
                # "_document_id": "0",
                "source_id":
                node.get_prop("source_id"),
                "entity_type":
                escape_quotes(node.get_prop("entity_type")) or "",
                "_community_id":
                "0"
            })
            if len(node_list) >= 1024:
                insert_node(nodes=node_list)
                node_list = []
        if len(node_list) > 0:
            insert_node(nodes=node_list)

        def insert_edge(edges: List):
            try:
                edge_query = f"""CALL db.upsertEdge("{self._edge_type}",{{type:"{self._vertex_type}", key:"src_id"}}, {{type:"{self._vertex_type}", key:"tgt_id"}},[{parser(edges)}])"""
                self.conn.run(query=edge_query)
            except Exception as e1:
                logger.error(e1)

                for index, edge in enumerate(edges):
                    micro_query = ''
                    try:
                        micro_query = f"""CALL db.upsertEdge("{self._edge_type}",{{type:"{self._vertex_type}", key:"src_id"}}, {{type:"{self._vertex_type}", key:"tgt_id"}},[{parser([edge])}])"""
                        logger.info(f'{index}, {micro_query}')
                        self.conn.run(query=micro_query)
                    except Exception as e2:
                        logger.error(micro_query)
                        with open('erroredge.txt', 'a') as f:
                            f.write(micro_query)
                            f.write(str(e2))
                            f.write('\n')
                        continue

        for edge in edges:
            edge_list.append({
                "src_id":
                escape_quotes(edge.sid),
                "tgt_id":
                escape_quotes(edge.tid),
                "id":
                escape_quotes(edge.name),
                "name":
                escape_quotes(edge.name),
                "description":
                escape_quotes(edge.get_prop("description")),
                "source_id":
                escape_quotes(edge.get_prop("source_id")),
                "weight":
                int(edge.get_prop("weight") or 0)
            })
            if len(edge_list) >= 1024:
                insert_edge(edges=edge_list)
                edge_list = []
        if len(edge_list) > 0:
            insert_edge(edges=edge_list)

    def truncate(self):
        """Truncate Graph."""
        gql = "MATCH (n) DELETE n"
        self.conn.run(gql)

    def drop(self):
        """Delete Graph."""
        self.conn.delete_graph(self.name)

    def delete_triplet(self, sub: str, rel: str, obj: str) -> None:
        """Delete triplet."""
        del_query = (f"MATCH (n1:{self._vertex_type} {{id:'{sub}'}})"
                     f"-[r:{self._edge_type} {{id:'{rel}'}}]->"
                     f"(n2:{self._vertex_type} {{id:'{obj}'}}) DELETE n1,n2,r")
        self.conn.run(query=del_query)

    def get_schema(self, refresh: bool = False) -> str:
        """Get the schema of the graph store."""
        query = "CALL dbms.graph.getGraphSchema()"
        data = self.conn.run(query=query)
        schema = data[0]["schema"]
        return schema

    def get_full_graph(self) -> Graph:
        """Get full graph."""
        inner_graph = self.query(f"MATCH (n)-[r]-(m) RETURN n,r,m",
                                 white_list=["community_id"])
        return inner_graph

    def explore(
        self,
        subs: List[str],
        direct: Direction = Direction.BOTH,
        depth: Optional[int] = None,
        fan: Optional[int] = None,
        limit: Optional[int] = 256,
    ) -> Graph:
        """Explore the graph from given subjects up to a depth."""
        if not subs:
            return MemoryGraph()

        if fan is not None:
            raise ValueError(
                "Fan functionality is not supported at this time.")
        else:
            depth_string = f"1..{depth}"
            if depth is None:
                depth_string = ".."

            limit_string = f"LIMIT {limit}"
            if limit is None:
                limit_string = ""
            if direct.name == "OUT":
                rel = f"-[r:{self._edge_type}*{depth_string}]->"
            elif direct.name == "IN":
                rel = f"<-[r:{self._edge_type}*{depth_string}]-"
            else:
                rel = f"-[r:{self._edge_type}*{depth_string}]-"

            query = (f"MATCH p=(n:{self._vertex_type})"
                     f"{rel}(m:{self._vertex_type}) "
                     f"WHERE n.id IN {subs} RETURN p {limit_string}")

            logger.info(f'{__file__} {query}')
            return self.query(query)

    async def get_neighbor_edges(
        self,
        vid: str,
        direction: Direction = Direction.BOTH,
        limit: Optional[int] = None,
    ) -> Iterator[Edge]:
        vid = escape_quotes(vid)
        memory_graph = self.explore(subs=[vid], depth=1)
        return await memory_graph.get_neighbor_edges(vid=vid,
                                                     direction=direction,
                                                     limit=limit)

    async def get_connections(
        self,
        sid: str,
        tid: str,
        direction: Direction = Direction.BOTH,
        limit: Optional[int] = None,
    ) -> Iterator[Edge]:
        sid = escape_quotes(sid)
        tid = escape_quotes(tid)
        depth_string = '1..2'
        query = f'MATCH p=(n:{self._vertex_type})-[r:{self._edge_type}*{depth_string}]-(m:entity) WHERE n.id="{sid}" AND m.id="{tid}" RETURN p'
        logger.debug(query)
        memory_graph = self.query(query)
        return memory_graph.edges()

    def get_node(self, vid: str) -> Vertex:
        vid = escape_quotes(vid)
        query = f"MATCH (n:{self._vertex_type}) WHERE n.id IN {[vid]} RETURN n"
        memory_graph = self.query(query)
        return memory_graph.get_node(vid=vid)

    def get_edge(self, sid: str, tid: str) -> Optional[Edge]:
        sid = escape_quotes(sid)
        tid = escape_quotes(tid)
        query = f'MATCH p=(n:{self._vertex_type})-[r:{self._edge_type}]-(m:entity) WHERE n.id="{sid}" AND m.id="{tid}" RETURN p'
        memory_graph = self.query(query)
        return memory_graph.get_edge(sid=sid, tid=tid)

    async def get_nodes_by_edge(self, edge_name: str) -> Tuple[Edge, Edge]:
        edge_name = escape_quotes(edge_name)

        query = f'MATCH (n:entity)-[r:relation]-(m:entity) WHERE r.name = "{edge_name}" RETURN m,n'
        memory_graph = self.query(query=query)
        vertex_iter = memory_graph.vertices()
        n0 = None
        n1 = None
        try:
            n0 = next(vertex_iter)
            n1 = next(vertex_iter)
            return n0, n1
        except Exception as e:
            return n0, n1

    async def node_degree(self, vid: str) -> int:
        vid = escape_quotes(vid)
        query = f'MATCH (n:entity)-[r:relation*1..1]-(m:entity) WHERE n.id = "{vid}" RETURN count(r)'
        result = self.conn.run(query=query)
        return result[0].get('count(r)')

    async def edge_degree(self, sid: str, tid: str) -> int:
        return await self.node_degree(sid) + await self.node_degree(tid)

    def query(self, query: str, **args) -> MemoryGraph:
        """Execute a query on graph."""
        result = self.conn.run(query=query)
        white_list = args.get("white_list", [])
        graph = self._format_query_data(result, white_list)
        mg = MemoryGraph()
        for vertex in graph["nodes"]:
            mg.upsert_vertex(vertex)
        for edge in graph["edges"]:
            mg.append_edge(edge)
        return mg

    # def stream_query(self, query: str) -> Generator[Graph, None, None]:
    #     """Execute a stream query."""
    #     from neo4j import graph

    #     for record in self.conn.run_stream(query):
    #         mg = MemoryGraph()
    #         for key in record.keys():
    #             value = record[key]
    #             if isinstance(value, graph.Node):
    #                 node_id = value._properties["id"]
    #                 description = value._properties["description"]
    #                 vertex = Vertex(node_id, name=node_id, description=description)
    #                 mg.upsert_vertex(vertex)
    #             elif isinstance(value, graph.Relationship):
    #                 rel_nodes = value.nodes
    #                 prop_id = value._properties["id"]
    #                 src_id = rel_nodes[0]._properties["id"]
    #                 dst_id = rel_nodes[1]._properties["id"]
    #                 description = value._properties["description"]
    #                 edge = Edge(src_id, dst_id, name=prop_id, description=description)
    #                 mg.append_edge(edge)
    #             elif isinstance(value, graph.Path):
    #                 nodes = list(record["p"].nodes)
    #                 rels = list(record["p"].relationships)
    #                 formatted_path = []
    #                 for i in range(len(nodes)):
    #                     formatted_path.append(
    #                         {
    #                             "id": nodes[i]._properties["id"],
    #                             "description": nodes[i]._properties["description"],
    #                         }
    #                     )
    #                     if i < len(rels):
    #                         formatted_path.append(
    #                             {
    #                                 "id": rels[i]._properties["id"],
    #                                 "description": rels[i]._properties["description"],
    #                             }
    #                         )
    #                 for i in range(0, len(formatted_path), 2):
    #                     mg.upsert_vertex(
    #                         Vertex(
    #                             formatted_path[i]["id"],
    #                             name=formatted_path[i]["id"],
    #                             description=formatted_path[i]["description"],
    #                         )
    #                     )
    #                     if i + 2 < len(formatted_path):
    #                         mg.append_edge(
    #                             Edge(
    #                                 formatted_path[i]["id"],
    #                                 formatted_path[i + 2]["id"],
    #                                 name=formatted_path[i + 1]["id"],
    #                                 description=formatted_path[i + 1]["description"],
    #                             )
    #                         )
    #             else:
    #                 vertex = Vertex("json_node", name="json_node", description=value)
    #                 mg.upsert_vertex(vertex)
    #         yield mg


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'drop':
        store = TuGraphStore(config_path='config.ini')
        user_input = input("Input Y/n to drop the database? (Y/n)\n")
        if user_input == 'Y':
            logger.info('Remove the database.')
            store.drop()
    else:
        print(
            "`python3 -m huixiangdou.service.graph_store drop` to drop the graph."
        )
