from huixiangdou.primitive import LLM, always_get_an_event_loop
from huixiangdou.pipeline import ParallelPipeline
from huixiangdou.service import RetrieveResource

import os
import json
import pdb
from loguru import logger

work_dir = 'workdir'
config_path = 'config-20241122.ini'

input_files = [
    'gold/2_public_data_kag_Qwen2.5-7B-Instruct.jsonl',
    'gold/0_direct_chat_public_data_Qwen2.5-7B-Instruct.jsonl'
]
# ['2_public_data_kag_Qwen2.5-7B-Instruct.jsonl', '0_direct_chat_public_data_context_Qwen2.5-72B-Instruct.jsonl']
# clses = ['mix.jsonl', 'agriculture.jsonl', 'biology.jsonl', 'physics.jsonl']
clses = ['agriculture.jsonl']
questions = set()
for cls in clses:
    filepath = os.path.join('/home/data/khj/workspace/UltraDomain', cls)
    with open(filepath) as f:
        for jsonstr in f:
            jsono = json.loads(jsonstr)
            questions.add(jsono['input'])

template = """---Role---
You are an expert tasked with evaluating two answers to the same question based on three criteria: **Comprehensiveness**, **Diversity**, and **Empowerment**.
---Goal---
You will evaluate two answers to the same question based on three criteria: **Comprehensiveness**, **Diversity**, and **Empowerment**.

- **Comprehensiveness**: How much detail does the answer provide to cover all aspects and details of the question?
- **Diversity**: How varied and rich is the answer in providing different perspectives and insights on the question?
- **Empowerment**: How well does the answer help the reader understand and make informed judgments about the topic?

For each criterion, choose the better answer (either Answer 1 or Answer 2) and explain why. Then, select an overall winner based on these three categories.

Here is the question:
{query}

Here are the two answers:

**Answer 1:**
{answer1}

**Answer 2:**
{answer2}

Evaluate both answers using the three criteria listed above and provide detailed explanations for each criterion.

Output your evaluation in the following JSON format:

{{
    "Comprehensiveness": {{
        "Winner": "[Answer 1 or Answer 2]",
        "Explanation": "[Provide explanation here]"
    }},
    "Empowerment": {{
        "Winner": "[Answer 1 or Answer 2]",
        "Explanation": "[Provide explanation here]"
    }},
    "Overall Winner": {{
        "Winner": "[Answer 1 or Answer 2]",
        "Explanation": "[Summarize why this answer is the overall winner based on the three criteria]"
    }}
}}
"""

count_left = 0
count_right = 0
def extract_winner(text : str):
    global count_left
    global count_right
    text = text.lower()
    if text.startswith('```json'):
        text = text[7:]
        text = text[0:-3]
    
    logger.info(text)
    try:
        jsono = json.loads(text)
        keys = ['comprehensiveness', 'empowerment', 'overall winner']
        if keys[-1] in jsono:
            winner = jsono[keys[-1]]['winner']
            if '1' in winner:
                count_left += 1
            elif '2' in winner:
                count_right += 1
            else:
                pdb.set_trace()
                pass
    except Exception as e:
        logger.error(str(e))

        index = text.find('overall winner')
        text = text[index:]
        texts = text.split('\n')
        for t in texts:
            if '"winner"' in t:
                if 'answer 1' in t:
                    count_left += 1
                elif 'answer 2' in t:
                    count_right += 1
                else:
                    pdb.set_trace()
                    pass
                break


loop = always_get_an_event_loop()
csv_file_name = 'output.csv'

pairs = dict()
for input_file in input_files:
    with open(input_file) as f:
        for jsonstr in f:
            jsono = json.loads(jsonstr)
            question = jsono['input']
            if question not in questions:
                continue

            if question not in pairs:
                pairs[question] = [jsono['output']]
            else:
                pairs[question].append(jsono['output'])

resource = RetrieveResource(config_path=config_path)
for k,v in pairs.items():
    if len(v) < 2:
        pdb.set_trace()
        continue
    prompt = template.format(query=k, answer1=v[0], answer2=v[1])
    response = loop.run_until_complete(resource.llm.chat(prompt))
    winner = extract_winner(text=response)

rate = count_left / count_right
logger.info(f'{count_left} {count_right}, rate {rate}')
