import os
import json
import pdb

output_dir = '/home/data/khj/workspace/HuixiangDou/eval/zero-shot'
outputs = dict()
with open('2_zero_shot_kag_Qwen2.5-7B-Instruct.jsonl') as f:
    for line in f:
        if not line:
            break
        try:
            jsono = json.loads(line)
        except Exception as e:
            pdb.set_trace()
            print(e)
        source = jsono['source']
        question = jsono['input']
        predict = jsono['output']
        answer = jsono['gt']

        if source not in outputs:
            outputs[source] = []
        outputs[source].append({'question':question, 'predict':predict, 'answer':answer})    

for filename, result in outputs.items():
    output_filename = os.path.join(output_dir, filename)
    with open(output_filename, 'w') as fout:
        jsonstr = json.dumps(result, indent=4, ensure_ascii=False)
        fout.write(jsonstr)
