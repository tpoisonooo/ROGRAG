import argparse
import os
import time

import pytoml
import requests
from aiohttp import web
from loguru import logger
from termcolor import colored

from .service import ErrorCode, SerialPipeline, ParallelPipeline, start_llm_server
from .primitive import Query, Pair, Token
import asyncio
from fastapi import FastAPI, APIRouter
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import json
from typing import List
import uuid
from .api import TextSimilarity, newquestionNode
import jieba
import oss2
from oss2.credentials import EnvironmentVariableCredentialsProvider

assistant = None
app = FastAPI(docs_url='/')


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


@app.post("/v2/chat")
async def huixiangdou_stream(talk_seed: Talk_seed):
    global assistant
    query = Query(text=talk_seed.user)

    pipeline = {}

    async def event_stream():
        async for sess in assistant.generate(
                query=query,
                history=talk_seed.history,
                language=talk_seed.language,
                enable_web_search=talk_seed.enable_web_search,
        ):
            status = {
                "code": int(sess.code),
                "error": sess.error,
            }

            references = []
            fasta_suffix = '.fasta'

            for i, ref in enumerate(sess.references):
                if '://' in sess.references[i]:
                    show_type = 'web'
                elif ref.endswith(fasta_suffix):
                    show_type = 'fasta'
                else:
                    show_type = 'local'

                reference = {
                    "chunk":
                    sess.context_chunk[i],
                    "source_or_url":
                    ref,
                    "show_type":
                    show_type,
                    "download_token":
                    os.path.join("seedllm", ref)
                    if show_type == 'fasta' else '',
                }
                references.append(reference)

            data = {
                "_id": str(uuid.uuid4()),
                "stage": sess.stage,
                "references": references,
                "delta": sess.delta,
            }

            pipeline['status'] = status
            pipeline['data'] = data
            # print(sess)
            yield f"data:{json.dumps(pipeline, ensure_ascii=False)}\n\n"

    async def event_stream_async():
        sentence = ''
        async for sess in assistant.generate(
                query=query,
                history=talk_seed.history,
                language=talk_seed.language,
                enable_web_search=talk_seed.enable_web_search,
        ):
            if sentence == '' and len(sess.references) > 0:
                sentence = format_refs(sess.references)

            if len(sess.delta) > 0:
                sentence += sess.delta
                yield sentence

    if type(assistant) is SerialPipeline:
        return StreamingResponse(event_stream(),
                                 media_type="text/event-stream")
    else:
        return StreamingResponse(event_stream(),
                                 media_type="text/event-stream")


@app.post("/v2/exemplify")
async def huixiangdou_stream(talk_seed: Talk_seed):

    global assistant
    query = Query(talk_seed.user)

    # 用户词典文件路径
    jieba_variety_path = 'huixiangdou/api/data/variety/jieba_variety.txt'
    jieba_variety_pinyin_path = 'huixiangdou/api/data/variety/jieba_variety_pinyin.txt'
    jieba_gene_path = 'huixiangdou/api/data/gene/jieba_gene.txt'
    config_path = 'config.ini'
    variety_path = 'huixiangdou/api/data/variety/Rice_Variety_merged.csv'
    variety_pinyin_path = 'huixiangdou/api/data/variety/Rice_Variety_merged_pinyin.csv'
    gene_path = 'huixiangdou/api/data/gene/rice_reference_genome_annotation_20240903.csv'
    variety_template_path = 'huixiangdou/api/data/variety/variety_question_template.csv'
    gene_template_path = 'huixiangdou/api/data/gene/gene_question_template.csv'

    jieba.load_userdict(jieba_gene_path)
    jieba.load_userdict(jieba_variety_path)
    jieba.load_userdict(jieba_variety_pinyin_path)

    question_handler = newquestionNode(config_path = config_path, variety_path = variety_path, variety_pinyin_path = variety_pinyin_path, \
                                       gene_path = gene_path, variety_template_path = variety_template_path, gene_template_path = gene_template_path)
    response = question_handler.process(query)
    # return json.dumps(response, ensure_ascii=False)
    return response


