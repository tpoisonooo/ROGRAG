from huixiangdou.primitive import LLM, always_get_an_event_loop, Query
from huixiangdou.pipeline import ParallelPipeline
from loguru import logger
import os
import json
import pdb

work_dir = 'workdir'
config_path = 'config.ini'

# 指定你的base目录
base_dir = '/data/khj/workspace/SeedBench/data/zero-shot'
assistant = ParallelPipeline(work_dir=work_dir, config_path=config_path)

# 遍历base目录
modelname = assistant.resource.llm.default_model_info()['model']
modelname = modelname.split('/')[-1]
output_file = '2_zero_shot_kag_seedllm_{}.jsonl'.format(modelname)

# get looper
loop = always_get_an_event_loop()

for root, dirs, files in os.walk(base_dir):
    for file in files:
        # 检查文件扩展名是否为.json
        if file.endswith('.json'):
            file_path = os.path.join(root, file)
            
            # 打开并读取JSON文件
            data = {}
            with open(file_path, 'r', encoding='utf-8') as fin:
                datas = json.load(fin)

                for data in datas:
                    question = data['question']
                    generation_question = data['instruction'] + '\n' + data['question']
                    answer = data['answer']
                    task = data['task_type']

                    async def wrap_async_run(query):
                        response = ''
                        async for sess in assistant.generate(query=query, history=[], language='zh_cn'):
                            response = sess.response
                            logger.info(sess.stage, response)
                        return response

                    q = Query(text=question, generation_question=generation_question)
                    output = loop.run_until_complete(wrap_async_run(query=q))
                    json_str = json.dumps({"input":generation_question, "output": output, "gt": answer, "task": task, "source": file}, ensure_ascii=False)

                    with open(output_file, 'a') as fout:
                        fout.write(json_str)
                        fout.write('\n')
                        fout.flush()
