import argparse
import json
import os
import time
import pdb
from multiprocessing import Process, Value
import asyncio
import cv2
import gradio as gr
import pytoml
from loguru import logger
from typing import List
from huixiangdou.primitive import Query
from huixiangdou.service import ErrorCode
from huixiangdou.pipeline import SerialPipeline, ParallelPipeline, FeatureStore, write_back_config_threshold
import json
from datetime import datetime


def ymd():
    now = datetime.now()
    date_string = now.strftime("%Y-%m-%d")
    os.makedirs(date_string, exist_ok=True)
    return date_string


def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='ParallelPipeline.')
    parser.add_argument('--work_dir',
                        type=str,
                        default='workdir',
                        help='Working directory.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        type=str,
        help='ParallelPipeline configuration path. Default value is config.ini'
    )
    parser.add_argument('--placeholder',
                        type=str,
                        default='百草园里有什么？',
                        help='Placeholder for user query.')
    parser.add_argument('--image', action='store_true', default=True, help='')
    parser.add_argument('--no-image',
                        action='store_false',
                        dest='image',
                        help='Close some components for readthedocs.')
    parser.add_argument(
        '--theme',
        type=str,
        default='soft',
        help=
        'Gradio theme, default value is `soft`. Open https://www.gradio.app/guides/theming-guide for all themes.'
    )

    args = parser.parse_args()
    return args


language = 'en'
enable_web_search = False
enable_code_search = True
pipeline = 'serial'
main_args = None
assistant = None


def on_language_changed(value: str):
    global language
    language = value
    return f'Switch to {value}'


def on_web_search_changed(value: str):
    global enable_web_search
    print(value)
    if 'no' in value:
        enable_web_search = False
    else:
        enable_web_search = True
    return f'Web search set to {enable_web_search}'


def on_code_search_changed(value: str):
    global enable_code_search
    print(value)
    if 'no' in value:
        enable_code_search = False
    else:
        enable_code_search = True
    return f'Code search set to {enable_code_search}'


def format_refs(refs: List[str]):
    refs_filter = list(set(refs))
    if len(refs) < 1:
        return ''
    text = ''
    if language == 'zh_cn':
        text += '参考资料：\r\n'
    else:
        text += '**References:**\r\n'

    for file_or_url in refs_filter:
        text += '* {}\r\n'.format(file_or_url)
    text += '\r\n'
    return text


def reinit_assistant():
    global assistant
    global pipeline
    global main_args
    if 'serial' in pipeline:
        assistant = SerialPipeline(work_dir=main_args.work_dir,
                                   config_path=main_args.config_path)
    else:
        assistant = ParallelPipeline(work_dir=main_args.work_dir,
                                     config_path=main_args.config_path)


async def add_dir(dir: str):
    global assistant
    resource = assistant.resource
    store = FeatureStore(resource=resource, work_dir=main_args.work_dir)
    scan_files = store.file_opr.scan_dir(dir)
    if len(scan_files) < 1:
        return 'no valid files found'
    store.preprocess(files=scan_files)
    store.file_opr.summarize(scan_files)
    
    await store.init(files=scan_files)
    await write_back_config_threshold(resource=resource,
                                      work_dir=main_args.work_dir,
                                      config_path=main_args.config_path)
    reinit_assistant()
    return 'success'


async def drop_db():
    global workdir
    global assistant
    resource = assistant.resource
    store = FeatureStore(resource=resource, work_dir=main_args.work_dir)

    await store.remove_knowledge()
    reinit_assistant()
    return 'success'


async def predict(text: str, image: str):
    global language
    global enable_web_search
    global main_args
    global assistant

    if not text:
        text = main_args.placeholder

    if image is not None:
        filename = 'image.png'
        image_path = os.path.join(main_args.work_dir, filename)
        cv2.imwrite(image_path, image)
    else:
        image_path = None

    query = Query(text=text,
                  image=image_path,
                  enable_web_search=enable_web_search,
                  enable_code_search=enable_code_search)

    if not assistant.is_initialized():
        if language == 'zh_cn':
            yield "知识库未准备好，请先上传数据。"
        else:
            yield "The knowledge base is not ready, please upload."
        return

    args = {'query': query, 'history': [], 'language': language}

    sentence = ''
    async for sess in assistant.generate(**args):
        if sentence == '' and sess.fused_reply:
            sentence = '\n'.join(sess.references()) + '\n'

        if len(sess.delta) > 0:
            sentence += sess.delta
            print('{}'.format(sess.delta), end="")
            yield sentence

    print('yield2 {}'.format(sentence))
    yield sentence


