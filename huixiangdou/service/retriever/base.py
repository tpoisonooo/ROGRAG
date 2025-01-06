from abc import ABC, abstractmethod
from ...primitive import Embedder, Reranker, Query, LLM, Chunk, Edge, Vertex, Edge, Vertex
from loguru import logger
from typing import List, Union, Tuple
from ..graph_store import  TuGraphStore
from ..nlu import truncate_list_by_token_size
from ..sql import ChunkSQL
import pytoml
import io
import os
import csv
from ..prompt import rag_prompts, GRAPH_FIELD_SEP
from collections import defaultdict
import pdb

class RetrieveReply:
    def __init__(self, nodes:List[List[str]]=None, relations: List[List[str]]=None, sources:List=None, sub_qa:List=None):
        self.nodes = nodes if nodes is not None else []
        self.relations = relations if relations is not None else []
        self.sources = sources if sources is not None else []
        self.sub_qa = sub_qa if sub_qa is not None else []

    def add_source(self, source: Chunk):
        self.sources.append(source)
        
    def format(self, query:str, language:str="zh_cn"):
        def list_of_list_to_csv(data: List[List[str]]) -> str:
            output = io.StringIO()  
            writer = csv.writer(output)
            writer.writerows(data)
            return output.getvalue()
        
        text_units = [["参考文献", "参考内容"]] + [[os.path.basename(s.metadata['source']), s.content_or_path] for s in self.sources]
        formatted_str = rag_prompts["generate"][language].format(entities=list_of_list_to_csv(self.nodes), 
                                                                 relations=list_of_list_to_csv(self.relations), 
                                                                 search_text=list_of_list_to_csv(text_units), 
                                                                 step_text=self.sub_qa, 
                                                                 input_text=query)
        return formatted_str

    def __repr__(self):
        return self.format(query='')

class RetrieveResource:
    def __init__(self,
                 config_path: str,
                 rerank_topn: int = 4):
        with open(config_path, encoding='utf8') as f:
            fs_config = pytoml.load(f)['store']

        # load text2vec and rerank model
        logger.info('loading test2vec and rerank models')
        self.embedder = Embedder(model_config=fs_config)
        self.reranker = Reranker(model_config=fs_config, topn=rerank_topn)
        self.llm = LLM(config_path=config_path)
        self.graph_store = TuGraphStore(config_path=config_path)
        # self.memory_graph = self.graph_store.get_full_graph()
        self.config_path = config_path

class Retriever(ABC):
    """retriever base class."""

    @abstractmethod
    async def explore(self, query: Union[Query, str]) -> RetrieveReply:
        pass

    @staticmethod
    def fuse(resource:RetrieveResource, query: Query, replies:List[RetrieveReply]) -> RetrieveReply:
        # rerank 重排倒排/bm25/web 等的结果，防止越过最大 token 限制
        if len(replies) == 1:
            return replies[0]
        
        chunks = []
        nodes = []
        relations = []
        for r in replies:
            chunks += r.sources
            nodes += r.nodes
            relations += r.relations
        
        chunks = resource.reranker.rerank(query=query.text, chunks=chunks)
        chunks = truncate_list_by_token_size(list_data=chunks, key=lambda x:x.content_or_path, max_token_size=query.max_token_for_text_unit)

        r = RetrieveReply(nodes=nodes, relations=relations, sources=chunks)
        return r

