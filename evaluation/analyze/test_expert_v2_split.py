import os
import csv
import json
import jieba
from rouge_chinese import Rouge
import re

csv_file_path = '/data/khj/workspace/HuixiangDou/expert_v2/output_en_expert_42_qa_results.csv'


def rouge_score_func(hyps, refs):
    assert (len(hyps) == len(refs))
    hyps = [' '.join(jieba.cut(h)) for h in hyps]
    hyps = [h if h.strip() != "" else "无内容" for h in hyps]
    refs = [' '.join(jieba.cut(r)) for r in refs]
    rouge_scores = Rouge().get_scores(hyps, refs)
    rouge_ls = [score["rouge-l"]["f"] for score in rouge_scores]
    average_rouge_l = sum(rouge_ls) / len(rouge_ls)
    return average_rouge_l


def load_types():
    _all = {"gene": set(), "mwf": set(), "mzn": set(), "transcriptome": set()}
    for root, dirs, files in os.walk(
            '/data/khj/workspace/HuixiangDou/expert_v1'):
        for file in files:
            if not file.endswith('.json'):
                continue

            _type = file.split('_')[1]

            with open(os.path.join(root, file)) as f:
                jsonobj = json.load(f)

            for item in jsonobj:
                if 'question' not in item:
                    continue
                question = item['question']
                _all[_type].add(question)
    return _all


def assign_types():
    _all = load_types()
    _types = {"gene": [], "mwf": [], "mzn": [], "transcriptome": []}
    with open(csv_file_path, mode='r') as file:
        # 创建 csv 读取器对象
        csv_reader = csv.reader(file)

        # 读取 csv 文件的表头（假设第一行是表头）
        headers = next(csv_reader)
        print("表头：", headers)

        # 逐行读取 csv 文件的内容
        for row in csv_reader:
            query = row[1].strip()
            if query.startswith('"'):
                query = query[1:]
            if query.endswith('"'):
                query = query[0:-1]

            for k, v in _all.items():
                for candidate in v:
                    score = rouge_score_func([query], [candidate])
                    if score > 0.8:
                        _types[k].append(row)

    for k, v in _types.items():
        jsonstr = json.dumps(v, indent=2, ensure_ascii=False)
        print(len(v))
        with open('out/' + k + '.json', 'w') as f:
            f.write(jsonstr)


assign_types()
