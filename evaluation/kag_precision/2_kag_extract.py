from huixiangdou.primitive import LLM, always_get_an_event_loop, Query
from huixiangdou.pipeline import ParallelPipeline, SerialPipeline
from loguru import logger
import os
import json
import pdb
import argparse
import datetime

def newdir():
    now = datetime.datetime.now()
    # 格式化日期和时间字符串
    # 例如：2023-12-25_14
    date_time_str = now.strftime("%Y-%m-%d_%H")

    # 创建目录路径
    dir_path = f"./{date_time_str}"
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Knowledge retrieval testcase.')
    parser.add_argument('--workdir',
                        type=str,
                        default='workdir',
                        help='Working directory.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        help='Configuration path. Default value is config.ini')
    parser.add_argument(
        '--small',
        type=str,
        default=None,
        help='Small dataset for dev.')
    parser.add_argument(
        '--datadir',
        type=str,
        default='/data/khj/workspace/SeedBench/data/zero-shot',
        help='SeedBench datadir for test.')
    parser.add_argument(
        '--outdir',
        type=str,
        default=None
    )
    parser.add_argument(
        '--pipeline',
        default='parallel',
        help='Worker pipeline.')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()

    if 'parallel' in args.pipeline:
        cls = ParallelPipeline
    else:
        cls = SerialPipeline
    # 指定你的base目录
    assistant = cls(work_dir=args.workdir, config_path=args.config_path)

    # 遍历base目录
    modelname = assistant.resource.llm.default_model_info()['model']
    modelname = modelname.split('/')[-1]

    if not args.outdir:
        args.outdir = newdir()
    output_file = os.path.join(args.outdir, '2_hybrid_zero_shot_kag_seedllm_{}.jsonl'.format(modelname))
    if os.path.exists(output_file):
        raise Exception(f'{output_file} already exists')

    # get looper
    loop = always_get_an_event_loop()

    for root, dirs, files in os.walk(args.datadir):
        for file in files:
            # 检查文件扩展名是否为.json
            if not file.endswith('.json'):
                continue

            if args.small:
                # 如果只测小规模问题，其他问题就跳过
                if args.small not in file:
                    continue

            file_path = os.path.join(root, file)
            
            # 打开并读取JSON文件
            data = {}
            with open(file_path, 'r', encoding='utf-8') as fin:
                datas = json.load(fin)

                for data in datas:
                    question = data['question']
                    generation_question = data['instruction'] + '\n' + data['question']
                    answer = data['answer']
                    task = data['task_type']

                    async def wrap_async_run(query):
                        response = ''
                        node = ''
                        async for sess in assistant.generate(query=query, history=[], language='zh_cn'):
                            response = sess.response
                            node = sess.node
                            logger.info(sess.stage, response)

                        debugfile = os.path.join(args.outdir, 'debug.jsonl')
                        sess.debug['gt'] = answer
                        sess.debug['input'] = generation_question
                        with open(debugfile, 'a') as f:
                            jsonstr = json.dumps(sess.debug, ensure_ascii=False)
                            f.write(jsonstr)
                            f.write('\n')
                        return response, node

                    q = Query(text=question, generation_question=generation_question)
                    output, node = loop.run_until_complete(wrap_async_run(query=q))
                    json_str = json.dumps({"input":generation_question, "output": output, "gt": answer, "task": task, "source": file, "node":node}, ensure_ascii=False)
                    with open(output_file, 'a') as fout:
                        fout.write(json_str)
                        fout.write('\n')
                        fout.flush()
