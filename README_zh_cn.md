[English](./README.md) | 简体中文

# HuixiangDou2: A Robustly Optimized GraphRAG Approach

我们整合四个开源项目——HuixiangDou、KAG、LightRAG 和 DB-GPT，总计 18k 行代码，并在 `Qwen2.5-7B-Instruct` 表现不佳的测试集上进行了对比实验。分数从 60 涨到 74.5，[这里是详细报告](https://github.com/tpoisonooo/HuixiangDou2/blob/main/docs/huixiangdou2_github.pdf)。

<div align="center">
<img src="https://github.com/user-attachments/assets/19558f67-9a3a-48a1-a1c1-7b0a0654602f" width="400">
</div>

## 版本说明

与 [HuixiangDou1](https://github.com/internlm/huixiangdou) 相比做了精度优化和 `async` 重构：
1. **图谱方案**。稠密计算仅用于查询近似实体和关系
2. 移植/合并多个开源实现，代码差异近 10k 行
  - **数据**。整理一套 LLM 未完全见过的、真实领域知识作测试（gpt 准确度 0.53）
  - **消融**。确认不同环节和参数对精度的影响
  - **改进**。相对于无检索方法直接使用 LLM，精度提升 0.22；对比基线实现，提升 0.1
3. API 保持兼容

> **注意**：开源对不同领域/行业的影响不同，我们仅能提供代码实现和测试结论，测试数据无法给出。

如果对你有用，麻烦 star 一下⭐

## 文档

- [1. 如何运行](docs/zh_cn/doc_how_to_run.md)
- [2. 目录结构功能](docs/zh_cn/doc_architecture.md)
- [环境、报错 **FAQ**](https://github.com/tpoisonooo/HuixiangDou2/issues/8)

## 致谢
- [SiliconCloud](https://siliconflow.cn/zh-cn/siliconcloud)    海量 LLM API，部分模型免费
- [KAG](https://github.com/OpenSPG/KAG)    基于推理的图谱检索
- [DB-GPT](https://github.com/eosphoros-ai/DB-GPT)    LLM 工具集合体
- [LightRAG](https://github.com/HKUDS/LightRAG)    简单高效的图谱检索方案

## 引用
```text
@misc{huixiangdou2,
  author = {Huanjun Kong},
  title = {HuixiangDou2: A Graph-based Augmented Generation Approach},
  howpublished = {\url{https://github.com/tpoisonooo/HuixiangDou2}},
  year = {2025}
}
```
