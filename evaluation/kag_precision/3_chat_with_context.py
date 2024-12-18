from huixiangdou.primitive import LLM, always_get_an_event_loop, RecursiveCharacterTextSplitter, Query
from huixiangdou.service.retriever import DenseRetriever
import os
import json
from loguru import logger
llm = LLM(config_path='config-20241125.ini')

files = os.listdir('/home/khj/workspace/UltraDomain/')
modelname = llm.default_model_info()['model']
modelname = modelname.split('/')[-1]
output = '3_chat_context_{}.jsonl'.format(modelname)

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

        clses = ['agriculture', 'biology', 'mix', 'physics']

        _pass = False
        for cls in clses:
            if cls in jsonl:
                _pass = True
                break

        if not _pass:
            continue

        filepath = os.path.join('/home/khj/workspace/UltraDomain/', jsonl)

        logger.info(f'processing {filepath}')
        with open(filepath) as fin:
            for line in fin:
                jsono = json.loads(line)
                q = jsono['input']
                if q in processed_keys:
                    logger.info('skip')
                    continue
                
                format = """## Task
Please read context to answer user input.

## user input
{question}

## context
{context}
"""
                context_str= jsono['context']
                logger.info(f'context str len {len(context_str)}')
                prompt = format.format(context=context_str, question=jsono['input'])
                
                # print(loop.run_until_complete(llm.chat('你好')))
                resp = loop.run_until_complete(llm.chat(prompt=prompt, allow_truncate=True))

                json_str = json.dumps({"input":q, "output": resp, "source": str(jsonl), "gt": jsono['answers']}, ensure_ascii=False)
                fout.write(json_str)
                fout.write('\n')
                fout.flush()