@app.post("/v2/download")
async def huixiangdou_stream(token: Token):

    # 从环境变量中获取访问凭证。运行本代码示例之前，请确保已设置环境变量OSS_ACCESS_KEY_ID和OSS_ACCESS_KEY_SECRET。
    os.environ['OSS_ACCESS_KEY_ID'] = 'LTAI5tHsCF8Z8sf2nYVEaRtK'  #AccessKey ID
    os.environ[
        'OSS_ACCESS_KEY_SECRET'] = 'Spkho47sJ4gNDnOz1LQCSvuOPlJEQq'  #AccessKey Secret
    auth = oss2.ProviderAuth(EnvironmentVariableCredentialsProvider())

    # yourEndpoint填写Bucket所在地域对应的Endpoint。以华东1（杭州）为例，Endpoint填写为https://oss-cn-hangzhou.aliyuncs.com。
    # 填写Bucket名称，例如examplebucket。
    bucket = oss2.Bucket(auth, 'https://oss-cn-shanghai.aliyuncs.com',
                         'openmmlab-deploee')
    # 填写Object完整路径，例如exampledir/exampleobject.txt。Object完整路径中不能包含Bucket名称。

    object_name = token.token
    downloadURL = {}
    status = {}
    headers = dict()
    headers['Accept-Encoding'] = 'gzip'
    # 指定HTTP查询参数。
    params = dict()
    # 设置单链接限速，单位为bit，例如限速100 KB/s。
    # params['x-oss-traffic-limit'] = str(100 * 1024 * 8)
    # 指定IP地址或者IP地址段。
    # params['x-oss-ac-source-ip'] = "127.0.0.1"
    # 指定子网掩码中1的个数。
    # params['x-oss-ac-subnet-mask'] = "32"
    # 指定VPC ID。
    # params['x-oss-ac-vpc-id'] = "vpc-t4nlw426y44rd3iq4xxxx"
    # 指定是否允许转发请求。
    # params['x-oss-ac-forward-allow'] = "true"
    # 生成下载文件的签名URL，有效时间为60秒。
    # 生成签名URL时，OSS默认会对Object完整路径中的正斜线（/）进行转义，从而导致生成的签名URL无法直接使用。
    # 设置slash_safe为True，OSS不会对Object完整路径中的正斜线（/）进行转义，此时生成的签名URL可以直接使用。
    url = bucket.sign_url('GET',
                          object_name,
                          60,
                          slash_safe=True,
                          headers=headers,
                          params=params)

    try:
        # 发起 GET 请求
        response = requests.get(url,
                                headers=headers,
                                params=params,
                                timeout=60)

        # 检查 HTTP 响应状态码
        if response.status_code == 200:
            status['code'] = 0
            status['error'] = 'None'

        else:
            status['code'] = response.status_code
            status[
                'error'] = f"URL is not valid. HTTP status code:, {response.status_code}"

    except requests.exceptions.RequestException as e:
        # 捕获请求过程中的异常
        status['code'] = 1
        status['error'] = f"Error occurred while accessing the URL:, {e}"

    downloadURL = {'status': status, 'data': {'url': url}}
    return downloadURL


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
        choices=['chat_with_repo', 'chat_in_group'],
        default='chat_with_repo',
        help=
        'Select pipeline type for difference scenario, default value is `chat_with_repo`'
    )
    parser.add_argument('--standalone',
                        action='store_true',
                        default=True,
                        help='Auto deploy required Hybrid LLM Service.')
    parser.add_argument(
        '--no-standalone',
        action='store_false',
        dest='standalone',  # 指定与上面参数相同的目标
        help='Do not auto deploy required Hybrid LLM Service.')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    # start service
    if args.standalone is True:
        # hybrid llm serve
        start_llm_server(config_path=args.config_path)
    # setup chat service
    if 'chat_with_repo' in args.pipeline:
        assistant = ParallelPipeline(work_dir=args.work_dir,
                                     config_path=args.config_path)
    elif 'chat_in_group' in args.pipeline:
        assistant = SerialPipeline(work_dir=args.work_dir,
                                   config_path=args.config_path)
    uvicorn.run(app, host='0.0.0.0', port=23333, log_level='info')
