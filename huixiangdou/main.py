#!/usr/bin/env python3
"""HuixiangDou binary."""
import argparse
import os
import time

import pytoml
import requests
from aiohttp import web
from loguru import logger
from termcolor import colored

from .service import ErrorCode
from .pipeline import ParallelPipeline, SerialPipeline
from .primitive import always_get_an_event_loop, Query

def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='SerialPipeline.')
    parser.add_argument('--work_dir',
                        type=str,
                        default='workdir',
                        help='Working directory.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        type=str,
        help='SerialPipeline configuration path. Default value is config.ini')
    parser.add_argument('--standalone',
                        action='store_true',
                        default=False,
                        help='Auto deploy required Hybrid LLM Service.')
    args = parser.parse_args()
    return args


def check_env(args):
    """Check or create config.ini and logs dir."""
    os.makedirs('logs', exist_ok=True)
    CONFIG_NAME = 'config.ini'
    CONFIG_URL = 'https://raw.githubusercontent.com/InternLM/HuixiangDou/main/config.ini'  # noqa E501
    if not os.path.exists(CONFIG_NAME):
        logger.warning(
            f'{CONFIG_NAME} not found, download a template from {CONFIG_URL}.')

        try:
            response = requests.get(CONFIG_URL, timeout=60)
            response.raise_for_status()
            with open(CONFIG_NAME, 'wb') as f:
                f.write(response.content)
        except Exception as e:
            logger.error(f'Failed to download file due to {e}')
            raise e

    os.makedirs(args.work_dir, exist_ok=True)


async def show(assistant, _: dict):
    # queries = [('Y两优1号的秧田基肥使用的是什么肥料？', '这是一道关于农业的单选题，你作为一名农业的大学生，应当按以下规则作答：请从A,B,C,D中选出一个唯一的正确选项，并回答。\n注意，你的回答应当仅包括正确选项的字母，不要包含多余的空格或其他字符。\n例如：\n正确答案：C\n请你严格按照这个格式回答，不要有额外输出。\n问题：\nY两优1号的秧田基肥使用的是什么肥料？\nA. 尿素\nB. 氯化钾\nC. 水稻专用肥\nD. 金稻龙药肥')]
    # queries = [('Y两优1号的秧田基肥使用的是什么肥料？', '这是一道关于农业的单选题，你作为一名农业的大学生，应当按以下规则作答：请从A,B,C,D中选出一个唯一的正确选项，并回答。请先给出解释，然后给出答案。\n问题：\nY两优1号的秧田基肥使用的是什么肥料？\nA. 尿素\nB. 氯化钾\nC. 水稻专用肥\nD. 金稻龙药肥')]
    # queries = [('汕优63是由哪个农科所育成的水稻品种', '这是一道关于农业的单选题，你作为一名农业的大学生，应当按以下规则作答：请从A,B,C,D中选出一个唯一的正确选项，并回答。\n注意，你的回答应当仅包括正确选项的字母，不要包含多余的空格或其他字符。\n例如：\n正确答案：C\n请你严格按照这个格式回答，不要有额外输出。\n问题：\n汕优63是由哪个农科所育成的水稻品种？\nA. 江苏南京市农科所\nB. 广东汕头市农科所\nC. 福建三明市农科所\nD. 浙江杭州市农科所')]
    # queries = [('淮稻7号的施肥方法中，分蘖肥应在栽插后多少天施入？', '这是一道关于农业的单选题，你作为一名农业的大学生，应当按以下规则作答：请从A,B,C,D中选出一个唯一的正确选项，并回答。\n注意，你的回答应当仅包括正确选项的字母，不要包含多余的空格或其他字符。\n例如：\n正确答案：C\n请你严格按照这个格式回答，不要有额外输出。\n问题：\n淮稻7号的施肥方法中，分蘖肥应在栽插后多少天施入？\nA. 3-4天\nB. 9-10天\nC. 7-8天\nD. 5-6天')]
    
    # 确实我的  bug queries = [('淮稻7号的施肥方法中，分蘖肥应在栽插后多少天施入？\nA. 3-4天\nB. 9-10天\nC. 7-8天\nD. 5-6天', '这是一道关于农业的单选题，你作为一名农业的大学生，应当按以下规则作答：请从A,B,C,D中选出一个唯一的正确选项，并回答。请先解释理由，然后给出答案\n问题：\n')]
    queries = [('越光的育种母本和父本分别是什么？\nA. 母本为农林22号，父本为农林1号\nB. 母本为农林22号，父本为农林11号\nC. 母本为农林11号，父本为农林22号\nD. 母本为农林1号，父本为农林22号', '这是一道关于农业的单选题，你作为一名农业的大学生，应当按以下规则作答：请从A,B,C,D中选出一个唯一的正确选项，并回答。请先解释理由，然后给出答案\n问题：\n')]

    # queries = [('黄华占适宜在哪个省份的稻瘟病轻发地区作单季籼稻种植？\nA. 浙江省\nB. 陕西省\nC. 新疆省\nD. 重庆市', '这是一道关于农业的单选题，你作为一名农业的大学生，应当按以下规则作答：请从A,B,C,D中选出一个唯一的正确选项，并回答。请先解释理由，然后给出答案\n问题：\n')  GT 有问题
            #    ('宜香优2115是在哪一年通过国家稻品种审定标准的？', '宜香优2115是在哪一年通过国家稻品种审定标准的？')]  GT 有冲突

    print(colored('Running some examples..', 'yellow'))
    for q in queries:
        print(colored('[Example]' + q[0], 'yellow'))

    for q in queries:
        sess = None
        for_retrieve = q[0].split('\nA')[0]
        for_question = q[0] + q[1]
        query = Query(text=for_retrieve, generation_question=for_question)
        async for sess in assistant.generate(query=query, history=[]):
            logger.info(sess.stage)
            pass

        logger.info('\n' + sess.format())

    while False:
        user_input = input("🔆 Input your question here, type `bye` for exit:\n")
        if 'bye' in user_input:
            break

        for sess in assistant.generate(query=user_input, history=[], groupname=''):
            pass
        
        print('\n' + sess.format())

