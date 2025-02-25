import pytest
import re
import pytoml
import unittest
import json
import os
from huixiangdou.service import KnowledgeRetriever, RetrieveResource, ChunkSQL
from huixiangdou.primitive import Faiss, Chunk, Query


def build_config():

    def load_secret():
        kimi_token = ''
        serper_token = ''
        with open('unittest/token.json') as f:
            json_obj = json.load(f)
            kimi_token = json_obj['kimi']
            serper_token = json_obj['serper']
        return kimi_token, serper_token

    kimi_token, serper_token = load_secret()
    with open('config.ini') as f:
        config = pytoml.load(f)
        config['web_search']['engine'] = 'serper'
        config['web_search']['serper_x_api_key'] = serper_token
        config['llm']['kimi']['api_key'] = kimi_token
    config_path = '/tmp/config.ini'
    with open(config_path, 'w', encoding='utf8') as f:
        pytoml.dump(config, f)
        f.flush()
    return config_path


def build_low_high_level_db(work_dir: str, resource: RetrieveResource):
    # copy test data to `work_dir`
    entityDB = Faiss()
    entityDB.upsert(Chunk(content_or_path="三味书屋"))
    entityDB.upsert(Chunk(content_or_path="百草园"))
    entityDB.save(folder_path=os.path.join(work_dir, 'db_kag_entity'),
                  embedder=resource.embedder)

    relationDB = Faiss()
    relationDB.upsert(Chunk(content_or_path="教书"))
    relationDB.upsert(Chunk(content_or_path="成长的地方"))
    relationDB.save(folder_path=os.path.join(work_dir, 'db_kag_relation'),
                    embedder=resource.embedder)

    chunks = ChunkSQL(file_dir=work_dir)
    chunks.add(chunk=[Chunk(content_or_path="从百草园到三味书屋")])


class TestKAG(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.config_path = build_config()
        self.work_dir = '/home/khj/seedllm/HuixiangDou/workdir'
        # build_low_high_level_db(work_dir=self.work_dir, resource=self.resource)
        self.resource = RetrieveResource(config_path=self.config_path)
        self.kag = KnowledgeRetriever(resource=self.resource,
                                      work_dir=self.work_dir)

    # 测试 combine_contexts 函数
    def test_combine_contexts(self):
        high_level_context = type(
            'RetrieveReply', (), {
                "text_units": [["entity1"]],
                "nodes": [["entity1"]],
                "relations": [["entity1"]]
            })
        low_level_context = type(
            'RetrieveReply', (), {
                "text_units": [["entity2"]],
                "nodes": [["entity2"]],
                "relations": [["entity2"]]
            })
        result = self.kag.combine_contexts(high_level_context,
                                           low_level_context)
        assert result.text_units == [["entity1"], ["entity2"]]

    async def test_query_local_query(self):
        query = Query(text='花园, 我家后面, 相传')
        ret = await self.kag._build_local_query_context(
            query, self.kag.graph, self.kag.entityDB, self.kag.chunkDB)

    async def test_query_global_query(self):
        query = Query(text='花园, 我家后面, 相传')
        ret = await self.kag._build_global_query_context(
            query, self.kag.graph, self.kag.entityDB, self.kag.relationDB,
            self.kag.chunkDB)

    async def asyncTearDown(self):
        # 清理测试环境
        import shutil
        os.remove(self.config_path)
