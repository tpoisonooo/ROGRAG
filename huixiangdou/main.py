#!/usr/bin/env python3
"""HuixiangDou binary."""
import argparse
import os

import pytoml
import requests
from loguru import logger
from termcolor import colored

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
            pass

        logger.info('\n' + sess.format())

    while True:
        user_input = input(
            "🔆 Input your question here, type `bye` for exit:\n")
        
        # Not null
        if not user_input or user_input.strip() == '':
            print("Input cannot be empty, please try again.")
            continue

        if 'bye' in user_input:
            break

        sess = None
        async for sess in assistant.generate(query=user_input,
                                       history=[]):
            pass

        print('\n' + sess.format())


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
