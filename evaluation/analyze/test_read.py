import json
import pdb
from loguru import logger

# path = '/home/data/khj/workspace/seedllm/HuixiangDou/2_zero_shot_kag_seedllm_Qwen2.5-7B-Instruct.jsonl'
path = '/home/data/khj/workspace/seedllm/HuixiangDou/1202_kag_seedllm_Qwen2.5-7B-Instruct.jsonl'
true_cnt = 0
false_cnt = 0

with open('badcase.jsonl', 'w') as fout:
    with open(path) as f:
        for line in f:
            jsono = json.loads(line)
            gt = jsono['gt'].lower()
            dt = jsono['output'].lower()
            source = jsono['source']
            if '1-1.json' not in source:
                continue

            if gt in dt:
                true_cnt += 1
            else:
                false_cnt += 1
                new_input = jsono['input'].split('问题：')[-1].strip()
                jsono['input'] = new_input
                logger.info(jsono)
                fout.write(json.dumps(jsono, ensure_ascii=False))
                fout.write('\n')
            
rate = true_cnt / (false_cnt + true_cnt)
logger.info(rate)
pdb.set_trace()
pass