from huixiangdou.primitive import LLM, always_get_an_event_loop
from huixiangdou.pipeline import ParallelPipeline
from huixiangdou.service import RetrieveResource

import os
import re
import json
import jieba
import csv
from rouge import Rouge
from loguru import logger

work_dir = 'workdir'
config_path = 'config-20241122.ini'

input_files = [
    # 'gold/0_direct_chat_public_data_context_Qwen2.5-72B-Instruct-128K.jsonl',
    # 'gold/0_direct_chat_public_data_Qwen2.5-14B-Instruct.jsonl',
    # 'gold/0_direct_chat_public_data_Qwen2.5-32B-Instruct.jsonl',

    # 'gold/0_direct_chat_public_data_Qwen2.5-7B-Instruct.jsonl',
    # 'gold/2_public_data_kag_Qwen2.5-7B-Instruct.jsonl',

    '3_chat_context_Qwen2.5-7B-Instruct.jsonl'
]
# ['2_public_data_kag_Qwen2.5-7B-Instruct.jsonl', '0_direct_chat_public_data_context_Qwen2.5-72B-Instruct.jsonl']
# clses = ['mix.jsonl', 'agriculture.jsonl', 'biology.jsonl', 'physics.jsonl']
clses = ['agriculture.jsonl']

template = """你是一位问答考试阅卷人，擅长根据标准答案，给学生答案打分。
## 任务
根据标准答案和学生答案。判断学生答案的正确度。

## 判断方法
- 识别标准答案的实体词（尤其是数字），对于每个实体词，在学生答案中查看是否存在。
- 提取标准答案中实体词间的重要关系，对于每个关系，尝试基于学生答案寻找参考。

## 判断依据
- 标准答案包含的信息，学生答案是否全都有
- 如果学生答案存在比标准答案更多的内容，不会而因此扣分
- 你不会因为学生答案多出步骤而扣分，只要关键步骤没有错误即可
- 如果学生答案涵盖了标准答案的所有核心信息，给出满分
- 如果学生答案的书写格式和标准答案不同，不会因格式扣分
- 你不会因为中英文差异而扣分
- 你会根据学生答案缺失的信息量扣除相应分数

## 输出格式要求
- 输出是包含得分的 kv 格式，例如 (score:100) 
- 你不会不给得分
- 得分是 0 到 100 之间的整数
- 你不会重复表达和同义反复
- 你会解释为什么给出这个得分

## 标准答案
{gt}

## 学生答案
{output}
"""

def extract_score(text : str):
    text = text.replace(' ', '')
    # 正则表达式模式，用于匹配 '(score:数字)' 格式
    pattern1 = r'\(score:(\d+)\)'
    # 使用正则表达式搜索文本
    match = re.search(pattern1, text)

    # 如果找到匹配项，则提取得分并转换为整型
    if match:
        score = int(match.group(1))  # group(1) 表示第一个括号内匹配的内容
        print(f"提取的得分是：{score}")
    else:
        print("没有找到匹配的得分。")
        return 0
    return int(score)

resource = RetrieveResource(config_path=config_path)
loop = always_get_an_event_loop()
csv_file_name = 'output.csv'

for input_file in input_files:
    results = dict()
    with open(input_file) as f:
        for jsonstr in f:
            jsono = json.loads(jsonstr)
            cls = jsono['source']
            if cls not in results:
                results[cls] = {}
            
            input = jsono['input']
            text1 = jsono['output']
            text2 = jsono['gt'][0]
            source = jsono['source']

            if source not in clses:
                logger.info(f'skip {source}')
                continue

            prompt = template.format(gt=text2, output=text1)
            response = loop.run_until_complete(resource.llm.chat(prompt))

            rouge = Rouge()
            dt_jb = ' '.join(jieba.cut(text1)) 
            gt_jb = ' '.join(jieba.cut(text2)) 
            scores = rouge.get_scores(dt_jb, gt_jb)
            rouge_score = scores[0]['rouge-1']['r']
            llm_score = extract_score(response)

            basename = os.path.basename(input_file)
            csv_file_name = f'csv/{basename}_{source}.csv'
            with open(csv_file_name, mode='a', newline='', encoding='utf-8') as fout:
                writer = csv.writer(fout)
                writer.writerow([input, text1, text2, rouge_score, response, llm_score, input_file])
                # results[cls].append({"rouge": float(score), "llm": response})
