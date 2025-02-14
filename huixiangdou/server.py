import argparse
import os
import time

import pytoml
import requests
from aiohttp import web
from loguru import logger
from termcolor import colored

from ..pipeline import SerialPipeline, ParallelPipeline
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
            query = query, 
            history = talk_seed.history,
            language = talk_seed.language,
            enable_web_search = talk_seed.enable_web_search,                          
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
                    "chunk": sess.context_chunk[i],
                    "source_or_url": ref,
                    "show_type": show_type,
                    "download_token": os.path.join("seedllm", ref) if show_type == 'fasta' else '',
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

    if type(assistant) is SerialPipeline:
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    else:
        return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/v2/exemplify")
async def huixiangdou_stream(talk_seed: Talk_seed):

    global assistant
    query = Query(talk_seed.user)

     # 用户词典文件路径  
    jieba_variety_path = 'huixiangdou/api/data/variety/jieba_variety.txt'
    jieba_variety_pinyin_path ='huixiangdou/api/data/variety/jieba_variety_pinyin.txt'
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
    return 'deprecated'

def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='SerialPipeline or Parallel Pipeline.')
    parser.add_argument('--work_dir',
                        type=str,
                        default='workdir',
                        help='Working directory.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        type=str,
        help='Configuration path. Default value is config.ini')
    parser.add_argument('--pipeline', type=str, choices=['serial', 'parallel'], default='parallel', 
                        help='Select pipeline type for difference scenario, default value is `parallel`')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    # setup chat service
    if 'parallel' in args.pipeline:
        assistant = ParallelPipeline(work_dir=args.work_dir, config_path=args.config_path)
    elif 'serial' in args.pipeline:
        assistant = SerialPipeline(work_dir=args.work_dir, config_path=args.config_path)
    uvicorn.run(app, host='0.0.0.0', port=23333, log_level='info')
