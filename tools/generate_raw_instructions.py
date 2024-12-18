from huixiangdou.service.prompt import reason_prompts

from huixiangdou.primitive import LLM, always_get_an_event_loop
from huixiangdou.service import RetrieveResource
from loguru import logger
import os
import json
import pdb
import re

def parse_string_form(response: str):
    try:
        logger.debug(f"logic form:{response}")
        _output_string = response.replace("：", ":")
        _output_string = response.strip()
        sub_queries = []
        logic_forms = []
        current_sub_query = ''
        for line in _output_string.split('\n'):
            if line.startswith('Step'):
                sub_queries_regex = re.search('Step\d+:(.*)', line)
                if sub_queries_regex is not None:
                    sub_queries.append(sub_queries_regex.group(1))
                    current_sub_query = sub_queries_regex.group(1)
            elif line.startswith('Output'):
                sub_queries.append("output")
            elif line.startswith('Action'):
                logic_forms_regex = re.search('Action\d+:(.*)', line)
                if logic_forms_regex:
                    logic_forms.append(logic_forms_regex.group(1))
                    if len(logic_forms) - len(sub_queries) == 1:
                        sub_queries.append(current_sub_query)
        return sub_queries, logic_forms
    except Exception as e:
        logger.warning(f"{response} parse logic form faied {e}", exc_info=True)
        return [], []

def main():
    work_dir = 'workdir'
    config_path = 'config.ini'

    # 指定你的base目录
    base_dir = '/home/khj/knowledge2question/data/one-shot'

    resource = RetrieveResource(config_path=config_path)
    output_file = 'reason_raw_response.jsonl'

    # get looper
    loop = always_get_an_event_loop()

    for root, dirs, files in os.walk(base_dir):
        for file in files:
            # 检查文件扩展名是否为.json
            if '1-1.json' not in file and '3-1.json' not in file:
                continue
            
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                
                # 打开并读取JSON文件
                data = {}
                with open(file_path, 'r', encoding='utf-8') as fin:
                    datas = json.load(fin)

                    for data in datas:
                        question = data['question']
                        index = question.find('A. ')
                        question = question[0:index]
                        prompt = reason_prompts['format_input']['zh_cn'].format(input_text=question)
                        output = loop.run_until_complete(resource.llm.chat(prompt))
                        sub_queries, logic_forms = parse_string_form(output)

                        json_str = json.dumps({"question":question, "output": output, "sub_queries": sub_queries, "logic_forms": logic_forms}, ensure_ascii=False, indent=2)

                        with open(output_file, 'a') as fout:
                            fout.write(json_str)
                            fout.write('\n')

if __name__ == '__main__':
    main()
