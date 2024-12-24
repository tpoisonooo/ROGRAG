from ..primitive import MemoryGraph, Chunk, Faiss, encode_string, judge_language, LLM
from .prompt import graph_prompts as PROMPTS
from .prompt import GRAPH_FIELD_SEP

from typing import List, Any
from collections import defaultdict, Counter
import asyncio
import re
import html
from loguru import logger
from bs4 import BeautifulSoup
from .graph_store import TuGraphStore

entity_max_length = 64

def is_float_regex(value):
    value = value.strip()
    return bool(re.match(r"^[-+]?[0-9]*\.?[0-9]+$", value))

# modify from LigthRAG and GraphRAG
# Refer the utils functions of the official GraphRAG implementation:
# https://github.com/microsoft/graphrag
def clean_str(input: Any) -> str:
    """Clean an input string by removing HTML escapes, control characters, and other unwanted characters."""
    # If we get non-string input, just give it back
    if not isinstance(input, str):
        return str(input)

    soup = BeautifulSoup(input.strip(), 'html.parser')
    cleaned_content = soup.get_text()
    # https://stackoverflow.com/questions/4324790/removing-control-characters-from-a-string-in-python
    cleaned_content = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", cleaned_content).replace('\u200B', '')
    result = html.unescape(cleaned_content.strip())
    if result.startswith('"') or result.startswith("'"):
        result = result[1:]
    if result.endswith('"') or result.endswith("'"):
        result = result[0:-1]
    return result

def truncate_list_by_token_size(list_data: list, key: callable, max_token_size: int):
    """Truncate a list of data by token size"""
    if max_token_size <= 0:
        return []
    tokens = 0
    for i, data in enumerate(list_data):
        tokens += len(encode_string(key(data)))
        if tokens > max_token_size:
            return list_data[:i]
    return list_data

def split_string_by_multi_markers(content: str, markers: list[str]) -> list[str]:
    """Split a string by multiple markers"""
    if not markers:
        return [content]
    results = re.split("|".join(re.escape(marker) for marker in markers), content)
    return [r.strip() for r in results if r.strip()]

def pack_user_assistant_to_messages(*args: str):
    roles = ["user", "assistant"]
    return [
        {"role": roles[i % 2], "content": content} for i, content in enumerate(args)
    ]

async def _handle_single_entity_extraction(
    record_attributes: list[str],
    chunk_key: str,
):
    if len(record_attributes) < 4 or record_attributes[0] != '"entity"':
        return None
    # add this record as a node in the G
    entity_name = clean_str(record_attributes[1].upper())
    if not entity_name.strip():
        return None
    entity_type = clean_str(record_attributes[2].upper())
    entity_description = clean_str(record_attributes[3])
    entity_source_id = chunk_key
    
    if not entity_name:
        return None
    
    global entity_max_length
    if len(entity_name) > entity_max_length:
        return None
    
    return dict(
        entity_name=entity_name,
        entity_type=entity_type,
        description=entity_description,
        source_id=entity_source_id,
    )
    
async def _handle_single_relationship_extraction(
    record_attributes: list[str],
    chunk_key: str,
):
    if len(record_attributes) < 5 or record_attributes[0] != '"relationship"':
        return None
    # add this record as edge
    source = clean_str(record_attributes[1].upper())
    target = clean_str(record_attributes[2].upper())
    edge_description = clean_str(record_attributes[3])

    edge_keywords = clean_str(record_attributes[4])
    edge_source_id = chunk_key
    weight = (
        float(record_attributes[-1]) if is_float_regex(record_attributes[-1]) else 1.0
    )
    
    if not edge_description or not edge_keywords:
        return None
    global entity_max_length
    
    if len(source) > entity_max_length:
        return None
    
    if len(target) > entity_max_length:
        return None
    
    return dict(
        src_id=source,
        tgt_id=target,
        weight=weight,
        description=edge_description,
        keywords=edge_keywords,
        source_id=edge_source_id,
    )
    
async def _handle_entity_relation_summary(
    entity_or_relation_name: str,
    summary: str,
    llm: LLM,
) -> str:
    language = judge_language(text=summary)
    tokens = encode_string(summary)
    if len(tokens) < 500:  # No need for summary
        return summary
    prompt_template = PROMPTS["summarize_entity"][language]
    context_base = dict(
        entity_name=entity_or_relation_name,
        description_list=summary.split(GRAPH_FIELD_SEP),
    )
    use_prompt = prompt_template.format(**context_base)
    logger.debug(f"Trigger summary: {entity_or_relation_name}")
    summary = await llm.chat(use_prompt)
    return summary

