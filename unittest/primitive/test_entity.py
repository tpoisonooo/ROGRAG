import os
import pdb
import shutil
from huixiangdou.service import Entity2ChunkSQL
from huixiangdou.primitive import Chunk


def test_entity_build_and_query():
    entities = ['HuixiangDou', 'WeChat']
    work_dir = '/tmp/entity'

    indexer = Entity2ChunkSQL(work_dir)
    indexer.clean()

    c0 = Chunk(content_or_path='How to deploy HuixiangDou on wechaty ?')
    c1 = Chunk(content_or_path='do you know what huixiangdou means ?')
    chunks = [c0, c1]

    indexer.insert_relation(entity=entities[0], chunk_ids=[c0._hash, c1._hash])
    indexer.insert_relation(entity=entities[1], chunk_ids=[c0._hash])
    del indexer

    retriever = Entity2ChunkSQL(work_dir)
    # chunk_id match counter
    chunk_id_list = retriever.get_chunk_ids(entities=['wechat'])
    print(chunk_id_list)
    assert chunk_id_list[0][0] == c0._hash

    shutil.rmtree(work_dir)

if __name__ == '__main__':
    test_entity_build_and_query()