def lark_group_recv_and_send(assistant, fe_config: dict):
    from .frontend import (is_revert_command, revert_from_lark_group,
                           send_to_lark_group)
    msg_url = fe_config['webhook_url']
    lark_group_config = fe_config['lark_group']
    sent_msg_ids = []

    while True:
        # fetch a user message
        resp = requests.post(msg_url, timeout=10)
        resp.raise_for_status()
        json_obj = resp.json()
        if len(json_obj) < 1:
            # no user input, sleep
            time.sleep(2)
            continue

        logger.debug(json_obj)
        query = json_obj['content']

        if is_revert_command(query):
            for msg_id in sent_msg_ids:
                error = revert_from_lark_group(msg_id,
                                               lark_group_config['app_id'],
                                               lark_group_config['app_secret'])
                if error is not None:
                    logger.error(
                        f'revert msg_id {msg_id} fail, reason {error}')
                else:
                    logger.debug(f'revert msg_id {msg_id}')
                time.sleep(0.5)
            sent_msg_ids = []
            continue

        for sess in assistant.generate(query=query, history=[], groupname=''):
            pass
        if sess.code == ErrorCode.SUCCESS:
            json_obj['reply'] = sess.format()
            error, msg_id = send_to_lark_group(
                json_obj=json_obj,
                app_id=lark_group_config['app_id'],
                app_secret=lark_group_config['app_secret'])
            if error is not None:
                raise error
            sent_msg_ids.append(msg_id)
        else:
            logger.debug(f'{sess.code} for the query {query}')


def wechat_personal_run(assistant, fe_config: dict):
    """Call assistant inference."""

    async def api(request):
        input_json = await request.json()
        logger.debug(input_json)

        query = input_json['query']

        if type(query) is dict:
            query = query['content']

        sess = None
        for sess in assistant.generate(query=query, history=[], groupname=''):
            pass

        return web.json_response({'code': int(sess.code), 'reply': sess.format()})

    bind_port = fe_config['wechat_personal']['bind_port']
    app = web.Application()
    app.add_routes([web.post('/api', api)])
    web.run_app(app, host='0.0.0.0', port=bind_port)

def run():
    """Automatically download config, start llm server and run examples."""
    args = parse_args()

    # query by worker
    with open(args.config_path, encoding='utf8') as f:
        fe_config = pytoml.load(f)['frontend']
    logger.info('Config loaded.')
    assistant = SerialPipeline(work_dir=args.work_dir, config_path=args.config_path)

    loop = always_get_an_event_loop()

    fe_type = fe_config['type']
    if fe_type == 'none':
        loop.run_until_complete(show(assistant, fe_config))
        
    elif fe_type == 'lark_group':
        lark_group_recv_and_send(assistant, fe_config)
        
    elif fe_type == 'wechat_personal':
        wechat_personal_run(assistant, fe_config)
        
    elif fe_type == 'wechat_wkteam':
        from .frontend import WkteamManager
        manager = WkteamManager(args.config_path)
        manager.loop(assistant)
        
    else:
        logger.info(
            f'unsupported fe_config.type {fe_type}, please read `config.ini` description.'  # noqa E501
        )

if __name__ == '__main__':
    run()
