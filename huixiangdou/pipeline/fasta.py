from ..primitive import (Chunk, Embedder, Faiss, BM25Okapi)
from ..service.sql import Entity2ChunkSQL
from typing import List
import os

class Fasta:
    
    def __init__(self, work_dir: str, embedder: Embedder):
        self.work_dir = work_dir
        self.embedder = embedder
        self.index_dir = os.path.join(self.work_dir, 'db_fasta_reverted_index')
        os.makedirs(self.index_dir, exist_ok=True)

    async def build_inverted_index(chunks: List[Chunk], ner_file: str):
        # 倒排索引 retrieve 建库
        entities = []
        with open(ner_file) as f:
            entities = json.load(f)
        
        time0 = time.time()
        map_entity2chunks = dict()
        indexer = Entity2ChunkSQL(file_dir=self.index_dir)
        indexer.clean()
        indexer.set_entity(entities=entities)
        
        print('build inverted indexer')
        # build inverted index
        for chunk_id, chunk in enumerate(chunks):
            if chunk.modal != 'text' and chunk.modal != 'fasta':
                continue
            entity_ids = indexer.parse(text=chunk.content_or_path)
            for entity_id in entity_ids:
                if entity_id not in map_entity2chunks:
                    map_entity2chunks[entity_id] = [chunk_id]
                else:
                    map_entity2chunks[entity_id].append(chunk_id)

        for entity_id, chunk_indexes in map_entity2chunks.items():
            indexer.insert_relation(eid = entity_id, chunk_ids=chunk_indexes)
        del indexer
        time1 = time.time()
        logger.info('Timecost for string match {}'.format(time1-time0))
        
    async def init(self, ner_path: str, file_dir: str):
        fasta_chunks = []
        for item in os.listdir(file_dir):
            fasta_file_path = os.path.join(file_dir, item)

            with open(fasta_file_path, 'r') as file:
                content = file.read()
                content = content.strip()[1:-1]
                for line in content.split(','):
                    chunk_text = line.strip()[1:-1]
                    chunk = Chunk(
                        content_or_path = chunk_text,
                        metadata = {"source": chunk_text, "read": chunk_text},
                        modal = 'fasta',
                    )
                    fasta_chunks.append(chunk)
        
        fasta_feature_dir = os.path.join(self.work_dir, "db_dense_fasta")
        os.makedirs(fasta_feature_dir, exist_ok=True)
        Faiss.save_local(folder_path=fasta_feature_dir, chunks=fasta_chunks, embedder=self.embedder)
        
        await self.build_inverted_index(chunks=chunks, ner_file=ner_path)
