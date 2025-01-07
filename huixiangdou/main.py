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
    queries = [('百草园里有什么？', '')]
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

    while True:
        user_input = input(
            "🔆 Input your question here, type `bye` for exit:\n")
        if 'bye' in user_input:
            break

        sess = None
        for sess in assistant.generate(query=user_input,
                                       history=[],
                                       groupname=''):
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

        return web.json_response({
            'code': int(sess.code),
            'reply': sess.format()
        })

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
    assistant = SerialPipeline(work_dir=args.work_dir,
                               config_path=args.config_path)

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
