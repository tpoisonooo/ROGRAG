import requests  
  
url = 'http://0.0.0.0:18445/generate_questions'  
# data_list = [
#     {'query':'如何学习Python？'},  #非品种 调用llm √
#     {'query':'黄华占是怎么培育出来的？'},  #question模板第一列 √
#     {'query':'喜欢的同义词有哪些'},  #非品种 调用llm √
#     {'query':'黄华占在哪些区域能长得好？'},  #question模板第四列 √
#     {'query':'黄华占怎么育种'},  #question模板换一种问法    匹配到了 这黄华占该怎么种才好？
#     {'query':'金谷红是怎么培育出来的'},  #其他品种模板第一列 √
#     {'query':'蜀恢527有啥特别的地方？'},  #其他品种模板第二列 √
#     {'query':'安丰优308特征有什么'}  #其他品种模板换一种问法 √   匹配到了 黄华占品种的特征特性有哪些？
# ]  

# data_list = [
#     {'query':'What are the optimal regions for cultivating Huanghuazhan？'}, #question模板第四列 √
#     {'query':'黄华占是怎么培育出来的？'},
#     {'query':'金谷红是怎么培育出来的'},
#     {'query':'What are the optimal regions for cultivating huanghuazhan？'},
#     {'query':'What are the optimal regions for cultivating huanghuazhan ？'},
#     {'query':'What are the optimal regions for cultivating huanghuazhan ？'},
#     {'query':'What are the optimal regions for cultivating luhui17？'},
#     {'query':'What are the optimal regions for cultivating luhui17 ？'},
#     {'query':'What are the optimal regions for cultivating Luhui17？'},
#     {'query':'水稻中的luhui17基因是指什么？能否说明一下？'},
#     {'query':'Could you tell me about the rice gene jingmeisimiao?'}
# ]  

data_list = [
{
  "user": "水稻中的luhui17基因是指什么？能否说明一下？",
  "history":
    [
    {
      "user": "",
      "assistant": "",
      "references": []
    }
    ]
},
{
  "user": "Could you tell me about the rice gene jingmeisimiao?",
  "history":
    [
    {
      "user": "",
      "assistant": "",
      "references": []
    }
    ]
},
{
  "user": "黄华占是一只可爱的小狗吗?",
  "history":
    [
    {
      "user": "",
      "assistant": "",
      "references": []
    }
    ]
},
{
  "user": "今天天气怎么样?",
  "history":
    [
    {
      "user": "",
      "assistant": "",
      "references": []
    }
    ]
}
]  
for data in data_list:  
    response = requests.post(url, json=data) 
  
    if response.status_code == 200:  
        print('Success:', response.json())  
    else:  
        print('Error:', response.status_code, response.text)