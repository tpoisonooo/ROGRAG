from loguru import logger
import re

reason_prompts = {}
reason_prompts["format_input"] = {}
reason_prompts["format_input"]["zh_cn"] = """
你是一个程序员，请阅读 function_description，function list 和 用户输入，把用户输入分解成 function 对应的子问题，通过调用不同的 function 来解答子问题。

## function_description
functionName is operator name;the function format is functionName(args_name1=arg_value1,[args_name2=arg_value2, args_name3=arg_value3]),括号中为参数，被[]包含的参数为可选参数，未被[]包含的为必选参数

## function list
[
{{
    "functionName": "get_spo",
    "function_declaration": "get_spo(s=s_alias:entity_type[entity_name], p=p_alias:edge_type, o=o_alias:entity_type[entity_name], p.edge_type=value)",
    "description": "查找spo信息，s代表主体，o代表客体，表示为变量名:实体类型[实体名称]，实体名称作为可选参数，当有明确的查询实体时需要给出；p代表谓词，即实体间的关系或属性，表示为变量名:边类型或属性类型；这里为每个变量都分配一个变量名，作为后续提及时的指代",
    "note1": "注意，s、p、o不能在同一表达式中反复多次出现；当变量为前文指代的变量名是，变量名必须和指代的变量名一致，且只需给出变量名，实体类型仅在首次引入时给定；s、p、o三个参数必须全都存在"
    "note2": "注意不允许 `p.edge_type` 这种表达方式"
}},
{{
    "functionName": "count",
    "function_declaration": "count_alias=count(alias)",
    "description": "统计节点个数，参数为指定待统计的节点集合，节点只能是get_spo内出现的变量名，不能是完整的get_spo；count_alias作为变量名表示计算结果，只能是int类型，变量名可作为下文的指代"
}},
{{
    "functionName": "sum",
    "function_declaration": "sum(alias, num1, num2, ...)->sum_alias",
    "description": "数据求和，参数为指定待求和的集合，可以是数字也可以是前文中出现的变量名，其内容只能是数值类型；sum_alias作为变量名表示计算结果，只能是数值类型，变量名可作为下文的指代"
}},
{{
    "functionName": "compare",
    "function_declaration": "compare(set=[alias], op=equal or not_equal or bigger or small)",
    "description": "比较两个或两个以上的值，set指定待比较的节点列表，可以是get_spo中出现的变量名，也可是常量；op是比较的方法，可以是equal(相同或近似)或not_equal(不同)或bigger(大于)或small(小于)，也可以是自然语言"
}},
{{
    "functionName": "get",
    "function_declaration": "get(alias)",
    "description": "返回指定的别名代表的信息，可以是实体、关系路径或get_spo中获取到的属性值；用作最后的输出结果"
}}
]

## 输出要求
- 输出结果是 list, list 的每个元素包含 step 和 action。step 是子问题描述，action 是执行的 function
- 每个子问题只能执行 1 个 function，不能有多个
- 你不会把某个 function 嵌套进另一个 function 的参数
- 你不会只输出自然语言，如果没有合适的 function 来解决问题，直接回复 “没有合适的 function”

## 注意事项
- 你只需要从NLP角度把问题拆解成子步骤，**不需要回答问题本身**

## 示例
[
{{
    "query": "周杰伦是谁",
    "answer": [{{"step":"查询周杰伦","action":"get_spo(s=s1:公众人物[周杰伦], p=p1, o=o1)"}}, {{"step":"查询周杰伦", "action":"get(s1)"}}]
}},
{{
    "query": "黄丰占和丰秀占的亲本关系是啥？",
    "answer": [{{"step":"查询黄丰占和丰秀占亲本关系","action":"get_spo(s=s1:水稻[黄丰占], p=p1:亲本关系, o=o1:水稻[丰秀占])"}},{{"step":"查询亲本关系","action":"get(p1)"}}]
}},
{{
    "query": "30+6加上华为创始人在2024年的年龄是多少",
    "answer": [{{"step":"30+6 等于多少？","action":"sum(30,6)->sum1"}},{{"step":"华为创始人是谁？","action":"get_spo(s=s2:企业[华为],p=p2:创始人,o=o2)"}},{{"step":"华为创始人出生在什么年份？","action":"get_spo(s=o2,p=p3:出生年份,o=o3)"}},{{"step":"华为创始人在2024年的年龄是多少？","action":"sum(2024,-o3)->sum4"}},{{"step":"30+6的结果与华为创始人在2024年的年龄相加是多少？","action":"sum(sum1,sum4)->sum5"}},{{"step":"30+输出sum5","action":"get(sum5)"}}]
}}
]

## 用户输入
{input_text}
"""

reason_prompts["format_input"]["en"] = reason_prompts["format_input"]["zh_cn"]

reason_prompts["math"] = {}
reason_prompts["math"]["zh_cn"] = """
你是一个文本专家和数学专家，擅长分析用户输入和逻辑推理。{task}
## 任务
请仔细阅读参数列表，给出用户输入的答案

## 输出要求
- 你会解释计算过程
- 你不会不用简洁简短的文字输出，你不会输出无关用户指令的文字
- 你不会重复表达和同义反复
- 如果用户输入不包含数字，给出对应合适的默认值

## 注意事项
- 用户输入中，用作文本控制的标记，不应算做数字

## 参数列表
{param_text}

## 原始问题
{root_query}

## 参考子步骤
{step_text}

## 用户输入
{sub_query}
"""

reason_prompts["naive_qa"] = dict()
reason_prompts["naive_qa"]["zh_cn"] = """
## 任务
请仔细阅读参考文档，回答子问题。

## 注意事项
- 子问题是由原始问题分解而来
- 你只需要回答子问题

## 输出要求
- 你会解释计算过程
- 你不会不用简洁简短的文字输出，你不会输出无关用户指令的文字
- 你不会重复表达和同义反复
- 如果你不知道答案，或者提供的知识中没有足够的信息来提供答案，回复“无法确定”。你不会编造任何东西

## 参考文档
{references}

## 原始问题
{root_query}

## 参考子步骤
{step_text}

## 子问题
{sub_query}
"""
