from huixiangdou.primitive import LLM, always_get_an_event_loop
from loguru import logger
import os
import json
import pdb
import argparse
import datetime
import csv
import openai
from openai import OpenAI
import jieba
from collections import Counter
import re
import jieba
from rouge_chinese import Rouge

def rouge_score_func(hyps, refs):
    assert(len(hyps) == len(refs))
    hyps = [' '.join(jieba.cut(h)) for h in hyps]
    hyps = [h if h.strip() != "" else "无内容" for h in hyps]
    refs = [' '.join(jieba.cut(r)) for r in refs]
    rouge_scores = Rouge().get_scores(hyps, refs)
    rouge_ls = [score["rouge-l"]["f"] for score in rouge_scores]
    average_rouge_l = sum(rouge_ls) / len(rouge_ls)
    return average_rouge_l

def extract_score(text):
    """
    从文本中提取得分
    :param text: 输入文本字符串
    :return: 提取的得分，如果没有匹配到则返回None
    """
    # 定义匹配模式
    pattern = r"<\|>(.*?)<\|>"
    
    # 使用re.search查找匹配项
    match = re.search(pattern, text)
    
    # 如果找到匹配项，返回得分
    if match:
        return float(match.group(1))
    else:
        raise Exception('score not exist')

def kimi(prompt:str, n:int=5):
    messages = [
        {
            'role': 'system',
            'content': 'You are a helpful assistant.'
        },
        {
            'role': 'user',
            'content': prompt
        }
    ]

    client = OpenAI(
        api_key=os.getenv('MOONSHOT_API_KEY'),
        base_url='https://api.moonshot.cn/v1',
    )

    completion = client.chat.completions.create(model='moonshot-v1-32k', messages=messages, n=n, temperature=1.0)
    contents = [choice.message.content for choice in completion.choices]

    scores = []
    for content in contents:
        try:
            score = extract_score(content)
            scores.append(score)
        except Exception as e:
            pass
    if not scores:
        pdb.set_trace()
        pass
    avg_score = sum(scores) / len(scores)
    return contents, avg_score

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Knowledge retrieval expert scoring.')
    parser.add_argument('--workdir',
                        type=str,
                        default='workdir',
                        help='Working directory.')
    parser.add_argument(
        '--datadir',
        type=str,
        default='/data/khj/workspace/HuixiangDou/2025-01-14_16',
        help='Expert datadir for test.')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()

    # get looper
    loop = always_get_an_event_loop()

    for root, dirs, files in os.walk(args.datadir):
        csv_files = []
        for file in files:
            if not file.endswith('.csv'):
                continue
            csv_files.append(os.path.join(root, file))
        
        # 打开并读取 csv
        data = {}
        # 打开 csv 文件

        for csv_file_path in csv_files:
            with open(csv_file_path, mode='r') as file:
                # 创建 csv 读取器对象
                print(file)
                csv_reader = csv.reader(file)
                # 逐行读取 csv 文件的内容
                
                list_of_row = []
                llm_score_list = []
                rouge_score_list = []
                for row in csv_reader:
                    # print(row)
                    question = row[0]
                    gt = row[1]
                    dt = row[-1]
                    if not question:
                        pdb.set_trace()
                        continue

                    template = """你是一个中英文阅卷人，擅长阅读**试卷问题**，分析**学生答案**和**参考答案**的关联度。最终给出得分。
## 任务
请仔细阅读**试卷问题**、**参考答案**和**学生依据**，给出 0 到 100 间的得分。

## 输出格式要求
- 先给出打分依据，然后给出得分
- 得分是 0 到 100 的整数，用分隔符 <|> 表达。例如 "<|>得分<|>"

## 打分示例
- 学生回答不知道，得 0 分，解释后输出 "<|>0<|>"

## 注意事项
- 作为阅卷人，无论何种情况，你会给出得分
- 你不会在输出结果时忘掉分隔符 <|>

## 试卷问题
{question}

## 参考答案
```txt
{gt}
```

## 学生答案
```txt
{dt}
```
"""
                    prompt = template.format(question=question, gt=gt, dt=dt)

                    _, llm_score = kimi(prompt, n=3)
                    llm_score_list.append(llm_score)

                    rouge_score = rouge_score_func(hyps=[dt], refs=[gt])
                    rouge_score_list.append(rouge_score)
                    row = {
                        "question": question,
                        "dt": dt,
                        "gt": gt,
                        "rouge": rouge_score,
                        "llm_score": llm_score
                    }
                    list_of_row.append(row)

                list_of_row.append({
                    "meta_avg_llm": sum(llm_score_list) / len(llm_score_list),
                    "meta_avg_rouge": sum(rouge_score_list) / len(rouge_score_list)
                })
                with open(os.path.join(args.datadir, os.path.basename(csv_file_path) + '.json'), 'w') as f:
                    json_str = json.dumps(list_of_row, ensure_ascii=False, indent=2)
                    f.write(json_str)