async def _merge_nodes_then_upsert(
    entity_name: str,
    nodes_data: list[dict],
    knowledge_graph_inst: MemoryGraph,
    llm: LLM,
):
    already_entitiy_types = []
    already_source_ids = []
    already_description = []

    already_node = knowledge_graph_inst.get_node(entity_name)
    if already_node is not None:
        already_entitiy_types.append(already_node.props.get("entity_type"))
        already_source_ids.extend(
            split_string_by_multi_markers(already_node.props.get("source_id"), [GRAPH_FIELD_SEP])
        )
        already_description.append(already_node.props.get("description"))

    entity_type = sorted(
        Counter(
            [dp["entity_type"] for dp in nodes_data] + already_entitiy_types
        ).items(),
        key=lambda x: x[1],
        reverse=True,
    )[0][0]
    description = GRAPH_FIELD_SEP.join(
        sorted(set([dp["description"] for dp in nodes_data] + already_description))
    )
    source_id = GRAPH_FIELD_SEP.join(
        set([dp["source_id"] for dp in nodes_data] + already_source_ids)
    )
    description = await _handle_entity_relation_summary(
        entity_name, description, llm
    )
    node_data = dict(
        entity_type=entity_type,
        description=description,
        source_id=source_id,
    )
    knowledge_graph_inst.upsert_node(
        name=entity_name,
        data=node_data,
    )
    node_data["entity_name"] = entity_name
    return node_data


async def _merge_edges_then_upsert(
    src_id: str,
    tgt_id: str,
    edges_data: list[dict],
    knowledge_graph_inst: MemoryGraph,
    llm: LLM,
):
    already_weights = []
    already_source_ids = []
    already_description = []
    already_keywords = []

    if knowledge_graph_inst.has_edge(src_id, tgt_id):
        already_edge = knowledge_graph_inst.get_edge(src_id, tgt_id)
        already_weights.append(already_edge["weight"])
        already_source_ids.extend(
            split_string_by_multi_markers(already_edge["source_id"], [GRAPH_FIELD_SEP])
        )
        already_description.append(already_edge["description"])
        already_keywords.extend(
            split_string_by_multi_markers(already_edge["keywords"], [GRAPH_FIELD_SEP])
        )

    weight = sum([dp["weight"] for dp in edges_data] + already_weights)
    description = GRAPH_FIELD_SEP.join(
        sorted(set([dp["description"] for dp in edges_data] + already_description))
    )
    keywords = GRAPH_FIELD_SEP.join(
        sorted(set([dp["keywords"] for dp in edges_data] + already_keywords))
    )
    source_id = GRAPH_FIELD_SEP.join(
        set([dp["source_id"] for dp in edges_data] + already_source_ids)
    )

    for need_insert_id in [src_id, tgt_id]:
        if not need_insert_id:
            continue
        if len(need_insert_id) > entity_max_length:
            continue

        if not (knowledge_graph_inst.has_node(need_insert_id)):
            knowledge_graph_inst.upsert_node(
                name=need_insert_id,
                data={
                    "source_id": source_id,
                    "description": description,
                    "entity_type": '"UNKNOWN"',
                }
            )
    description = await _handle_entity_relation_summary(
        (src_id, tgt_id), description, llm
    )
    knowledge_graph_inst.upsert_edge(
        src_id,
        tgt_id,
        name=keywords,
        data=dict(
            weight=weight,
            description=description,
            keywords=keywords,
            source_id=source_id,
        )
    )

    edge_data = dict(
        src_id=src_id,
        tgt_id=tgt_id,
        description=description,
        keywords=keywords,
    )
    return edge_data

