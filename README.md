English | [Simplified Chinese](./README_zh_cn.md)

# HuixiangDou2: A Robustly Optimized GraphRAG Approach

We integrated 4 open-source projects (HuixiangDou, KAG, LightRAG, and DB-GPT, totaling 18k lines of code) and conducted comparative experiments on a test set where the performance of `Qwen2.5-7B-Instruct` was subpar. The results showed an improvement from a baseline score of 0.6 to ~0.75.

We ultimately developed a GraphRAG implementation whose performance has been recognized by domain experts. [Here is the report]([./docs/](https://github.com/tpoisonooo/HuixiangDou2/blob/main/docs/huixiangdou2_github.pdf)).

<div align="center">
<img src="https://github.com/user-attachments/assets/19558f67-9a3a-48a1-a1c1-7b0a0654602f" width=400>
</div>

## Version Description

Compared to [HuixiangDou1](https://github.com/internlm/huixiangdou), this repo improves accuracy and `async` refactor:
1. **Graph Schema**. Dense retrieval is only for querying similar entities and relationships.
2. Ported/merged multiple open-source implementations, with code differences of nearly 10k lines:
   - **Data**. Organized a set of real domain knowledge that LLM has not fully seen for testing (GPT accuracy 0.53)
   - **Ablation**. Confirmed the impact of different stages and parameters on accuracy
   - **Improvement**. Compared to directly using LLM without retrieval, accuracy improved **0.22**; compared to the baseline implementation, improved **0.1**
3. API remains compatible

> **Note**: The impact of open-source on different fields/industries varies. We can only provide code implementation and test conclusions, and the test data cannot be provided.

If it is useful to you, please star it ⭐

## Documentation
- [1. How to Run](docs/en/doc_how_to_run.md)
- [2. Directory Structure and Function](docs/en/doc_architecture.md)
- [**FAQ** about environment and error](https://github.com/tpoisonooo/HuixiangDou2/issues/8) 

## Acknowledgements
- [SiliconCloud](https://siliconflow.cn) Abundant LLM API, some models are free
- [KAG](https://github.com/OpenSPG/KAG) Graph retrieval based on reasoning
- [DB-GPT](https://github.com/eosphoros-ai/DB-GPT) LLM tool collection
- [LightRAG](https://github.com/HKUDS/LightRAG) Simple and efficient graph retrieval solution

## Citation
```text
@misc{huixiangdou2,
  author = {Huanjun Kong},
  title = {HuixiangDou2: A Graph-based Augmented Generation Approach},
  howpublished = {\url{https://github.com/tpoisonooo/HuixiangDou2}},
  year = {2025}
}
```
