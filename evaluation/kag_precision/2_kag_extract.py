from huixiangdou.primitive import LLM, always_get_an_event_loop
from huixiangdou.pipeline import ParallelPipeline

import os
import json
from loguru import logger

work_dir = 'workdir'
config_path = 'config.ini'
assistant = ParallelPipeline(work_dir=work_dir, config_path=config_path)

files = ['mix.jsonl']
modelname = assistant.resource.llm.default_model_info()['model']
modelname = modelname.split('/')[-1]
output = '2_public_data_kag_{}.jsonl'.format(modelname)

processed_keys = set()
if os.path.exists(output):
    with open(output) as fin:
        for jsonstr in fin:
            jsono = json.loads(jsonstr)
            processed_keys.add(jsono['input'])

with open(output, 'a') as fout:
    loop = always_get_an_event_loop()

    for jsonl in files:
        if not jsonl.endswith('.jsonl'):
            continue
        filepath = os.path.join('/home/khj/workspace/UltraDomain/', jsonl)

        logger.info(f'processing {filepath}')
        with open(filepath) as fin:
            for line in fin:
                jsono = json.loads(line)
                input = jsono['input']
                if input in processed_keys:
                    logger.info('skip')
                    continue
                
                async def wrap_async_run(query):
                    response = ''
                    async for sess in assistant.generate(query=query, history=[], language='en'):
                        response = sess.response
                        logger.info(sess.stage, response)
                    return response
                
                output = loop.run_until_complete(wrap_async_run(query=input))
                logger.info(output)
                json_str = json.dumps({"input":input, "output": output, "source": str(jsonl), "gt": jsono['answers']}, ensure_ascii=False)
                fout.write(json_str)
                fout.write('\n')
                fout.flush()
