import argparse
import os
import pandas as pd
from pypinyin import pinyin, Style
import re
from loguru import logger

from .pipeline import SerialPipeline, ParallelPipeline
from .primitive import Query, Pair, Token
from .service import server_prompts
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
import json
from typing import List
import uuid
import jieba

assistant = None
analogy = None
app = FastAPI(docs_url='/')


def get_req_uuid():
    return str(uuid.uuid4())[0:6]


class TextSimilarity:

    def __init__(self):
        pass

    def jaccard_similarity_str(self, str1: str, str2: str) -> float:
        set1 = set(jieba.lcut(str1.lower()))  # 使用jieba分词
        set2 = set(jieba.lcut(str2.lower()))  # 注意：中文通常不转换为小写
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union) if union else 0

    def jaccard_similarity_list(self, list1: list, list2: list) -> float:
        set1 = set(list1)
        set2 = set(list2)
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union) if union else 0

    def is_chinese_dominant(self, s, threshold=0.5):
        chinese_count = 0
        total_count = len(s)

        for char in s:
            if '\u4e00' <= char <= '\u9fff':
                chinese_count += 1

        chinese_ratio = chinese_count / total_count
        return chinese_ratio > threshold


class ExampleAnalogy:

    def __init__(self,
                 resource,
                 api_data_dir: str,
                 threshold: float = 0.3,
                 language: str = 'zh_cn'):
        if not os.path.exists(api_data_dir):
            logger.info('api_data_dir not exist, quit')
            return
        variety_path = os.path.join(api_data_dir,
                                    'variety/Rice_Variety_merged.csv')
        variety_pinyin_path = os.path.join(
            api_data_dir, 'variety/Rice_Variety_merged_pinyin.csv')
        gene_path = os.path.join(
            api_data_dir, 'gene/rice_reference_genome_annotation_20240903.csv')
        variety_template_path = os.path.join(
            api_data_dir, 'variety/variety_question_template.csv')
        gene_template_path = os.path.join(api_data_dir,
                                          'gene/gene_question_template.csv')

        # init jieba
        jieba_variety_path = os.path.join(api_data_dir,
                                          'variety/jieba_variety.txt')
        jieba_variety_pinyin_path = os.path.join(
            api_data_dir, 'variety/jieba_variety_pinyin.txt')
        # jieba_gene_path = os.path.join(api_data_dir, 'gene/jieba_gene.txt')
        # jieba.load_userdict(jieba_gene_path)
        jieba.load_userdict(jieba_variety_path)
        jieba.load_userdict(jieba_variety_pinyin_path)

        self.llm = resource.llm
        self.api_data_dir = api_data_dir
        self.threshold = threshold
        self.language = language
        #读取问题模板
        self.variety_question = pd.read_csv(
            variety_template_path)  # 假设问题在第三、四、五列
        self.gene_question = pd.read_csv(gene_template_path)
        #读取物种列表和基因列表
        self.variety = pd.read_csv(variety_path)
        self.variety_pinyin = pd.read_csv(variety_pinyin_path)
        self.gene = pd.read_csv(gene_path)
        self.variety_set = set(
            self.variety[self.variety.columns[0]].str.lower()).union(
                set(self.variety_pinyin[
                    self.variety_pinyin.columns[0]].str.lower()))
        self.gene_set = set()
        # 定义分隔符列表
        separators = [',', '/', '; ']
        for column in self.gene.columns[:5]:
            for sep in separators:
                self.gene_set.update(item.lower()
                                     for row in self.gene[column].astype(str)
                                     for item in row.split(sep) if item)

        # init llm chat template
        self.EXAMPLIFY_TEMPLATE = server_prompts['examplify'][language]

    async def process(self, query: str):
        metric = TextSimilarity()
        if metric.is_chinese_dominant(query):
            words = jieba.lcut(query.lower())
        else:
            tokens = re.findall(r'\w+|\?', query.lower())
            words = [token for token in tokens if token]
        # print(words)

        # 查找在self.variety中出现的词
        matched_word = None
        matched_gene = None
        matched_rice = None
        question_type = None
        # print('self.gene_set',self.gene_set)
        for word in words:
            if len(word) <= 1:
                continue
            if not matched_word and word in self.gene_set:
                matched_word = word
            elif not matched_word and word in self.variety_set:
                matched_word = word
            elif word == '水稻' or word == 'rice':
                matched_rice = word
            elif word == '基因' or word == 'gene':
                matched_gene = word

        #如果gene类型和rice同时出现,则检索gene类型
        if matched_word is not None:
            print('检索成功!')
        elif (matched_rice is not None
              and matched_gene is None) or (matched_gene is not None
                                            and matched_rice is None):
            #如果是关于水稻/基因但没涉及种类，使用大模型生成新问题
            prompt = self.EXAMPLIFY_TEMPLATE.format(query=query)
            response = await self.llm.chat(prompt=prompt)
            similar_questions = response
            response_body = {}
            response_body['status'] = {}
            response_body['data'] = {}
            response_body['status']['code'] = 0
            response_body['status']['error'] = 'None'
            response_body['data']['_id'] = get_req_uuid()
            response_body['data']['cases'] = similar_questions
            return response_body
        else:
            # 如果没有特定种类or涉及水稻/基因
            response_body = {}
            response_body['status'] = {}
            response_body['data'] = {}
            response_body['status']['code'] = 1
            response_body['status']['error'] = 'Not special specy'
            response_body['data']['_id'] = get_req_uuid()
            response_body['data']['cases'] = []
            return response_body

        key1 = self.variety_question.iloc[1, 1]
        key2 = ''.join(item[0] for item in pinyin(key1, style=Style.NORMAL))
        key3 = self.gene_question.iloc[1, 1].lower()
        key4 = self.gene_question.iloc[1, 1].lower()
        question_type = ""

        # 遍历variety_question的前十行
        similar_questions = []
        max_similarity = 0.2
        best_row = None
        best_col = None
        row_index = -1
        for index, row in self.variety_question.head(10).iterrows():
            for col in range(2, 6):  # 遍历第三、四、五、六列
                question = row.iloc[col]
                replaced_question = question.replace(key1, matched_word)
                similarity = metric.jaccard_similarity_str(
                    query, replaced_question)
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_row = row
                    best_col = col
                    row_index = index
                    question_type = 'variety'

        # 遍历variety_question的十~二十行
        for index in range(10, 20):  # 从索引10（第11行）到索引19（第20行）
            row = self.variety_question.iloc[index]
            for col in range(2, 6):  # 遍历第三、四、五、六列
                question = row.iloc[col].lower()
                replaced_question = question.replace(key2, matched_word)
                similarity = metric.jaccard_similarity_str(
                    query, replaced_question)
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_row = row
                    best_col = col
                    row_index = index
                    question_type = 'variety'

        # 遍历gene_question的前十行
        for index, row in self.gene_question.head(10).iterrows():
            for col in range(2, 6):  # 遍历第三、四、五、六列
                question = row.iloc[col]
                replaced_question = question.replace(key3, matched_word)
                similarity = metric.jaccard_similarity_str(
                    query, replaced_question)
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_row = row
                    best_col = col
                    row_index = index
                    question_type = 'gene'

        # 遍历gene_question的十~二十行
        for index in range(10, 20):  # 从索引10（第11行）到索引19（第20行）
            row = self.gene_question.iloc[index]
            for col in range(2, 6):  # 遍历第三、四、五、六列
                question = row.iloc[col].lower()
                replaced_question = question.replace(key4, matched_word)
                similarity = metric.jaccard_similarity_str(
                    query, replaced_question)
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_row = row
                    best_col = col
                    row_index = index
                    question_type = 'gene'
        # print('max_similarity:', max_similarity)
        if best_row is not None:
            # 替换best_row中除第三、四、五列外的其他列（如果需要）中的key为matched_word
            replaced_questions = []
            for col in range(2, 6):
                if col != best_col:
                    if row_index < 10 and question_type == 'variety':
                        replaced_question = (best_row).iloc[col].replace(
                            key1, matched_word)
                    elif row_index >= 10 and question_type == 'variety':
                        replaced_question = ((
                            best_row).iloc[col]).lower().replace(
                                key2, matched_word)
                    elif row_index < 10 and question_type == 'gene':
                        replaced_question = ((
                            best_row).iloc[col]).lower().replace(
                                key3, matched_word)
                    else:
                        replaced_question = ((
                            best_row).iloc[col]).lower().replace(
                                key4, matched_word)
                    replaced_questions.append(replaced_question)
            similar_questions = replaced_questions

            response_body = {}
            response_body['status'] = {}
            response_body['data'] = {}
            response_body['status']['code'] = 0
            response_body['status']['error'] = 'None'
            response_body['data']['_id'] = get_req_uuid()
            response_body['data']['cases'] = similar_questions
            return response_body

        # 如果问指定物种但问题无关，使用大模型生成新问题
        prompt = self.EXAMPLIFY_TEMPLATE.format(query=query)
        response = await self.llm.chat(prompt=prompt)
        similar_questions = response
        # print(similar_questions)
        response_body = {}
        response_body['status'] = {}
        response_body['data'] = {}
        response_body['status']['code'] = 0
        response_body['status']['error'] = 'None'
        response_body['data']['_id'] = get_req_uuid()
        response_body['data']['cases'] = similar_questions
        return response_body