# for reasoning
class LogicNode:
    def __init__(self, operator, args):
        self.operator = operator
        self.args = args
        self.sub_query = args.get('sub_query', '')
        self.root_query = args.get('root_query', '')

    def __repr__(self):
        params = [f"{k}={v}" for k, v in self.args.items()]
        params_str = ','.join(params)
        return f"{self.operator}({params_str})"

    def to_dict(self):
        return json.loads(self.to_json())

    def to_json(self):
        return json.dumps(obj=self,
                          default=lambda x: x.__dict__, sort_keys=False, indent=2)

    def to_dsl(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def to_std(self, args):
        for key, value in args.items():
            self.args[key] = value
        self.sub_query = args.get('sub_query', '')
        self.root_query = args.get('root_query', '')
    
def graph_elems_to_chunks(items: List[Tuple[Edge, Vertex]], chunkDB: ChunkSQL):
    chunk_ids = []
    for item in items:
        chunk_ids += item.props.get('source_id').split(GRAPH_FIELD_SEP)
    unique_chunk_ids = list(set(chunk_ids))
    
    chunks = [chunkDB.get(_hash=chunk_id) for chunk_id in unique_chunk_ids]
    return chunks

class OpSession:
    def __init__(self):
        # list of <subquery, result>
        self.lf_exec_results: List[Tuple[str, RetrieveReply]] = []

        # op input parameters
        self.param = defaultdict(lambda: defaultdict(set))
        
        # evidences
        self.evidence_chunk_ids = dict()
        self.output_chunk_ids = dict()
        self.evidence_strs = []

    def upsert_evidence(self, sub_query: str, alias:str, items: List[Tuple[Edge, Vertex, str]], sub_answer:str=None):
        # pdb.set_trace()
        chunk_ids = []
        for item in items:
            if isinstance(item, Edge) or isinstance(item, Vertex):
                chunk_ids += item.props.get('source_id').split(GRAPH_FIELD_SEP)
        
        if alias not in self.evidence_chunk_ids:
            self.evidence_chunk_ids[alias] = set(chunk_ids)
        else:
            self.evidence_chunk_ids[alias] |= set(chunk_ids)

        if not sub_answer:
            sub_answer = str(items)
        self.evidence_strs.append({'sub_query':sub_query, 'sub_answer': sub_answer})
    
    def mask_vars(self, var_list: Tuple[str, List[str]]):
        if not var_list:
            return
        
        if isinstance(var_list, str):
            var_list = [var_list]
        
        for var in var_list:
            if var in self.evidence_chunk_ids:
                self.output_chunk_ids[var] = self.evidence_chunk_ids[var]
        
    def to_reply(self, chunkDB: ChunkSQL):
        r = RetrieveReply(sub_qa=self.evidence_strs)
        
        target_chunk_ids = self.output_chunk_ids
        if not target_chunk_ids:
            target_chunk_ids = self.evidence_chunk_ids

        if target_chunk_ids:
            chunk_ids = set()
            for ids in target_chunk_ids.values():
                chunk_ids |= ids
                
            for chunk_id in chunk_ids:
                c = chunkDB.get(_hash=chunk_id)
                r.sources.append(c)
        return r

class OpExecutor(ABC):
    """
    Base class for operators execution.

    Each subclass must implement the execution and judgment functions.
    """
    def __init__(self, resource: RetrieveResource, **kwargs):
        """
        Initializes the operator executor with necessary components.

        Parameters:
            nl_query (str): Natural language query string.
            kg_graph (KgGraph): Knowledge graph object for subsequent queries and parsing.
            schema (SchemaUtils): Semantic structure definition to assist in the parsing process.
            debug_info (dict): Debug information dictionary to record debugging information during parsing.
        """
        super().__init__(**kwargs)
        self.resource = resource
        self.sub_answer = ''

    def split(self, params: Union[str, List[str]]) -> Tuple[List[int], List[str], List[float]]:
        if isinstance(params, str):
            params = [params]
            
        # parse symbol, var and consts
        # -1, var, [99, 22]
        consts = []
        vars_ = []
        signs = []
        for param in params:
            param = param.strip()
            try:
                consts.append(float(param))
            except ValueError:
                if param.startswith('-'):
                    vars_.append(param[1:])
                    signs.append(-1)
                else:
                    vars_.append(param)
                    signs.append(1)
        return signs, vars_, consts
        
    async def run(self, logic_node: LogicNode, op_sess: OpSession):
        """
         Executes the operation based on the given logic node.

         This method should be implemented by subclasses to define how the operation is executed.

         Parameters:
             logic_node (LogicNode): The logic node that defines the operation to execute.
             param (dict): Parameters needed for the execution.

         Returns:
             Union[KgGraph, list]: The result of the operation, which could be a knowledge graph or a list.
         """
        pass

    def is_this_op(self, logic_node: LogicNode) -> bool:
        """
        Determines if this executor is responsible for the given logic node.

        This method should be implemented by subclasses to specify the conditions under which
        this executor can handle the logic node.

        Parameters:
            logic_node (LogicNode): The logic node to check.

        Returns:
            bool: True if this executor can handle the logic node, False otherwise.
        """
        pass
    
