#生成gene question json文件
import os  
import json  
import re  # 引入正则表达式库来处理字符串 
  
# 打开包含问答对的txt文件  
file_path = '/root/wangzhefan/api/data/gene/v0.3_QA_July30_2024.txt'  
with open(file_path, 'r', encoding='utf-8') as file:  
    lines = file.readlines()  
  
# 准备用于存储问题的列表  
questions = []  

# 使用正则表达式匹配":"后的内容  
pattern = re.compile(r':\s*(.*)$')  

# 遍历每一行，查找以"Q"开头的问题    
for line in lines:    
    if line.strip().startswith('Q'):    
        # 使用正则表达式查找":"后的内容  
        match = pattern.search(line)  
        if match:  
            question = match.group(1).strip()  # 提取":"后的内容并去除首尾空白  
            # 构建包含"user"和"history"的字典，并将它添加到列表中    
            questions.append({    
                "user": question,    
                "history": [    
                    {    
                        "user": "",    
                        "assistant": "",    
                        "references": []    
                    }    
                ]    
            })     
  
# 将问题（作为字典列表）存储到一个新的JSON文件中  
filename = '/root/wangzhefan/api/data/gene/user_questions.json'  # 注意：这里使用.json扩展名以表明文件内容是JSON格式的  
  
# 检查文件是否存在（虽然在这个场景下，我们总是想要写入数据，但检查仍然是一个好习惯）  
if not os.path.exists(filename) or os.path.getsize(filename) == 0:  # 或者检查文件是否为空  
    # 以写入模式打开文件（如果文件已存在且不为空，这里会覆盖原有内容）  
    with open(filename, 'w', encoding='utf-8') as outfile:  
        # 使用json.dump将questions列表以JSON格式写入文件  
        json.dump(questions, outfile, ensure_ascii=False, indent=4)  
  
print(f"数据已成功写入到 {filename}")





# #生成variety question json文件
# import pandas as pd  
# import json  
  
# # 读取Excel文件  
# excel_file_path = '/root/wangzhefan/api/data/question/FengDeng_RAG_evaluation_20240528.xlsx'  
# try:  
#     df = pd.read_excel(excel_file_path, usecols=[1])  # 假设第二列的索引是1（通常Excel中列索引从0开始，但这里我们指定读取第二列）  
# except FileNotFoundError:  
#     print(f"Error: 文件 {excel_file_path} 未找到。")  
#     exit(1)  
# except Exception as e:  
#     print(f"Error reading Excel file: {e}")  
#     exit(1)  
  
# # 创建一个空的列表来保存JSON对象  
# data_list = []  
  
# # 遍历DataFrame，将第二列的值作为"user"字段的值  
# for index, row in df.iterrows():  
#     question = row.iloc[0]  # 假设只有一列，直接取这一列的值  
#     data_list.append({"user": str(question), "history": [{"user": "", "assistant": "", "references": []}]})  
  
# # 将列表转换为JSON格式并写入文件  
# json_file_path = '/root/wangzhefan/api/data/question/user_questions_chinese.json'  
# with open(json_file_path, 'w', encoding='utf-8') as file:  
#     json.dump(data_list, file, ensure_ascii=False, indent=4)  
  
# print(f"JSON文件 {json_file_path} 已成功生成。")