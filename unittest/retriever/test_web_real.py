import os
import unittest
from huixiangdou.service import WebRetriever, RetrieveResource, RetrieveReply  # 确保从你的模块导入相应的类
from huixiangdou.primitive import Query, always_get_an_event_loop


class TestWebRetriever:

    def __init__(self):
        self.config_path = 'config.ini'
        self.resource = RetrieveResource(
            config_path=self.config_path)  # 假设这个类有一个默认的构造函数
        self.web_retriever = WebRetriever(resource=self.resource,
                                          config_path=self.config_path)

    async def test_explore(self):
        # 测试explore方法
        query = Query(text='test query')
        result = await self.web_retriever.explore(query)
        print(result)
        # result = await self.web_retriever.analyze_url('http://baike.baidu.com/item/%E5%A4%A7%E7%B1%B3/22607')
        # print(result)


if __name__ == '__main__':
    retriever = TestWebRetriever()
    loop = always_get_an_event_loop()
    loop.run_until_complete(retriever.test_explore())
