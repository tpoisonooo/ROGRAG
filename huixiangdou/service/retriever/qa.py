from ...primitive import Query, Faiss, Chunk, Pair
from .base import Retriever, RetrieveResource, RetrieveReply
from loguru import logger
import os
from typing import List

class QARetriever(Retriever):

    def __init__(self, resource: RetrieveResource, work_dir: str, **kwargs) -> None:
        super().__init__()
        """Init with model device type and config."""
        self.faiss = Faiss.load_local(os.path.join(work_dir, 'db_qa'))
        self.resource = resource
        self.soybean_dir = os.path.join(work_dir, 'soybean')
        self.varieties = [name.split('.')[0].strip() for name in os.listdir(self.soybean_dir)]

    async def explore(self, query: Query, _: List[Pair]=[]) -> RetrieveReply:
        """Retrieve chunks by named entity."""

        chunk_score_pairs = self.faiss.similarity_search(embedder=self.resource.embedder, query=query, threshold=0.8)
        chunk_score_pairs = chunk_score_pairs[0:1]
        chunks = [c for c, _ in chunk_score_pairs]

        for _, s in chunk_score_pairs:
            logger.warning('qa score {}'.format(s))

        sources = []
        for variety in self.varieties:
            if variety in query.text:
                with open(os.path.join(self.soybean_dir, f'{variety}.txt'), 'r') as f:
                    sources.append(Chunk(content_or_path=f.read(), metadata={"source":variety}))
        
        if chunks:
            merged_content = ""
            for c in chunks:
                merged_content += '问：{} 答：{}\n'.format(c.content_or_path, c.metadata["answer"])
                sources.append(Chunk(content_or_path=merged_content, metadata={"source":"丰登大豆知识库"}))

        r = RetrieveReply(sources=sources)
        return r
