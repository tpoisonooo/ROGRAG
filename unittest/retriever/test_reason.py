from huixiangdou.service.retriever import ReasonRetriever, RetrieveResource
from huixiangdou.primitive import Faiss, Chunk, Query, LLM, always_get_an_event_loop

import json
import pdb
from loguru import logger


def run_reasoning():
    resource = RetrieveResource(config_path='config.ini')
    retriever = ReasonRetriever(resource=resource, work_dir='workdir')

    loop = always_get_an_event_loop()
    filename = '/home/khj/knowledge2question/data/one-shot/1-1.json'

    output_path = 'output.txt'
    with open(filename, 'r', encoding='utf-8') as fin:
        datas = json.load(fin)

        for data in datas:
            question = data['question']
            index = question.find('A. ')
            question = question[0:index]
            # question = '查询水稻基因组中FIE同源物的数量'
            # question = '黄丰占的特性有多少种？'
            # question = 'Where was strong GUS staining observed?'
            # question = '黄华占在铅山县汪二镇进行了示范种植最早种植年份加上99再加2是多少'
            # question = '亲本关系在哪些水稻上有体现？'
            # question = '黄华占和丰秀占，哪个水稻的认定时间更早？'

            qs = [
                '黄华占在铅山县汪二镇进行了示范种植最早种植年份加上99再加2是多少', '黄丰占的特性有多少种？',
                '亲本关系在哪些水稻上有体现？', '黄华占和丰秀占，哪个水稻的认定时间更早？'
            ]

            q = Query(text=question)

            try:

                r = loop.run_until_complete(retriever.explore(query=q))
                print(r)
                with open(output_path, 'a') as fout:
                    json_str = json.dumps({
                        'r': str(r),
                        'q': question
                    },
                                          indent=2,
                                          ensure_ascii=False)
                    fout.write(json_str)
                    fout.write('\n')

            except Exception as e:
                pdb.set_trace()
                if 'similarity search' in str(e):
                    continue

                logger.error(e)


if __name__ == '__main__':
    run_reasoning()
