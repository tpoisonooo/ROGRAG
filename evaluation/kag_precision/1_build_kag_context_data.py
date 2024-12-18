import os
import json

# 把 UltraDomain 去重后的数据，按照 "领域/编号" 的形式放入 repodir

input_dir = '/home/khj/workspace/rag-data0'
output_base = '/home/khj/workspace/seedllm/HuixiangDou/repodir'
filenames = os.listdir(input_dir)

for filename in filenames:
    cls = filename.split('_')[0]
    
    filepath = os.path.join(input_dir, filename)
    with open(filepath) as fin:
        json_str = fin.read()
        json_obj = json.loads(json_str)

        for idx, content in enumerate(json_obj):

            output_dir = os.path.join(output_base, cls)
            os.makedirs(output_dir, exist_ok=True)

            output_file = os.path.join(output_dir, f'{idx}.txt')
            with open(output_file, 'w') as fout:
                fout.write(content)
                fout.flush()
