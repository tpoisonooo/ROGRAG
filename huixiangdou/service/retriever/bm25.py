from ...primitive import Query, BM25Okapi
from .base import Retriever, RetrieveResource, RetrieveReply

import os


class BM25Retriever(Retriever):

    def __init__(self, resource: RetrieveResource, work_dir: str) -> None:
        super().__init__()
        """Init with model device type and config."""
        self.bm25 = BM25Okapi()

        db_code_path = os.path.join(work_dir, 'db_code')
        if os.path.exists(db_code_path):
            self.bm25.load(db_code_path)
            self.inited = True
        else:
            self.inited = False

    async def explore(self, query: Query) -> RetrieveReply:
        """Retrieve chunks by named entity."""
        # reverted index retrieval
        r = RetrieveReply()

        if not self.inited:
            return r

        if type(query) is str:
            query = Query(text=query)

        chunks = self.retriever.bm25.get_top_n(query=query.text)

        for c in chunks:
            r.text_units.append([c._hash, c.content_or_path])
            r.add_source(c)
        return r
