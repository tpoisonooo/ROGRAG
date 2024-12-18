# #rice和rice pinyin第一列写入词典
# import jieba  
# import pandas as pd
# import os
# from pypinyin import pinyin, Style   
  
# # CSV文件路径  
# csv_file_path = '/root/wangzhefan/api/data/gene/test.csv'  
  
# df = pd.read_csv(csv_file_path)
  
# # 将DataFrame转换为list，然后转换为set以去除重复项（如果有的话）  
# first_column_data = df.iloc[:, 0]  # 使用iloc来按位置索引  
# custom_words = first_column_data.tolist()   
  
# # 如果需要，你可以在这里打印出这些自定义词来检查  
# print("自定义词列表：", custom_words[0:5]) 
# print("自定义词列表：", custom_words[-5:])   
  
# # 用户词典文件路径  
# userdict_path = '/root/wangzhefan/api/data/jieba_gene.txt'  
  
# # 如果用户词典文件不存在，则创建它  
# if not os.path.exists(userdict_path):  
#     with open(userdict_path, 'w', encoding='utf-8') as file:  
#         # 可以在这里写入一些初始的词典条目（如果需要的话），但在这个例子中我们保持文件为空  
#         pass  
  
# # # 将自定义词写入用户词典文件  
# # with open(userdict_path, 'a', encoding='utf-8') as file:  
# #     for word in custom_words:
# #         pinyin_list = pinyin(word, style=Style.NORMAL)
# #         pinyin_word = ''.join(item[0] for item in pinyin_list)     
# #         # 假设每个词后面跟一个空格和频率（这里使用10作为示例），然后是一个换行符  
# #         file.write(f"{pinyin_word.lower()} 10\n")  

# # 将自定义词（小写形式）写入用户词典文件  
# with open(userdict_path, 'a', encoding='utf-8') as file:  
#     for word in custom_words:  
#         # 将词汇转换为小写，并写入文件，假设每个词后面跟一个空格和频率（这里使用10作为示例），然后是一个换行符  
#         file.write(f"{word.lower()} 10\n")  

# # 加载用户词典  
# jieba.load_userdict(userdict_path)  
  
# # 现在你可以使用jieba进行分词了  
# text = "中9a适宜种植区域有哪些？"  
# seg_list = jieba.cut(text.lower(), HMM=False)  
# print("分词结果：", " ".join(seg_list))



import jieba  
import pandas as pd  
import os  
  
# CSV文件路径  
csv_file_path = '/root/wangzhefan/api/data/gene/rice_reference_genome_annotation_20240903.csv'  
  
# 读取CSV文件  
df = pd.read_csv(csv_file_path, skiprows=1)  
  
# 用户词典文件路径  
userdict_path = '/root/wangzhefan/api/data/jieba_gene.txt'  
  
# 确保用户词典文件存在  
if not os.path.exists(userdict_path):  
    with open(userdict_path, 'w', encoding='utf-8') as file:  
        pass  
  
# 创建一个集合来跟踪已经写入的词汇  
written_words = set()  
  
# 写入前五列中的分割词汇到用户词典，避免重复  
with open(userdict_path, 'a', encoding='utf-8') as file:  
    for index, row in df.iterrows():  # 遍历DataFrame的每一行  
        for col in range(5):  # 遍历前五列  
            entry = row.iloc[col]  # 获取当前行的当前列的值  
            if pd.notna(entry):  # 检查单元格是否为NaN  
                for word in entry.split(',') + entry.split('/') + entry.split(';'):  # 分割单元格内容  
                    # 去除空字符串并转换为小写  
                    word = word.strip().lower()  
                    if word and word not in written_words:  # 如果单词不为空且未写入过  
                        # 写入文件，并添加到已写入词汇集合中  
                        file.write(f"{word} 10\n")  
                        written_words.add(word) 
  
# 加载用户词典  
jieba.load_userdict(userdict_path)






# #将水稻品种中文csv变成拼音csv
# import pandas as pd  
# from pypinyin import pinyin, Style  
  
# # 读取CSV文件，假设没有列名  
# df = pd.read_csv('/root/wangzhefan/api/data/Rice_Variety_merged.csv', header=None, encoding='utf-8')  
  
# # 使用iloc获取第一列（索引为0的列）  
# first_column = df.iloc[:, 0]  
  
# # 创建一个新的Series来存储拼音  
# pinyin_series = first_column.apply(lambda x: ''.join([word[0].lower()  for word in pinyin(x, style=Style.NORMAL)]) if pd.notna(x) else '') 
# # print(pinyin_series[0:10])  
# # print(pinyin_series.head())    
# # 并给这个列一个名字，比如'Pinyin'  
# new_df = pd.DataFrame(pinyin_series)  
# # print(new_df) 
# # 将新DataFrame保存到CSV文件中，没有索引  
# new_df.to_csv('/root/wangzhefan/api/data/Rice_Variety_merged_pinyin.csv', index=False, encoding='utf-8-sig',header = None)  
  
# # 注意：这里的'/path/to/your/new_file_with_pinyin.csv'需要替换为你想要保存新文件的实际路径