# def build_feature_store(main_args):
#     if os.path.exists('workdir'):
#         logger.warning('feature_store `workdir` already exist, skip')
#         return
#     logger.info('start build feature_store..')
#     os.system(
#         'python3 -m huixiangdou.service.feature_store --config_path {}'.format(
#             main_args.config_path))

if __name__ == '__main__':
    main_args = parse_args()

    show_image = True
    radio_options = ["serial", "parallel"]

    if not main_args.image:
        show_image = False

    themes = {
        'soft': gr.themes.Soft(),
        'monochrome': gr.themes.Monochrome(),
        'base': gr.themes.Base(),
        'default': gr.themes.Default(),
        'glass': gr.themes.Glass()
    }
    if main_args.theme in themes:
        theme = themes[main_args.theme]
    else:
        theme = gr.themes.Soft()

    if 'serial' in pipeline:
        assistant = SerialPipeline(work_dir=main_args.work_dir,
                                   config_path=main_args.config_path)
    else:
        assistant = ParallelPipeline(work_dir=main_args.work_dir,
                                     config_path=main_args.config_path)

    with gr.Blocks(theme=theme,
                   title='HuixiangDou AI assistant',
                   analytics_enabled=True) as demo:
        with gr.Row():
            gr.Markdown(
                """
            #### [HuixiangDou](https://github.com/internlm/huixiangdou) AI assistant
            """,
                label='Reply',
                header_links=True,
                line_breaks=True,
            )

        with gr.Row():
            ui_language = gr.Radio(["en", "zh_cn"],
                                   label="Language",
                                   info="Use `en` by default")
            ui_web_search = gr.Radio(["no", "yes"],
                                     label="Enable web search",
                                     info="Disable by default")
            ui_code_search = gr.Radio(["yes", "no"],
                                      label="Enable code search",
                                      info="Enable by default")

        with gr.Row():
            ui_file_dir = gr.TextArea(
                label='File directory',
                show_copy_button=True,
                placeholder='Such as `/path/to/your/documents/`',
                lines=1)
            
            with gr.Column():
                ui_file_button = gr.Button('Add file directory')
                ui_drop_button = gr.Button('Drop database')

        with gr.Row():
            input_question = gr.TextArea(label='Input your question',
                                         placeholder=main_args.placeholder,
                                         show_copy_button=True,
                                         lines=9)
            input_image = gr.Image(
                label=
                '[Optional] Image-text retrieval needs `config-multimodal.ini`',
                render=show_image)

        with gr.Row():
            run_button = gr.Button()

        with gr.Row():
            result = gr.Markdown(
                '>Text reply or inner status callback here, depends on `pipeline type`',
                label='Reply',
                show_label=True,
                header_links=True,
                line_breaks=True,
                show_copy_button=True)
            # result = gr.TextArea(label='Reply', show_copy_button=True, placeholder='Text Reply or inner status callback, depends on `pipeline type`')

        ui_language.change(fn=on_language_changed,
                           inputs=ui_language,
                           outputs=[result])

        ui_web_search.change(fn=on_web_search_changed,
                             inputs=ui_web_search,
                             outputs=[result])
        ui_code_search.change(fn=on_code_search_changed,
                              inputs=ui_code_search,
                              outputs=[result])
        ui_file_button.click(fn=add_dir, inputs=ui_file_dir, outputs=[result])
        ui_drop_button.click(fn=drop_db, inputs=[], outputs=[result])
        run_button.click(predict, [input_question, input_image], [result])

    demo.queue()
    demo.launch(share=False, server_name='0.0.0.0', debug=True)