class Talk(BaseModel):
    text: str
    image: str = ''


class Talk_seed(BaseModel):
    language: str
    enable_web_search: bool
    user: str
    history: list[Pair]


def format_refs(refs: List[str]):
    refs_filter = list(set(refs))
    if len(refs) < 1:
        return ''

    text = '**References:**\r\n'
    for file_or_url in refs_filter:
        text += '* {}\r\n'.format(file_or_url)
    text += '\r\n'
    return text


def extract_history(talk_seed):
    history = []
    for item in talk_seed.history:
        history.append({"role": "user", "content": item.user})
        history.append({"role": "assistant", "content": item.assistant})
    return history


async def coreference_resolution(query: str, history: List, language: str):
    if not history:
        return query
    global assistant
    pronouns = [
        'it', 'he', 'she', 'their', 'they', 'him', 'her', 'this', 'that', '它',
        '他', '她', '这', '那'
    ]
    for p in pronouns:
        if p in query:
            template = server_prompts['corefence_resolution'][language]
            json_str = json.dumps(history[-1], ensure_ascii=False)
            prompt = template.format(query=query, history=json_str)
            response = await assistant.resource.llm.chat(prompt=prompt)
            if 'NO' in response:
                return query
            return response
    return query


@app.post("/v2/chat")
async def chat(talk_seed: Talk_seed):
    global assistant
    print('enable web search {}'.format(talk_seed.enable_web_search))
    req_id = get_req_uuid()
    pipeline = {}
    language = 'zh_cn' if 'zh' in talk_seed.language else 'en'
    history = extract_history(talk_seed)

    # disable coreference resolution
    # coref_input = await coreference_resolution(query=talk_seed.user, history=history, language=language)
    coref_input = talk_seed.user
    logger.info('talk_seed.user {}, coref_input {}'.format(
        talk_seed.user, coref_input))

    query = Query(text=coref_input,
                  generation_question=coref_input,
                  enable_web_search=talk_seed.enable_web_search)

    async def event_stream():
        async for sess in assistant.generate(
                query=query,
                history=history,
                language=language,
        ):
            status = {"code": int(sess.code), "error": str(sess.code)}
            references = []

            if sess.fused_reply and not sess.delta:
                sources = sess.fused_reply.sources if sess.fused_reply else []

                logger.info(sources)
                for source in sources:
                    ref = source.metadata["source"]

                    if '://' in ref:
                        reference = {
                            "chunk": source.content_or_path,
                            "source_or_url": ref,
                            "show_type": 'web',
                            "download_token": '',
                        }
                    else:
                        reference = {
                            "chunk": source.content_or_path,
                            "source_or_url": ref.split('/')[-1][0:12] + '..',
                            "show_type": 'local',
                            "download_token": '',
                        }
                    references.append(reference)
            data = {
                "_id": req_id,
                "stage": sess.stage,
                "references": references[0:assistant.resource.reranker.topn],
                "delta": sess.delta,
            }

            pipeline['status'] = status
            pipeline['data'] = data
            yield f"data:{json.dumps(pipeline, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/v2/exemplify")
