from ...primitive import Query, Faiss
from .base import Retriever, RetrieveResource, RetrieveReply
from ..nlu import truncate_list_by_token_size

import os


class DenseRetriever(Retriever):

    def __init__(self, resource: RetrieveResource, work_dir: str) -> None:
        super().__init__()
        """Init with model device type and config."""
        dense_path = os.path.join(work_dir, 'db_dense')
        self.faiss = Faiss.load(dense_path)
        self.resource = resource

    async def explore(self, query: Query) -> RetrieveReply:
        """Retrieve chunks by named entity."""
        chunks = self.faiss.similarity_search(embedder=self.resource.embedder,
                                              query=query)
        # (self, embedder: Embedder, query: Query, threshold: float = -1):

        chunks = self.resource.reranker.rerank(query=query.text, chunks=chunks)
        chunks = truncate_list_by_token_size(
            list_data=chunks,
            key=lambda x: x.content_or_path,
            max_token_size=query.max_token_for_text_unit)

        r = RetrieveReply(sources=chunks)
        return r
