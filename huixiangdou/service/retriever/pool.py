from .base import Retriever
from .bm25 import BM25Retriever
from loguru import logger
import time
from .knowledge import KnowledgeRetriever
from .web import WebRetriever
from .bm25 import BM25Retriever
from .inverted import InvertedRetriever
from .base import RetrieveResource
from enum import Enum

class RetrieveMethod(str, Enum):
    """Enumerator of the Distance strategies for calculating distances
    between vectors."""
    KNOWLEDGE = "KNOWLEDGE"
    BM25 = "BM25"
    WEB = "WEB"
    INVERTED = "INVERTED"

class SharedRetrieverPool:
    """A resource pool consist of shared resource: (unique LLM, embedder and reranker) and Retriever instances."""
    def __init__(self,
                 resource: RetrieveResource,
                 cache_size: int = 4):
        self.cache = dict()
        self.cache_size = cache_size
        self.resource = resource
        self.classes = {
            RetrieveMethod.KNOWLEDGE: KnowledgeRetriever,
            RetrieveMethod.WEB: WebRetriever,
            RetrieveMethod.BM25: BM25Retriever,
            RetrieveMethod.INVERTED: InvertedRetriever
        }

    def get(self,
            fs_id: str = 'default',
            work_dir='workdir',
            method:RetrieveMethod=RetrieveMethod.KNOWLEDGE) -> Retriever:
        """Get database by id."""

        newkey = f'{fs_id}-{str(method)}'

        if newkey in self.cache:
            self.cache[newkey]['time'] = time.time()
            return self.cache[newkey]['retriever']

        if len(self.cache) >= self.cache_size:
            # drop the oldest one
            del_key = None
            min_time = time.time()
            for key, value in self.cache.items():
                cur_time = value['time']
                if cur_time < min_time:
                    min_time = cur_time
                    del_key = key

            if del_key is not None:
                del_value = self.cache[del_key]
                self.cache.pop(del_key)
                del del_value['retriever']

        instance = self.classes[method](resource=self.resource, work_dir=work_dir)
        self.cache[newkey] = {'retriever': instance, 'time': time.time()}
        return instance

    def pop(self, fs_id: str):
        """Drop database by id."""

        del_keys = []
        for k, v in self.cache.items():
            if fs_id in k:
                del_keys.append(k)
                
        for del_key in del_keys:
            del_value = self.cache[del_key]
            self.cache.pop(del_key)
            del del_value