# modified from LightRAG
async def parse_chunk_to_knowledge(
    chunks: List[Chunk], 
    llm: LLM, 
    entityDB: Faiss, 
    relationDB: Faiss,
    entityDB_mix: Faiss, 
    relationDB_mix: Faiss,
    graph_store: TuGraphStore) -> None:

    graph = MemoryGraph()
    entity_extract_prompt = PROMPTS["entity_extraction"]
    context_base = dict(
        tuple_delimiter=PROMPTS["DEFAULT_TUPLE_DELIMITER"],
        record_delimiter=PROMPTS["DEFAULT_RECORD_DELIMITER"],
        completion_delimiter=PROMPTS["DEFAULT_COMPLETION_DELIMITER"],
        entity_types=",".join(PROMPTS["DEFAULT_ENTITY_TYPES"]),
    )
    continue_prompt = PROMPTS["entiti_continue_extraction"]
    if_loop_prompt = PROMPTS["entiti_if_loop_extraction"]

    already_processed = 0
    already_entities = 0
    already_relations = 0
    
    async def _process_single_content(chunk:Chunk):
        nonlocal already_processed, already_entities, already_relations
        content = chunk.content_or_path
        language = judge_language(text=content)
        hint_prompt = entity_extract_prompt[language].format(**context_base, input_text=content)
        final_result = await llm.chat(hint_prompt)

        history = pack_user_assistant_to_messages(hint_prompt, final_result) # 重复提取实体词，until LLM 判断为 finished
        entity_extract_max_gleaning = 1
        for now_glean_index in range(entity_extract_max_gleaning):
            glean_result = await llm.chat(continue_prompt[language], history=history)
            history += pack_user_assistant_to_messages(continue_prompt[language], glean_result)
            final_result += glean_result
            if now_glean_index == entity_extract_max_gleaning - 1:
                break

            if_loop_result: str = await llm.chat(
                if_loop_prompt[language], history=history
            )
            if_loop_result = if_loop_result.strip().strip('"').strip("'").lower()
            if "yes" in if_loop_result:
                break

        records = split_string_by_multi_markers(
            final_result,
            [context_base["record_delimiter"], context_base["completion_delimiter"]],
        )

        maybe_nodes = defaultdict(list)
        maybe_edges = defaultdict(list)
        for record in records:
            record = re.search(r"\((.*)\)", record)
            if record is None:
                continue
            record = record.group(1)
            record_attributes = split_string_by_multi_markers(
                record, [context_base["tuple_delimiter"]]
            )
            if_entities = await _handle_single_entity_extraction(
                record_attributes, chunk._hash
            )
            if if_entities is not None:
                maybe_nodes[if_entities["entity_name"]].append(if_entities)
                continue

            if_relation = await _handle_single_relationship_extraction(
                record_attributes, chunk._hash
            )
            if if_relation is not None:
                maybe_edges[(if_relation["src_id"], if_relation["tgt_id"])].append(
                    if_relation
                )
        already_processed += 1
        already_entities += len(maybe_nodes)
        already_relations += len(maybe_edges)
        now_ticks = PROMPTS["process_tickers"][
            already_processed % len(PROMPTS["process_tickers"])
        ]
        print(
            f"{now_ticks} Processed {already_processed} chunks, {already_entities} entities(duplicated), {already_relations} relations(duplicated)\r",
            end="",
            flush=True,
        )
        return dict(maybe_nodes), dict(maybe_edges)
    
    # use_llm_func is wrapped in ascynio.Semaphore, limiting max_async callings
    results = await asyncio.gather(
        *[_process_single_content(c) for c in chunks]
    )
    print()  # clear the progress bar
    maybe_nodes = defaultdict(list)
    maybe_edges = defaultdict(list)
    for m_nodes, m_edges in results:
        for k, v in m_nodes.items():
            maybe_nodes[k].extend(v)
        for k, v in m_edges.items():
            maybe_edges[tuple(sorted(k))].extend(v)
    
    all_entities_data = await asyncio.gather(
        *[
            _merge_nodes_then_upsert(k, v, graph, llm)
            for k, v in maybe_nodes.items()
        ]
    )
    all_relationships_data = await asyncio.gather(
        *[
            _merge_edges_then_upsert(k[0], k[1], v, graph, llm)
            for k, v in maybe_edges.items()
        ]
    )
    if not len(all_entities_data):
        logger.warning("Didn't extract any entities, maybe your LLM is not working")
        return None
    if not len(all_relationships_data):
        logger.warning(
            "Didn't extract any relationships, maybe your LLM is not working"
        )
        return None

    if entityDB is not None:
        for dp in all_entities_data:
            entityDB_mix.upsert(Chunk(content_or_path=dp["entity_name"] + dp["description"], metadata={"entity_name":dp["entity_name"], "entity_type":dp["entity_type"]}))
            entityDB.upsert(Chunk(content_or_path=dp["entity_name"], metadata={"entity_name":dp["entity_name"], "entity_type":dp["entity_type"], "description":dp["description"]}))
            
    if relationDB is not None:
        for dp in all_relationships_data:
            relationDB_mix.upsert(Chunk(content_or_path=dp["keywords"]+dp["src_id"]+dp["tgt_id"]+dp["description"], metadata={"src_id":dp["src_id"], "tgt_id":dp["tgt_id"]}))
            relationDB.upsert(Chunk(content_or_path=dp["keywords"], metadata={"src_id":dp["src_id"], "tgt_id":dp["tgt_id"], "description":dp["description"]}))
    
    graph_store.insert_graph(graph=graph)
    return