async def examplify(talk_seed: Talk_seed):
    global analogy
    if analogy:
        return await analogy.process(query=talk_seed.user)
    return '{}'


@app.post("/v2/download")
async def download(token: Token):
    return 'deprecated'


def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(
        description='SerialPipeline or Parallel Pipeline.')
    parser.add_argument('--work_dir',
                        type=str,
                        default='workdir',
                        help='Working directory.')
    parser.add_argument('--config_path',
                        default='config.ini',
                        type=str,
                        help='Configuration path. Default value is config.ini')
    parser.add_argument(
        '--pipeline',
        type=str,
        choices=['serial', 'parallel'],
        default='parallel',
        help=
        'Select pipeline type for difference scenario, default value is `parallel`'
    )
    parser.add_argument('--port', type=int, default=23333, help='bind port')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    # setup chat service
    if 'parallel' in args.pipeline:
        assistant = ParallelPipeline(work_dir=args.work_dir,
                                     config_path=args.config_path)
    elif 'serial' in args.pipeline:
        assistant = SerialPipeline(work_dir=args.work_dir,
                                   config_path=args.config_path)

    api_data_dir = '/home/khj/workspace/HuixiangDou/apidata/'
    analogy = ExampleAnalogy(resource=assistant.resource,
                             api_data_dir=api_data_dir)

    uvicorn.run(app, host='0.0.0.0', port=args.port, log_level='info')
