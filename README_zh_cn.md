[English](README_en.md) | 简体中文

<div align="center">
<img src="resource/logo.png" width="160px"/>
</div>

HuixiangDou2 是一套 KG-LLM Retrieval 实现。

在 [HuixiangDou1](https://github.com/internlm/huixiangdou) 基础上完成精度优化和 `async` 重构：
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

## 致谢
- [SiliconCloud](https://siliconflow.cn/zh-cn/siliconcloud)    海量 LLM API，部分模型免费
- [KAG](https://github.com/OpenSPG/KAG)    基于推理的图谱检索
- [DB-GPT](https://github.com/eosphoros-ai/DB-GPT)    LLM 工具集合体
- [LightRAG](https://github.com/HKUDS/LightRAG)    简单高效的图谱检索方案