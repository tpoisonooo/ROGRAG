import pandas as pd
from ..primitive import LLM
import argparse
import jieba
from pypinyin import pinyin, Style
import uuid  # 用于生成唯一ID  
import re

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


# 相似度计算 计算两个字符串之间的杰卡德相似度
class TextSimilarity:
    def __init__(self):
        pass

    def jaccard_similarity_str(self, str1: str, str2: str) -> float:
        set1 = set(jieba.lcut(str1.lower()))  # 使用jieba分词
        set2 = set(jieba.lcut(str2.lower()))  # 注意：中文通常不转换为小写
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union) if union else 0

    def jaccard_similarity_list(self, list1: list, list2: list) -> float:
        set1 = set(list1)
        set2 = set(list2)
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union) if union else 0

    def is_chinese_dominant(self, s, threshold=0.5):
        chinese_count = 0
        total_count = len(s)

        for char in s:
            if '\u4e00' <= char <= '\u9fff':
                chinese_count += 1

        chinese_ratio = chinese_count / total_count
        return chinese_ratio > threshold
  
# 生成新问题
class newquestionNode:  
    def __init__(
        self, 
        config_path: str, 
        variety_path: str, 
        variety_pinyin_path: str, 
        gene_path: str, 
        variety_template_path: str, 
        gene_template_path: str, 
        threshold: float = 0.3, 
        language: str = 'zh'
    ):
        self.config_path = config_path 
        self.threshold = threshold 
        self.language = language 
        #读取问题模板
        self.variety_question = pd.read_csv(variety_template_path)  # 假设问题在第三、四、五列
        self.gene_question = pd.read_csv(gene_template_path)
        #读取物种列表和基因列表
        self.variety = pd.read_csv(variety_path)
        self.variety_pinyin = pd.read_csv(variety_pinyin_path)
        self.gene = pd.read_csv(gene_path)
        self.variety_set = set(self.variety[self.variety.columns[0]].str.lower()).union(set(self.variety_pinyin[self.variety_pinyin.columns[0]].str.lower()))
        self.gene_set = set()
        # 定义分隔符列表  
        separators = [',', '/', '; '] 
        for column in self.gene.columns[:5]:  
            for sep in separators:  
                self.gene_set.update(  
                    item.lower() for row in self.gene[column].astype(str)  
                    for item in row.split(sep) if item  
                )   
        # for column in self.gene.columns[:5]:
        #     self.gene_set.update(self.gene[column].astype(str).str.lower())
        # print('self.gene_set',self.gene_set)
        #llm初始化 
        self.llm = LLM(config_path=self.config_path) 
        if language == 'zh':
            self.GENERATE_TEMPLATE = '问题：“{}” \n 请生成三个与该问题尽可能相似的问题，返回格式为[["问题1"],["问题2"],["问题3"]]'  # noqa E501
            self.ABSTRACT_TEMPLATE = '问题：“{}” \n 请帮我从问题中提取五个关键词'
        else:
            self.GENERATE_TEMPLATE = 'Question: "{}"\n Please generate three questions that are as similar as possible to the problem, with the return format being [["Question 1"], ["Question 2"], ["Question 3"]]'  # noqa E501
            self.ABSTRACT_TEMPLATE = 'Question: "{}"\n Please help me extract five keywords from the question'
  
    def process(self, query, answer = ''):  

        metric = TextSimilarity()
        query = query.text
        
        if metric.is_chinese_dominant(query):
            words = jieba.lcut(query.lower())
        else:
            tokens = re.findall(r'\w+|\?', query.lower())  
            words  = [token for token in tokens if token]    
        # print(words)

        # 查找在self.variety中出现的词  
        matched_word = None
        matched_gene = None
        matched_rice = None 
        question_type = None
        # print('self.gene_set',self.gene_set)
        for word in words:  
            if word in self.gene_set:  
                matched_word = word
            elif word in self.variety_set:
                matched_word = word
            elif word == '水稻' or word =='rice':
                matched_rice = word
            elif word == '基因' or word =='gene':
                matched_gene = word
        
        # print('matched_gene:',matched_gene)
        # print('matched_rice:',matched_rice)
        #如果gene类型和rice同时出现,则检索gene类型
        if matched_word is not None:
            print('检索成功!') 
        elif (matched_rice is not None and matched_gene is None) or (matched_gene is not None and matched_rice is None):
            #如果是关于水稻/基因但没涉及种类，使用大模型生成新问题  
            prompt = self.GENERATE_TEMPLATE.format(query)  
            response = self.llm.chat(prompt=prompt, backend='remote')  
            similar_questions = response
            response_body = {}
            response_body['status'] = {}
            response_body['data'] = {}  
            response_body['status']['code'] = 0  
            response_body['status']['error'] = 'None'
            response_body['data']['_id'] = str(uuid.uuid4())  
            response_body['data']['cases'] = similar_questions
            return response_body
        else:
            # 如果没有特定种类or涉及水稻/基因
            response_body = {}
            response_body['status'] = {}
            response_body['data'] = {}  
            response_body['status']['code'] = 1  
            response_body['status']['error'] = 'Not special specy'
            response_body['data']['_id'] = str(uuid.uuid4())
            response_body['data']['cases'] = []  
            return response_body
            

        key1 = self.variety_question.iloc[1, 1]
        key2 = ''.join(item[0] for item in pinyin(key1, style=Style.NORMAL))
        key3 = self.gene_question.iloc[1, 1].lower()
        key4 = self.gene_question.iloc[1, 1].lower()
        question_type = ""

        # 遍历variety_question的前十行  
        similar_questions = []  
        max_similarity = 0.2 
        best_row = None
        best_col = None
        row_index = -1  
        for index, row in self.variety_question.head(10).iterrows():
            for col in range(2, 6):  # 遍历第三、四、五、六列  
                question = row.iloc[col]
                replaced_question = question.replace(key1, matched_word)
                similarity = metric.jaccard_similarity_str(query, replaced_question)  
                if similarity > max_similarity:
                    max_similarity = similarity  
                    best_row = row
                    best_col = col
                    row_index = index
                    question_type = 'variety'

        # 遍历variety_question的十~二十行 
        for index in range(10, 20):  # 从索引10（第11行）到索引19（第20行）  
            row = self.variety_question.iloc[index]
            for col in range(2, 6):  # 遍历第三、四、五、六列  
                question = row.iloc[col].lower()
                replaced_question = question.replace(key2, matched_word)
                similarity = metric.jaccard_similarity_str(query, replaced_question)  
                if similarity > max_similarity:
                    max_similarity = similarity  
                    best_row = row
                    best_col = col
                    row_index = index
                    question_type = 'variety'
        
        # 遍历gene_question的前十行  
        for index, row in self.gene_question.head(10).iterrows():
            for col in range(2, 6):  # 遍历第三、四、五、六列  
                question = row.iloc[col]
                replaced_question = question.replace(key3, matched_word)
                similarity = metric.jaccard_similarity_str(query, replaced_question)  
                if similarity > max_similarity:
                    max_similarity = similarity  
                    best_row = row
                    best_col = col
                    row_index = index
                    question_type = 'gene'

        # 遍历gene_question的十~二十行 
        for index in range(10, 20):  # 从索引10（第11行）到索引19（第20行）  
            row = self.gene_question.iloc[index]
            for col in range(2, 6):  # 遍历第三、四、五、六列  
                question = row.iloc[col].lower()
                replaced_question = question.replace(key4, matched_word)
                similarity = metric.jaccard_similarity_str(query, replaced_question)  
                if similarity > max_similarity:
                    max_similarity = similarity  
                    best_row = row
                    best_col = col
                    row_index = index
                    question_type = 'gene'
        # print('max_similarity:', max_similarity)
        if best_row is not None:  
            # 替换best_row中除第三、四、五列外的其他列（如果需要）中的key为matched_word    
            replaced_questions = []  
            for col in range(2, 6):  
                if col != best_col:
                    if row_index < 10 and question_type == 'variety':
                        replaced_question = (best_row).iloc[col].replace(key1, matched_word)
                    elif row_index >= 10 and question_type == 'variety':
                        replaced_question = ((best_row).iloc[col]).lower().replace(key2, matched_word)
                    elif row_index < 10 and question_type == 'gene':
                        replaced_question = ((best_row).iloc[col]).lower().replace(key3, matched_word)
                    else:
                        replaced_question = ((best_row).iloc[col]).lower().replace(key4, matched_word)
                    replaced_questions.append(replaced_question)  
            similar_questions = replaced_questions

            response_body = {}
            response_body['status'] = {}
            response_body['data'] = {}  
            response_body['status']['code'] = 0  
            response_body['status']['error'] = 'None'
            response_body['data']['_id'] = str(uuid.uuid4())  
            response_body['data']['cases'] = similar_questions
            return  response_body
        else:
            # 如果问指定物种但问题无关，使用大模型生成新问题  
            prompt = self.GENERATE_TEMPLATE.format(query)  
            response = self.llm.generate_response(prompt=prompt, backend='remote')  
            similar_questions = response
            # print(similar_questions)
            response_body = {}
            response_body['status'] = {}
            response_body['data'] = {}  
            response_body['status']['code'] = 0  
            response_body['status']['error'] = 'None'
            response_body['data']['_id'] = str(uuid.uuid4())  
            response_body['data']['cases'] = similar_questions
            return  response_body
            
  