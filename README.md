English | [Simplified Chinese](./README_zh_cn.md)

# HuixiangDou2: A Robustly Optimized GraphRAG Approach
<div>
  <a href="https://arxiv.org/abs/2503.06474" target="_blank">
    <img alt="Arxiv" src="https://img.shields.io/badge/arxiv-2503.06474%20-darkred?logo=arxiv&logoColor=white" />
  </a>
</div>

## Introduction

GraphRAG has many tuning spots, making it hard to discern whether performance gains stem from parameter adjustments or pipeline optimizations. Moreover, RAG test data is embedded in LLM training sets. LLM input tokens impact generation probabilities (background: phi-4 technical report). It's unclear if precision improvements originate from key token searches or retrievals.

Thus, HuixiangDou2 didn't introduce new methods but integrated multiple open-source projects (HuixiangDou, KAG, LightRAG, and DB-GPT, totaling 18k lines of code) and conducted comparative experiments on a test set where Qwen2.5-7B-Instruct underperformed. The score rose from 60 to 74.5. Ultimately, a GraphRAG implementation with performance recognized by human domain experts was developed. [Here is the report](https://arxiv.org/abs/2503.06474).

> **Note**: The impact of open-source on different fields/industries varies. Since licensing restriction, we can **only give the code and test conclusions, and the test data cannot be provided**.

<div align="center">
<img src="https://github.com/user-attachments/assets/19558f67-9a3a-48a1-a1c1-7b0a0654602f" width=400>
</div>

## Documentation
- [1. Run from Docker (CMD / Swagger Server API / Gradio)](docs/en/doc_how_to_run_from_docker.md)
- [2. Run from Source](docs/en/doc_how_to_run.md)
- [3. Directory Structure and Function](docs/en/doc_architecture.md)
- [**FAQ** about environment and error](https://github.com/tpoisonooo/HuixiangDou2/issues/8) 

If it is useful to you, please star it ⭐

## Version Description

Compared to [HuixiangDou1](https://github.com/internlm/huixiangdou), this repo improves accuracy:
1. **Graph Schema**. Dense retrieval is only for querying similar entities and relationships.
2. Ported/merged multiple open-source implementations, with code differences of nearly 18k lines:
   - **Data**. Organized a set of real domain knowledge that LLM has not fully seen for testing (gpt accuracy < 0.6)
   - **Ablation**. Confirmed the impact of different stages and parameters on accuracy
   - **Improvement**. As shown below.
      <div>
      <img src="https://github.com/user-attachments/assets/c3453bc8-85d5-47e1-8160-7ba28a467a70" width=300>
      </div>
     
3. API remains compatible. That means Wechat/Lark/Web in v1 is also accessible.
   ```text
   # v1 API https://github.com/InternLM/HuixiangDou/blob/main/huixiangdou/service/parallel_pipeline.py#L290
   async def generate(self,
               query: Union[Query, str],
               history: List[Tuple[str]]=[], 
               language: str='zh', 
               enable_web_search: bool=True,
               enable_code_search: bool=True):

   # v2 API https://github.com/tpoisonooo/HuixiangDou2/blob/main/huixiangdou/pipeline/parallel.py#L135
   async def generate(self,
                   query: Union[Query, str],
                   history: List[Pair] = [],
                   request_id: str = 'default',
                   language: str = 'zh_cn'):
   ```
   

## Acknowledgements
- [SiliconCloud](https://siliconflow.cn) Abundant LLM API, some models are free
- [KAG](https://github.com/OpenSPG/KAG) Graph retrieval based on reasoning
- [DB-GPT](https://github.com/eosphoros-ai/DB-GPT) LLM tool collection
- [LightRAG](https://github.com/HKUDS/LightRAG) Simple and efficient graph retrieval solution

## Citation
```text
@misc{kong2024huixiangdou,
      title={HuiXiangDou: Overcoming Group Chat Scenarios with LLM-based Technical Assistance},
      author={Huanjun Kong and Songyang Zhang and Jiaying Li and Min Xiao and Jun Xu and Kai Chen},
      year={2024},
      eprint={2401.08772},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}

@misc{kong2024labelingsupervisedfinetuningdata,
      title={Labeling supervised fine-tuning data with the scaling law}, 
      author={Huanjun Kong},
      year={2024},
      eprint={2405.02817},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2405.02817}, 
}

@misc{kong2025huixiangdou2robustlyoptimizedgraphrag,
      title={HuixiangDou2: A Robustly Optimized GraphRAG Approach}, 
      author={Huanjun Kong and Zhefan Wang and Chenyang Wang and Zhe Ma and Nanqing Dong},
      year={2025},
      eprint={2503.06474},
      archivePrefix={arXiv},
      primaryClass={cs.IR},
      url={https://arxiv.org/abs/2503.06474}, 
}
```
