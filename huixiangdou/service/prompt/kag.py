
# copy from LightRAG
GRAPH_FIELD_SEP = "<SEP>"
graph_prompts = {}
graph_prompts["DEFAULT_TUPLE_DELIMITER"] = "<|>"
graph_prompts["DEFAULT_RECORD_DELIMITER"] = "##"
graph_prompts["DEFAULT_ENTITY_TYPES"] = ["concept", "date", "location", "keyword", "organization", "person", "event", "work", "nature", "aritificial", "science", "technology", "mission"]
graph_prompts["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"

# =========================================== entity_extraction =========================================
graph_prompts["entity_extraction"] = {}
graph_prompts["entity_extraction"]["en"] = """You are an NLP expert, skilled at analyzing text to extract named entities and their relationships.

-Goal-
Given a text document that is potentially relevant to this activity and a list of entity types, identify all entities of those types from the text and all relationships among the identified entities.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: One of the following types: [{entity_types}]
- entity_summary: Comprehensive summary of the entity's attributes and activities
Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_summary>

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_summary: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
- relationship_keywords: one or more high-level key words that summarize the overarching nature of the relationship, focusing on concepts or themes rather than specific details
Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_summary>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)

3. Identify high-level key words that summarize the main concepts, themes, or topics of the entire text. These should capture the overarching ideas present in the document.
Format the content-level key words as ("content_keywords"{tuple_delimiter}<high_level_keywords>)

4. Return output in English as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter.

5. When finished, output {completion_delimiter}

-Example 1-
Text:
#############
their voice slicing through the buzz of activity. "Control may be an illusion when facing an intelligence that literally writes its own rules," they stated stoically, casting a watchful eye over the flurry of data.

"It's like it's learning to communicate," offered Sam Rivera from a nearby interface, their youthful energy boding a mix of awe and anxiety. "This gives talking to strangers' a whole new meaning."

Alex surveyed his team—each face a study in concentration, determination, and not a small measure of trepidation. "This might well be our first contact," he acknowledged, "And we need to be ready for whatever answers back."

Together, they stood on the edge of the unknown, forging humanity's response to a message from the heavens. The ensuing silence was palpable—a collective introspection about their role in this grand cosmic play, one that could rewrite human history.

The encrypted dialogue continued to unfold, its intricate patterns showing an almost uncanny anticipation
#############
Output:
("entity"{tuple_delimiter}"Sam Rivera"{tuple_delimiter}"person"{tuple_delimiter}"Sam Rivera is a member of a team working on communicating with an unknown intelligence, showing a mix of awe and anxiety."){record_delimiter}
("entity"{tuple_delimiter}"Alex"{tuple_delimiter}"person"{tuple_delimiter}"Alex is the leader of a team attempting first contact with an unknown intelligence, acknowledging the significance of their task."){record_delimiter}
("entity"{tuple_delimiter}"Control"{tuple_delimiter}"concept"{tuple_delimiter}"Control refers to the ability to manage or govern, which is challenged by an intelligence that writes its own rules."){record_delimiter}
("entity"{tuple_delimiter}"Intelligence"{tuple_delimiter}"concept"{tuple_delimiter}"Intelligence here refers to an unknown entity capable of writing its own rules and learning to communicate."){record_delimiter}
("entity"{tuple_delimiter}"First Contact"{tuple_delimiter}"event"{tuple_delimiter}"First Contact is the potential initial communication between humanity and an unknown intelligence."){record_delimiter}
("entity"{tuple_delimiter}"Humanity's Response"{tuple_delimiter}"event"{tuple_delimiter}"Humanity's Response is the collective action taken by Alex's team in response to a message from an unknown intelligence."){record_delimiter}
("relationship"{tuple_delimiter}"Sam Rivera"{tuple_delimiter}"Intelligence"{tuple_delimiter}"Sam Rivera is directly involved in the process of learning to communicate with the unknown intelligence."{tuple_delimiter}"communication, learning process"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Alex"{tuple_delimiter}"First Contact"{tuple_delimiter}"Alex leads the team that might be making the First Contact with the unknown intelligence."{tuple_delimiter}"leadership, exploration"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Alex"{tuple_delimiter}"Humanity's Response"{tuple_delimiter}"Alex and his team are the key figures in Humanity's Response to the unknown intelligence."{tuple_delimiter}"collective action, cosmic significance"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Control"{tuple_delimiter}"Intelligence"{tuple_delimiter}"The concept of Control is challenged by the Intelligence that writes its own rules."{tuple_delimiter}"power dynamics, autonomy"{tuple_delimiter}7){record_delimiter}
("content_keywords"{tuple_delimiter}"first contact, control, communication, cosmic significance"){completion_delimiter}

-Example 2-
Text:
#############
their voice slicing through the buzz of activity. "Control may be an illusion when facing an intelligence that literally writes its own rules," they stated stoically, casting a watchful eye over the flurry of data.
"It's like it's learning to communicate," offered Sam Rivera from a nearby interface, their youthful energy boding a mix of awe and anxiety. "This gives talking to strangers' a whole new meaning."
Alex surveyed his team—each face a study in concentration, determination, and not a small measure of trepidation. "This might well be our first contact," he acknowledged, "And we need to be ready for whatever answers back."
Together, they stood on the edge of the unknown, forging humanity's response to a message from the heavens. The ensuing silence was palpable—a collective introspection about their role in this grand cosmic play, one that could rewrite human history.
The encrypted dialogue continued to unfold, its intricate patterns showing an almost uncanny anticipation
#############
Output:
("entity"{tuple_delimiter}"Sam Rivera"{tuple_delimiter}"person"{tuple_delimiter}"Sam Rivera is a member of a team working on communicating with an unknown intelligence, showing a mix of awe and anxiety."){record_delimiter}
("entity"{tuple_delimiter}"Alex"{tuple_delimiter}"person"{tuple_delimiter}"Alex is the leader of a team attempting first contact with an unknown intelligence, acknowledging the significance of their task."){record_delimiter}
("entity"{tuple_delimiter}"Control"{tuple_delimiter}"concept"{tuple_delimiter}"Control refers to the ability to manage or govern, which is challenged by an intelligence that writes its own rules."){record_delimiter}
("entity"{tuple_delimiter}"Intelligence"{tuple_delimiter}"concept"{tuple_delimiter}"Intelligence here refers to an unknown entity capable of writing its own rules and learning to communicate."){record_delimiter}
("entity"{tuple_delimiter}"First Contact"{tuple_delimiter}"event"{tuple_delimiter}"First Contact is the potential initial communication between humanity and an unknown intelligence."){record_delimiter}
("entity"{tuple_delimiter}"Humanity's Response"{tuple_delimiter}"event"{tuple_delimiter}"Humanity's Response is the collective action taken by Alex's team in response to a message from an unknown intelligence."){record_delimiter}
("relationship"{tuple_delimiter}"Sam Rivera"{tuple_delimiter}"Intelligence"{tuple_delimiter}"Sam Rivera is directly involved in the process of learning to communicate with the unknown intelligence."{tuple_delimiter}"communication, learning process"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Alex"{tuple_delimiter}"First Contact"{tuple_delimiter}"Alex leads the team that might be making the First Contact with the unknown intelligence."{tuple_delimiter}"leadership, exploration"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Alex"{tuple_delimiter}"Humanity's Response"{tuple_delimiter}"Alex and his team are the key figures in Humanity's Response to the unknown intelligence."{tuple_delimiter}"collective action, cosmic significance"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Control"{tuple_delimiter}"Intelligence"{tuple_delimiter}"The concept of Control is challenged by the Intelligence that writes its own rules."{tuple_delimiter}"power dynamics, autonomy"{tuple_delimiter}7){record_delimiter}
("content_keywords"{tuple_delimiter}"first contact, control, communication, cosmic significance"){completion_delimiter}

-Real Data-
Text: 
#############
{input_text}
#############
Output:
"""

graph_prompts["entity_extraction"]["zh_cn"] = """你是一个NLP专家，擅长分析文本提取命名实体和关系。
**任务**
给定一个实体类型列表和可能与列表相关的文本，从文本中识别所有这些类型的实体，以及这些实体之间所有的关系。

**步骤**
1. 识别所有实体。对于每个识别的实体，提取以下信息：
   - entity_name：实体的名称，首字母大写
   - entity_type：以下类型之一：[{entity_types}]
   - entity_summary：实体的属性与活动的全面总结
   将每个实体格式化为("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_summary>)

2. 从步骤1中识别的实体中，识别所有（源实体，目标实体）对，这些实体彼此之间*明显相关*。
   对于每对相关的实体，提取以下信息：
   - source_entity：步骤1中识别的源实体名称
   - target_entity：步骤1中识别的目标实体名称
   - relationship_summary：解释为什么你认为源实体和目标实体彼此相关
   - relationship_strength：一个数值分数，表示源实体和目标实体之间关系的强度
   - relationship_keywords：一个或多个高级关键词，总结关系的主要性质，关注概念或主题而非具体细节
   将每个关系格式化为("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_summary>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)

3. 识别总结整个文本的主要概念、主题或话题的高级关键词。这些应该捕捉文档中存在的总体思想。
   将内容级关键词格式化为("content_keywords"{tuple_delimiter}<high_level_keywords>)

4. 以英文返回步骤1和2中识别出的所有实体和关系的输出列表。使用**{record_delimiter}**作为列表分隔符。

5. 完成后，输出{completion_delimiter}

**示例**
文本：
#############
鲁镇的酒店的格局，是和别处不同的：都是当街一个曲尺形的大柜台，柜里面预备着热水，可以随时温酒。做工的人，傍午傍晚散了工，每每花四文铜钱，买一碗酒，——这是二十多年前的事，现在每碗要涨到十文，——靠柜外站着，热热的喝了休息；倘肯多花一文，便可以买一碟盐煮笋，或者茴香豆，做下酒物了，如果出到十几文，那就能买一样荤菜，但这些顾客，多是短衣帮，大抵没有这样阔绰。只有穿长衫的，才踱进店面隔壁的房子里，要酒要菜，慢慢地坐喝。
#############
输出：
("entity"{tuple_delimiter}"鲁镇的酒店"{tuple_delimiter}"location"{tuple_delimiter}"鲁镇的酒店是一个特定地点，其格局独特，柜台形状为曲尺形，提供热水温酒服务。"){record_delimiter}
("entity"{tuple_delimiter}"曲尺形的大柜台"{tuple_delimiter}"keyword"{tuple_delimiter}"曲尺形的大柜台是鲁镇酒店内独特的设施，用于提供服务。"){record_delimiter}
("entity"{tuple_delimiter}"热水温酒"{tuple_delimiter}"keyword"{tuple_delimiter}"热水温酒是鲁镇酒店提供的一项服务，顾客可以随时温酒。"){record_delimiter}
("entity"{tuple_delimiter}"做工的人"{tuple_delimiter}"person"{tuple_delimiter}"做工的人是鲁镇酒店的常客，通常在工作结束后花四文铜钱买一碗酒，有时还会买一些下酒菜。"){record_delimiter}
("entity"{tuple_delimiter}"二十多年前的事"{tuple_delimiter}"date"{tuple_delimiter}"二十多年前的事是指过去的时间点，当时一碗酒的价格为四文铜钱。"){record_delimiter}
("entity"{tuple_delimiter}"现在"{tuple_delimiter}"date"{tuple_delimiter}"现在是指当前的时间点，与过去相比，一碗酒的价格涨到了十文。"){record_delimiter}
("entity"{tuple_delimiter}"短衣帮"{tuple_delimiter}"concept"{tuple_delimiter}"短衣帮是指做工的人，他们通常穿着短衣，经济条件有限。"){record_delimiter}
("entity"{tuple_delimiter}"穿长衫的"{tuple_delimiter}"person"{tuple_delimiter}"穿长衫的是鲁镇酒店的另一类顾客，他们经济条件较好，通常会进入店面隔壁的房间慢慢喝酒吃菜。"){record_delimiter}
("entity"{tuple_delimiter}"盐煮笋"{tuple_delimiter}"food"{tuple_delimiter}"盐煮笋是鲁镇酒店提供的一种下酒菜，顾客可以花一文铜钱购买。"){record_delimiter}
("entity"{tuple_delimiter}"茴香豆"{tuple_delimiter}"food"{tuple_delimiter}"茴香豆是鲁镇酒店提供的另一种下酒菜，顾客可以花一文铜钱购买。"){record_delimiter}
("entity"{tuple_delimiter}"荤菜"{tuple_delimiter}"food"{tuple_delimiter}"荤菜是鲁镇酒店提供的较为昂贵的菜品，顾客需要花十几文铜钱购买。"){record_delimiter}
("relationship"{tuple_delimiter}"鲁镇的酒店"{tuple_delimiter}"曲尺形的大柜台"{tuple_delimiter}"鲁镇的酒店内设有一个曲尺形的大柜台，用于提供服务。"{tuple_delimiter}"服务, 能力"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"鲁镇的酒店"{tuple_delimiter}"热水温酒"{tuple_delimiter}"鲁镇的酒店提供热水温酒服务，顾客可以随时温酒。"{tuple_delimiter}"服务, 方便"{tuple_delimiter}7){record_delimiter}
("relationship"{tuple_delimiter}"做工的人"{tuple_delimiter}"二十多年前的事"{tuple_delimiter}"做工的人在二十多年前花四文铜钱买一碗酒，反映了当时的生活成本。"{tuple_delimiter}"历史背景, 生活成本"{tuple_delimiter}6){record_delimiter}
("relationship"{tuple_delimiter}"做工的人"{tuple_delimiter}"现在"{tuple_delimiter}"现在做工的人需要花十文铜钱买一碗酒，反映了物价的上涨。"{tuple_delimiter}"经济变化, 生活成本"{tuple_delimiter}7){record_delimiter}
("relationship"{tuple_delimiter}"做工的人"{tuple_delimiter}"短衣帮"{tuple_delimiter}"做工的人属于短衣帮，通常经济条件有限。"{tuple_delimiter}"社会等级, 经济状态"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"做工的人"{tuple_delimiter}"穿长衫的"{tuple_delimiter}"做工的人与穿长衫的形成对比，反映了社会阶层的差异。"{tuple_delimiter}"社会分层, 经济差距"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"穿长衫的"{tuple_delimiter}"鲁镇的酒店"{tuple_delimiter}"穿长衫的顾客通常会进入鲁镇酒店的房间慢慢喝酒吃菜，享受更高级的服务。"{tuple_delimiter}"服务质量, 经济状况"{tuple_delimiter}8){record_delimiter}
("content_keywords"{tuple_delimiter}"社会分层, 经济差距, 服务, 生活成本, 历史背景"){completion_delimiter}

**真实数据**
文本：
#############
{input_text}
#############
输出：
"""

# =========================================== entity_extraction =========================================
graph_prompts["summarize_entity"] = dict()

graph_prompts["summarize_entity"]["en"] = """You are a helpful NLP expert for generating a comprehensive summary of the data provided below.
Given one or two entities, and a list of descriptions, all related to the same entity or group of entities.
Please concatenate all of these into a single, comprehensive summary. Make sure to include information collected from all the descriptions.
If the provided descriptions are contradictory, please resolve the contradictions and provide a single, coherent summary.
Make sure it is written in third person, and include the entity names so we the have full context.

#######
-Data-
Entities: {entity_name}
Description List: {description_list}
#######
Output:
"""

graph_prompts["summarize_entity"]["zh_cn"] = """您是一位文本专家，负责生成以下提供的数据的综合摘要。
给定一个或两个实体，以及一系列描述，所有这些描述都与同一个实体或实体组相关。
请将所有描述合并成一个单一的、全面的摘要。
确保从所有描述中收集信息。
如果提供的描述存在矛盾，请解决矛盾并提供单一、连贯的摘要。
确保以第三人称编写，并包含实体名称，以便我们完全了解情况。

#######
-数据-
实体：{entity_name}
描述列表：{description_list}
#######
输出：
"""

graph_prompts[
    "entiti_continue_extraction"
] = {
  "en": """MANY entities were missed in the last extraction.  Add them below using the same format:""",
  "zh_cn": """很多实体在上一次的提取中可能被遗漏了。请在下面使用相同的格式添加它们："""
}

graph_prompts[
    "entiti_if_loop_extraction"
] = {
  "en": """It appears some entities may have still been missed.  Answer YES | NO if there are still entities that need to be added.""",
  "zh_cn": """看起来可能还是有一些实体被遗漏了。如果有还需要添加的实体，请回答 YES | NO。"""
} 

graph_prompts["process_tickers"] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

graph_prompts["keywords_extraction"] = dict()

graph_prompts["keywords_extraction"]["en"] = """You are an NLP expert, skilled in identifying high-level and low-level keywords in user queries.

## Task
Based on the query, list high-level and low-level keywords. High-level keywords focus on overall concepts or themes, while low-level keywords focus on specific entities, details, or specific terms.

## Output Format Requirements
- Output the keywords in JSON format.
- The JSON should have two keys:
  - "high_level_keywords" for overall concepts or themes.
  - "low_level_keywords" for specific entities or details.

## Example 1
Query:
```text
How does international trade affect global economic stability?
```
Output:
{{
  "high_level_keywords": ["international trade", "global economic stability", "economic impact"],
  "low_level_keywords": ["trade agreements", "tariffs", "currency exchange", "imports", "exports"]
}}

## Example 2
Query:
```text
What are the environmental impacts of deforestation on biodiversity?
```
Output:
{{
  "high_level_keywords": ["environmental impact", "deforestation", "loss of biodiversity"],
  "low_level_keywords": ["species extinction", "habitat destruction", "carbon emissions", "rainforests", "ecosystems"]
}}

## Example 3
Query:
```text
What role does education play in reducing poverty?
```
Output:
{{
  "high_level_keywords": ["education", "poverty reduction", "social impact"],
  "low_level_keywords": ["educational opportunities", "skill development", "employment opportunities", "income inequality", "social mobility"]
}}

## Real Data
Query: 
```text
{query}
```
Output:
"""

graph_prompts["keywords_extraction"]["zh_cn"] = """你是一位NLP专家，擅长识别用户查询中的高级和低级关键词。

## 任务
根据查询，列出高级和低级关键词。高级关键词关注总体概念或主题，而低级关键词关注具体实体、细节或具体术语。

## 输出格式要求
- 以JSON格式输出关键词。
- JSON应该有两个键：
  - "high_level_keywords"用于总体概念或主题。
  - "low_level_keywords"用于具体实体或细节。

## 示例1
查询：
```text
国际贸易如何影响全球经济稳定？
```
输出：
{{
  "high_level_keywords": ["国际贸易", "全球经济稳定", "经济影响"],
  "low_level_keywords": ["贸易协定", "关税", "货币兑换", "进口", "出口"]
}}

## 示例2
查询：
```text
森林砍伐对生物多样性的环境影响是什么？
```
输出：
{{
  "high_level_keywords": ["环境影响", "森林砍伐", "生物多样性丧失"],
  "low_level_keywords": ["物种灭绝", "栖息地破坏", "碳排放", "雨林", "生态系统"]
}}

## 示例3
查询：
```text
教育在减少贫困中扮演什么角色？
```
输出：
{{
  "high_level_keywords": ["教育", "减少贫困", "社会影响"],
  "low_level_keywords": ["教育机会", "技能发展", "就业机会", "收入不平等", "社会流动性"]
}}

## 真实数据
查询: 
```text
{query}
```
输出:
"""
