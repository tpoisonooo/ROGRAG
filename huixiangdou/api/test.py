import pandas as pd
from loguru import logger
from ..primitive import LLM
import argparse

#解析参数
def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='Worker.')
    # parser.add_argument('--work_dir',
    #                     type=str,
    #                     default='workdir',
    #                     help='Working directory.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        type=str,
        help='Worker configuration path. Default value is config.ini')
    # parser.add_argument('--standalone',
    #                     action='store_true',
    #                     default=False,
    #                     help='Auto deploy required Hybrid LLM Service.')
    args = parser.parse_args()
    return args


# 相似度计算
def jaccard_similarity(str1: str, str2: str) -> float:  
    set1 = set(str1.lower().split())  
    set2 = set(str2.lower().split())  
    intersection = set1.intersection(set2)  
    union = set1.union(set2)  
    return len(intersection) / len(union) if union else 0 

# 生成新问题
class newquestionNode:  
    def __init__(self, config_path: str, csv_path: str, threshold: float = 0.3, language: str = 'zh'):
        self.config_path = config_path
        self.llm = LLM(config_path=config_path)
        self.csv_path = csv_path  
        self.threshold = threshold 
        self.language = language 
        self.data = pd.read_csv(csv_path)  # 假设问题在第三、四、五列  
        if language == 'zh':
            self.GENERATE_TEMPLATE = '问题：“{}” \n 请生成三个与该问题尽可能相似的问题'  # noqa E501
        else:
            self.GENERATE_TEMPLATE = 'Question: "{}"\n Please generate three questions that are as similar as possible to the problem.'  # noqa E501
  
    def process(self, query, answer):  
        
        # print("Query:" + sess.query)
        # print("response:" + sess.response)
        # keywords = sess.query + sess.response  
        keywords = query

        similar_questions = []  
        for index, row in self.data.iterrows():  
            # 假设我们将第三、四、五列视为可能的问题  
            for col in range(2, 6):  
                question = row[col]  
                similarity = jaccard_similarity(keywords, question)  
                if similarity >= self.threshold:  
                    # 返回该行除当前列外的其他列（假设第一列是ID，我们不需要它）  
                    other_questions = [row[i] for i in range(2, 6) if i != col]  
                    similar_questions.append(tuple(other_questions))  
                    break  # 如果找到一个相似问题就跳出循环  
  
        if not similar_questions:  
            # answer the question
            prompt = self.GENERATE_TEMPLATE.format(query)
            # response = self.llm.generate_response(prompt=prompt, history=sess.history, backend='puyu')
            self.llm = LLM(config_path=self.config_path) 
            response = self.llm.generate_response(prompt=prompt, backend='remote')
            # 为了简化，我们直接返回一些模拟的问题  
            print(response)
            # print("模拟问题1", "模拟问题2", "模拟问题3")
        else:
            print(similar_questions)
        return similar_questions

def run():
    args = parse_args()
    logger.info('Config loaded.')

    # assistant = Worker(config_path=args.config_path)
    queries = ['请问黄华占的选育过程是怎样的？', '请问明天天气如何？']
    answers = ['111111','22222']
    for i in range(len(queries)):
        new3question = newquestionNode(args.config_path, "/root/wangzhefan/api/data/variety_question_template.csv")
        # print(queries[i], answers[i])
        new3question.process(queries[i], answers[i])
        # code, reply, references = assistant.generate(query=query,
        #                                              history=[],
        #                                              groupname='')

if __name__ == '__main__':
    run()