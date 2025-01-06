import unittest
import os
from huixiangdou.service import Entity2ChunkSQL
import json
import shutil
class TestEntity2ChunkSQL(unittest.TestCase):

    def setUp(self):
        self.file_dir = '/tmp/test_db'
        os.makedirs(self.file_dir, exist_ok=True)
        self.entity2chunk = Entity2ChunkSQL(self.file_dir, ignore_case=True)

    def test_init_and_clean(self):
        # 测试初始化和清理数据库
        self.assertTrue(os.path.exists(os.path.join(self.file_dir, 'entity2chunk.sql')))
        self.entity2chunk.clean()
        # 清理后，数据库文件应该仍然存在，但表应该被重置
        self.assertTrue(os.path.exists(os.path.join(self.file_dir, 'entity2chunk.sql')))

    def test_insert_and_parse(self):
        # 测试插入关系和解析文本
        self.entity2chunk.insert_relation("上海", ['chunk1', 'chunk2'])
        self.entity2chunk.insert_relation("明天", ['chunk3'])
        
        chunk_ids = self.entity2chunk.get_chunk_ids(["上海"])
        self.assertEqual(chunk_ids, [('chunk1', 1), ('chunk2', 1)])  # 只返回出现次数最多的chunk_id

    def tearDown(self):
        # 测试结束后清理测试数据库
        self.entity2chunk.__del__()
        shutil.rmtree(self.file_dir)

if __name__ == '__main__':
    unittest.main()
