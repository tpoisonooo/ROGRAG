from ...primitive import Query
from ..sql import Entity2ChunkSQL, ChunkSQL
from .base import Retriever, RetrieveResource, RetrieveReply

import os


class InvertedRetriever(Retriever):

    def __init__(self, resource: RetrieveResource, work_dir: str) -> None:
        super().__init__()
        """Init with model device type and config."""
        self.indexer = Entity2ChunkSQL(
            os.path.join(work_dir, 'db_entity2chunk'))
        self.chunkDB = ChunkSQL(file_dir=os.path.join(work_dir, 'db_chunk'))
        self.topk = 10

    async def explore(self, query: Query) -> RetrieveReply:
        """Retrieve chunks by named entity."""
        # reverted index retrieval

        if type(query) is str:
            query = Query(text=query)

        # chunk_id match counter
        chunk_id_score_list = self.indexer.get_chunk_ids(entities=[query.text])
        chunk_id_score_list = chunk_id_score_list[0:self.topk]

        r = RetrieveReply()
        if len(chunk_id_score_list) >= 1:
            for chunk_id, ref_count in chunk_id_score_list:
                c = self.chunkDB.get(_hash=chunk_id)
                if c is None:
                    raise ValueError(f'{chunk_id} not exist')
                r.add_source(c)
        return r
