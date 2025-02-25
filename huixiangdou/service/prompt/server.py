# PreprocNode
server_prompts = {}
server_prompts['examplify'] = {
    "zh_cn":
    '''
请生成三个与该问题尽可能相似的问题，返回格式为 json list

## 样例返回
["问题1","问题2","问题3"]

## 问题
```text
{query}
```
''',
    "en":
    '''
Please generate three questions that are as similar as possible to the problem, return format is json list

## example output
["Q1","Q2","Q3"]

## problem
```text
{query}
```
'''
}

# =========================================== coreference resolution =========================================
server_prompts['corefence_resolution'] = {
    "zh_cn":
    """你是个文本专家，擅长做指代消歧任务。请阅读输入input和历史消息，消歧后输出语句。如果不需要消除歧义，请输出 "NO"

## 输入说明
输入语句和历史消息是 json 格式，使用 ChatML format。其中 "user" 是用户输入；"assistant" 是助手回复。

## 输出格式要求
- 你不会重复表达和同义反复。
- 如果不需要消除歧义，请输出 "NO"
- 你不会解释输出理由

## 样例1
样例用户输入：
```json
{{"input":"它的种植方法是什么？","history":{{"role":"user","content":"鲁棉研37号种植地区有哪些？"}}, {{"role":"assistant", "content":"鲁棉研37号在山东省适宜地区作为春棉品种推广利用。"}}}}
```
消除歧义，样例输出："鲁棉研37号的种植方法是什么？"

## 样例2
样例用户输入：
```json
{{"input":"茴香豆是什么？","history":{{"role":"user","content":"今天天气如何？"}}, {{"role":"assistant", "content":"24日（今天）. 晴. 8/2℃. <3级 · 25日"}}}}
```
没有歧义要消除，直接输出："NO"

## 真实用户输入
```json
{{"input":"{query}","history":{history}}}
```
输出：
""",
    "en":
    """
You are a text expert, proficient in performing coreference resolution tasks. Please read the input and historical messages, resolve the ambiguity, and output the sentence. If there is no ambiguity to resolve, output "NO".

## Input Description
The input sentence and historical messages are in JSON format, using ChatML format. "user" represents the user's input, and "assistant" represents the assistant's response.

## Output Format Requirements
- You will not repeat expressions or use tautologies.
- If there is no ambiguity to resolve, output "NO".
- You will not explain the reasons for the output.

## Example 1
Example user input:
```json
{{
  "input": "What is its planting method?",
  "history": [
    {{"role": "user", "content": "Which regions are suitable for planting Lumeian No. 37?"}},
    {{"role": "assistant", "content": "Lumeian No. 37 is promoted as a spring cotton variety in suitable regions of Shandong Province."}}
  ]
}}
```
Ambiguity resolved, example output: "What is the planting method for Lumeian No. 37?"

## Example 2
Example user input:
```json
{{
  "input": "What is fennel bean?",
  "history": [
    {{"role": "user", "content": "How is the weather today?"}},
    {{"role": "assistant", "content": "24th (today). Sunny. 8/2°C. <3 level · 25th"}}
  ]
}}
```
No ambiguity to resolve, output directly: "NO"

## Real User Input
```json
{{
  "input": "{query}",
  "history": {history}
}}
```
Output:
"""
}
