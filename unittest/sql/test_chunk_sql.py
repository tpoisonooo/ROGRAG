import unittest
from unittest.mock import patch, mock_open
from huixiangdou.service import ChunkSQL
from huixiangdou.primitive import Chunk
import sqlite3
import os
import shutil


class TestChunkSQL(unittest.TestCase):

    def setUp(self):
        self.file_dir = '/tmp/chunk'
        self.chunksql = ChunkSQL(self.file_dir)
        self.chunk = Chunk(_hash='test_hash',
                           content_or_path='test_content',
                           metadata={"key": "value"},
                           modal='text')

    def test_init(self):
        # 测试初始化是否创建了目录和数据库
        self.assertTrue(os.path.exists(self.file_dir))
        self.assertTrue(
            os.path.exists(os.path.join(self.file_dir, 'chunks.sql')))

    def test_add_get_chunk(self):
        # 测试获取chunk
        self.chunksql.add(self.chunk)
        retrieved_chunk = self.chunksql.get(self.chunk._hash)
        self.assertEqual(retrieved_chunk._hash, self.chunk._hash)
        self.assertEqual(retrieved_chunk.content_or_path,
                         self.chunk.content_or_path)

    def test_exist(self):
        # 测试chunk是否存在
        self.chunk._hash += "abc"
        self.chunksql.add(self.chunk)
        self.assertTrue(self.chunksql.exist(self.chunk))
        self.assertFalse(self.chunksql.exist(Chunk(_hash='non_existent_hash')))

    def test_delete_chunk(self):
        # 测试删除chunk
        self.chunk._hash += "def"
        self.chunksql.add(self.chunk)
        self.chunksql.delete(self.chunk._hash)
        self.assertIsNone(self.chunksql.get(self.chunk._hash))

    def tearDown(self):
        # 清理测试数据库和目录
        self.chunksql.__del__()
        if os.path.exists(self.file_dir):
            shutil.rmtree(self.file_dir)


if __name__ == '__main__':
    unittest.main()
