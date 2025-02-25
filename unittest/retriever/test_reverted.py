import unittest
import os
from unittest.mock import MagicMock, patch
from huixiangdou.service import InvertedRetriever, RetrieveResource, RetrieveReply
from huixiangdou.service.sql import Entity2ChunkSQL, ChunkSQL
from huixiangdou.primitive import Query, Chunk


class TestInvertedRetriever(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.work_dir = '/tmp/test_inverted'
        os.makedirs(self.work_dir, exist_ok=True)
        self.resource = RetrieveResource('config.ini')  # 假设这个类有一个默认的构造函数
        indexer = Entity2ChunkSQL(
            os.path.join(self.work_dir, 'db_entity2chunk'))

        # 准备测试数据
        chunks = [Chunk(content_or_path="东方明珠"), Chunk(content_or_path="故宫大G")]

        indexer.insert_relation("上海", chunks[0]._hash)
        indexer.insert_relation("北京", chunks[1]._hash)
        del indexer

        chunk_sql = ChunkSQL(file_dir=os.path.join(self.work_dir, 'db_chunk'))
        chunk_sql.add(chunks)
        del chunk_sql

    async def test_explore(self):
        # 测试explore方法
        test_query = Query(text='北京')
        retriever = InvertedRetriever(self.resource, self.work_dir)
        r = await retriever.explore(test_query)
        self.assertIsInstance(r, RetrieveReply)
        self.assertEqual(len(r.text_units), 1)
        assert '故宫大G' in str(r.text_units[0])

    async def test_explore_empty_result(self):
        # 测试explore方法，查询没有结果
        retriever2 = InvertedRetriever(self.resource, self.work_dir)
        q = Query(text='nonexistent entity')

        result = await retriever2.explore(query=q)
        self.assertIsInstance(result, RetrieveReply)
        self.assertEqual(len(result.text_units), 0)

    async def asyncTearDown(self):
        import shutil
        shutil.rmtree(self.work_dir)


if __name__ == '__main__':
    unittest.main()
