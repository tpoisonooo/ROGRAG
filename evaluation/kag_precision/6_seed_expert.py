from huixiangdou.primitive import LLM, always_get_an_event_loop, Query
from huixiangdou.pipeline import ParallelPipeline, SerialPipeline
from loguru import logger
import os
import json
import pdb
import argparse
import datetime
import csv

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
        '--datadir',
        type=str,
        default='/home/khj/workspace/HuixiangDou/expert_level_questions/mwf',
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

    output_file = os.path.join(args.outdir, '6_{}_{}_{}.csv'.format(args.datadir.split('/')[-1], modelname, args.pipeline))
    if os.path.exists(output_file):
        raise Exception(f'{output_file} already exists')

    # get looper
    loop = always_get_an_event_loop()

    list_of_row = []
    for root, dirs, files in os.walk(args.datadir):
        csv_files = []
        for file in files:
            if not file.endswith('.csv'):
                continue
            csv_files.append(os.path.join(root, file))
        
        # 打开并读取 csv
        data = {}
        # 打开 csv 文件
        for csv_file_path in csv_files:
            with open(csv_file_path, mode='r', encoding='ISO-8859-1') as file:
                # 创建 csv 读取器对象
                print(file)
                csv_reader = csv.reader(file)
                
                # 读取 csv 文件的表头（假设第一行是表头）
                headers = next(csv_reader)
                print("表头：", headers)
                
                # 逐行读取 csv 文件的内容
                for row in csv_reader:
                    print(row)
                    question = row[0]
                    if not question:
                        continue

                    async def wrap_async_run(query):
                        response = ''
                        node = ''

                        async for sess in assistant.generate(query=query, history=[], language='zh_cn'):
                            response = sess.response
                            node = sess.node
                            logger.info(sess.stage, response)
                        return response, node

                    if not question:
                        pdb.set_trace()
                        continue
                        
                    q = Query(text=question, generation_question=question)
                    output, node = loop.run_until_complete(wrap_async_run(query=q))

                    row.append(output)
                    list_of_row.append(row)
 
    with open(output_file, mode='a', newline='', encoding='utf-8') as fout:
        writer = csv.writer(fout)
        for row in list_of_row:
            writer.writerow(row)
