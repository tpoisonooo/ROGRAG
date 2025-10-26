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
from huixiangdou.service import ErrorCode, RetrieveResource
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


language = 'zh_cn'
enable_web_search = False
enable_code_search = True
pipeline = 'parallel'
main_args = None
resource = None
ui_allfiles = None

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


def reinit():
    global main_args
    global resource
    
    resource = RetrieveResource(main_args.config_path)


def allfiles():
    from huixiangdou.service import ChunkSQL
    chunksql = ChunkSQL(os.path.join(main_args.work_dir, 'db_chunk')) 
    names = chunksql.listall()
    namestr = '\n'.join(names)
    return namestr


async def add_files(files: List, progress=gr.Progress()):
    if not files:
        return '没有上传任何文件', allfiles()
    global resource
    store = FeatureStore(resource=resource, work_dir=main_args.work_dir)
    scan_files = store.file_opr.scan_files(files)
    if len(scan_files) < 1:
        return '未上传任何文件', allfiles()

    progress(0, desc="转换中")
    store.preprocess(files=scan_files)
    store.file_opr.summarize(scan_files)
    
    progress(0.3, desc="开始建库")
    async for step in store.init(files=scan_files):
        progress(0.3 + 0.3 * step, desc="索引中")

    progress(0.9, desc="重新初始化")
    reinit()
    progress(1.0, desc="完成")
    return '扩展成功', allfiles() 


async def drop_db():
    global workdir
    global resource
    store = FeatureStore(resource=resource, work_dir=main_args.work_dir)

    await store.remove_knowledge()
    reinit()
    return '删除成功', allfiles()


async def predict(text: str):
    global language
    global enable_web_search
    global main_args
    global resource
    global pipeline

    if not text:
        text = main_args.placeholder

    image_path = None

    query = Query(text=text,
                  image=image_path,
                  enable_web_search=enable_web_search,
                  enable_code_search=enable_code_search)

    if 'serial' in pipeline:
        assistant = SerialPipeline(resouce=resource)
    else:
        assistant = ParallelPipeline(resouce=resource)

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

    reinit()
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

    with gr.Blocks(theme=theme,
                   title='HuixiangDou AI assistant',
                   analytics_enabled=True) as demo:
        with gr.Row():
            gr.Markdown(
                """
            #### “智幄明航”动态通航安全监管智能体
            """,
                label='Reply',
                header_links=True,
                line_breaks=True,
            )

        with gr.Row():
            ui_language = gr.Radio(["en", "zh_cn"],
                                   label="语言",
                                   info="默认使用 `zh_cn`")
            ui_web_search = gr.Radio(["no", "yes"],
                                     label="网络搜索",
                                     info="默认关闭")
            ui_code_search = gr.Radio(["yes", "no"],
                                      label="代码检索",
                                      info="默认开启")

        with gr.Row():
            ui_allfiles = gr.TextArea(label='当前知识库文件列表', value=allfiles(), lines=11)
            
            with gr.Column():
                ui_file_button = gr.Button('扩展知识库')
                ui_drop_button = gr.Button('清空知识库')
                files = gr.Files(file_count="multiple", label="请选择要增加的文件（支持多选）")

        with gr.Row():
            input_question = gr.TextArea(label='输入问题',
                                         placeholder=main_args.placeholder,
                                         show_copy_button=True,
                                         lines=1)
        #    input_image = gr.Image(
        #        label=
        #        '[可选] 图文检索需配置 `config-multimodal.ini`',
        #        render=show_image)

        with gr.Row():
            run_button = gr.Button('运行')

        with gr.Column():
            system_state = gr.Markdown(
                '>这里是系统状态',
                label='状态',
                show_label=True,
                header_links=True,
                line_breaks=True,
                show_copy_button=True)

            reply_question = gr.Markdown(
                '>这里是问题回复',
                label='答复',
                show_label=True,
                header_links=True,
                line_breaks=True,
                show_copy_button=True)
            # result = gr.TextArea(label='Reply', show_copy_button=True, placeholder='Text Reply or inner status callback, depends on `pipeline type`')

        ui_language.change(fn=on_language_changed,
                           inputs=ui_language,
                           outputs=[system_state])

        ui_web_search.change(fn=on_web_search_changed,
                             inputs=ui_web_search,
                             outputs=[system_state])
        ui_code_search.change(fn=on_code_search_changed,
                              inputs=ui_code_search,
                              outputs=[system_state])
        ui_file_button.click(fn=add_files, inputs=files, outputs=[system_state, ui_allfiles])
        ui_drop_button.click(fn=drop_db, inputs=[], outputs=[system_state, ui_allfiles])
        run_button.click(predict, [input_question], reply_question)

    demo.queue()
    demo.launch(share=False, server_name='0.0.0.0', server_port=8888, debug=True)
