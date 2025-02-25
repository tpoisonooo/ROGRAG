import json
import pdb
import sys
from loguru import logger

##
# 后置 pf
# 2024-12-30 11:59:52.120 | INFO     | __main__:precision_verifier:32 - ('reason', 0.8765432098765432, 71, 81)
# 2024-12-30 11:59:52.120 | INFO     | __main__:precision_verifier:33 - ('reason', 'knowledge', 72, 43)
# 2024-12-30 11:59:52.120 | INFO     | __main__:precision:47 - ('reason', 0.55, 110, 196)
# 2024-12-30 11:59:52.120 | INFO     | __main__:token_avg:110 - ('reason', 'avg token length', 1699.2857142857142)
# 2024-12-30 11:59:52.120 | INFO     | __main__:precision:47 - ('knowledge', 0.715, 143, 196)
# 2024-12-30 11:59:52.120 | INFO     | __main__:token_avg:110 - ('knowledge', 'avg token length', 9863.877551020409)
# 2024-12-30 11:59:52.121 | INFO     | __main__:join_precision:88 - (71, 39, 10, 76)
# 2024-12-30 11:59:52.121 | INFO     | __main__:join_precision:103 - ('join', 0.77, 154, 196, 200)

# Simple LFPlaner 由于拆分形式和图谱不对齐
# 1. 无法确保 SPO 切分名词的准确性，需引入启发式的方法
# 2. LLM 本身的优化

# LLM-based verifier 模式只适合简单问题
# 引入 verifier

##
# 前置 pf
# 2025-01-08 17:40:59.299 | INFO     | __main__:precision_verifier:52 - ('reason', 0.8809523809523809, 74, 84)
# 2025-01-08 17:40:59.300 | INFO     | __main__:precision_verifier:53 - ('reason', 'knowledge', 0, 0)
# 2025-01-08 17:40:59.300 | INFO     | __main__:precision:67 - ('reason', 0.37, 74, 84)
# 2025-01-08 17:40:59.300 | INFO     | __main__:token_avg:130 - ('reason', 'avg token length', 1490.392857142857)
# 2025-01-08 17:40:59.301 | INFO     | __main__:precision:67 - ('knowledge', 0.37, 74, 84)
# 2025-01-08 17:40:59.301 | INFO     | __main__:token_avg:130 - ('knowledge', 'avg token length', 8659.619047619048)
# 2025-01-08 17:40:59.301 | INFO     | __main__:join_precision:108 - (74, 0, 10, 0)
# 2025-01-08 17:40:59.301 | INFO     | __main__:join_precision:123 - ('join', 0.405, 81, 84, 200)


def precision_verifier(name, ppls, dts, gts, knowledges):
    assert len(dts) == len(gts)
    true_cnt = 0
    false_cnt = 0
    ppl_false_cnt = 0

    knowledge_true = 0
    knowledge_false = 0
    for i, dt in enumerate(dts):
        ppl = ppls[i]
        resp = dt['response']

        if 'YES' in ppl:
            if gts[i] in resp.lower():
                true_cnt += 1
            else:
                false_cnt += 1
        else:
            if gts[i].lower() in knowledges[i]['response'].lower():
                knowledge_true += 1
            else:
                knowledge_false += 1

    # ('reason', 0.8765432098765432, 71, 81)
    rate = true_cnt / (true_cnt + false_cnt)
    logger.info((name, rate, true_cnt, false_cnt + true_cnt))
    logger.info((name, 'knowledge', knowledge_true, knowledge_false))


def precision(name, dts, gts):
    assert len(dts) == len(gts)
    true_cnt = 0
    false_cnt = 0
    for i, dt in enumerate(dts):
        resp = dt['response']
        if gts[i] in resp.lower():
            true_cnt += 1
        else:
            false_cnt += 1

    rate = true_cnt / 200
    logger.info((name, rate, true_cnt, false_cnt + true_cnt))


def join_precision(name, ppls, reasons, knowledges, gts):
    assert len(reasons) == len(gts)
    assert len(knowledges) == len(gts)

    true_cnt = 0
    false_cnt = 0
    ppl_tp = 0
    ppl_tn = 0
    ppl_fp = 0
    ppl_fn = 0

    for i in range(len(gts)):
        reason_resp = reasons[i]['response']
        knowledge_resp = knowledges[i]['response']
        ppl = ppls[i]

        # 正类
        if gts[i].lower() in reason_resp.lower():
            if 'YES' in ppl:
                ppl_tp += 1
            else:
                ppl_fn += 1
        else:
            if 'YES' in ppl:
                ppl_fp += 1
            else:
                ppl_tn += 1

        if 'YES' in ppl:
            dt = reason_resp.lower()
        else:
            dt = knowledge_resp.lower()

        if gts[i].lower() in reason_resp.lower() or gts[i].lower(
        ) in knowledge_resp.lower():
            # if gts[i] in dt:
            true_cnt += 1
        else:
            false_cnt += 1

    logger.info((ppl_tp, ppl_fn, ppl_fp, ppl_tn))
    # T=(dt=gt)   P=yes
    # precision = TP / (TP + FP)

    # F=(dt!=gt)  N=no
    # recall = TP / (TP + FN)

    # (71, 39, 10, 76)

    # precision, recall, F1
    # 0.8765,0.6455,0.7437

    # Verifier max score
    # 0.77
    rate = true_cnt / 200
    logger.info((name, rate, true_cnt, false_cnt + true_cnt, 200))


def token_avg(name, dts):
    _sum = 0
    for i, dt in enumerate(dts):
        length = dt['token_len']
        _sum += length
    logger.info((name, 'avg token length', _sum / len(dts)))


def calc(path):
    true_cnt = 0
    false_cnt = 0

    reasons = []
    knowledges = []
    gts = []
    ppls = []
    with open(path) as f:
        for line in f:

            jsono = json.loads(line)
            if 'retriever_reason' not in jsono:
                print(jsono.keys())
                continue

            ppls.append(jsono['ppl'])

            if 'YES' not in jsono['ppl']:
                pdb.set_trace()
                pass

            reason = jsono['retriever_reason']
            reasons.append(reason)
            knowledge = jsono['retriever_knowledge']
            knowledges.append(knowledge)
            gt = jsono['gt'].lower()
            gts.append(gt)
            question = jsono['input']

    pdb.set_trace()
    # avg_token
    precision_verifier('reason', ppls, reasons, gts, knowledges)
    precision('reason', reasons, gts)
    token_avg('reason', reasons)
    precision('knowledge', knowledges, gts)
    token_avg('knowledge', knowledges)
    join_precision('join', ppls, reasons, knowledges, gts)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        # path = '/home/data/khj/workspace/seedllm/HuixiangDou/2_zero_shot_kag_seedllm_Qwen2.5-7B-Instruct.jsonl'
        path = '/data/khj/workspace/HuixiangDou/1202_kag_seedllm_Qwen2.5-7B-Instruct.jsonl'
        path = '/data/khj/workspace/HuixiangDou/2024-12-26_13/2_hybrid_zero_shot_kag_seedllm_Qwen2.5-7B-Instruct.jsonl'
        path = '/data/khj/workspace/HuixiangDou/2024-12-29_14/debug.jsonl'
        path = '/data/khj/workspace/HuixiangDou/2025-01-08_16/debug.jsonl'
    calc(path=path)
