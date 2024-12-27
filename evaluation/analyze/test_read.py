import json
import pdb
import sys
from loguru import logger

def calc(path):
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

                    if 'retriever_reason' == jsono['node']:
                        fout.write(json.dumps(jsono, ensure_ascii=False))
                        fout.write('\n')

    rate = true_cnt / (false_cnt + true_cnt)
    logger.info((rate, true_cnt, false_cnt + true_cnt))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        # path = '/home/data/khj/workspace/seedllm/HuixiangDou/2_zero_shot_kag_seedllm_Qwen2.5-7B-Instruct.jsonl'
        path = '/data/khj/workspace/HuixiangDou/1202_kag_seedllm_Qwen2.5-7B-Instruct.jsonl'
        path = '/data/khj/workspace/HuixiangDou/2024-12-26_13/2_hybrid_zero_shot_kag_seedllm_Qwen2.5-7B-Instruct.jsonl'
    calc(path=path)
