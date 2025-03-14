[English](./README.md) | 简体中文

# HuixiangDou2: A Robustly Optimized GraphRAG Approach
<div>
  <a href="https://arxiv.org/abs/2503.06474" target="_blank">
    <img alt="Arxiv" src="https://img.shields.io/badge/arxiv-2503.06474%20-darkred?logo=arxiv&logoColor=white" />
  </a>
</div>

GraphRAG 有很多地方要调，很难确保是参数生效还是 pipeline 生效。此外大语言模型（LLM）的训练集里其实有 RAG 测试数据。LLM input token 影响生成概率（背景知识：phi-4技术报告、[《当我谈RAG时我谈些什么》](https://link.zhihu.com/?target=https%3A//fatescript.github.io/blog/2024/LLM-RAG/)）。此时无法保证精度提升来源是 key token search 还是检索。

HuixiangDou2 并没有提出新的方法，而是合并多个开源项目——HuixiangDou、KAG、LightRAG 和 DB-GPT，总计 18k 行代码，并在 `Qwen2.5-7B-Instruct` 表现不佳的测试集上进行了对比实验。分数从 60 涨到 74.5。 最终融出一个运行效果得到人类领域专家认可的 GraphRAG 实现。[这里是技术报告](https://arxiv.org/abs/2503.06474)。

<div align="center">
<img src="https://github.com/user-attachments/assets/19558f67-9a3a-48a1-a1c1-7b0a0654602f" width="400">
</div>

> 注意：开源这件事本身，对不同领域/行业的影响各不相同。我们只能提供代码和测试结论，**无法提供测试数据**。

如果对你有用，麻烦 star 一下⭐

## 版本说明

与 [HuixiangDou1](https://github.com/internlm/huixiangdou) 扩展功能相比，v2 专注提升精度：
1. **图谱方案**。稠密计算仅用于查询近似实体和关系
2. 移植/合并多个开源实现，代码差异 ~18k 行
  - **数据**。整理一套 LLM 未完全见过的、真实领域知识作测试（gpt 准确度低于 0.6）
  - **消融**。确认不同环节和参数对精度的影响
  - **改进**。对比表如图
    <div>
    <img src="https://github.com/user-attachments/assets/c3453bc8-85d5-47e1-8160-7ba28a467a70" width="300">
    </div>

3. 版本间的 API 保持兼容。v1 的微信、飞书、 Web 前后端都可以用。具体入参对比：
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

   *  history item 从 `Tuple` 改 `Pair`，是因为二代支持 [Swagger API](./docs/swagger.json)，类似知乎直答的效果
   *  language 从 `zh` 改 `zh_cn`，因为中文本来就有简繁两版
   *  enable_web_search 和 enable_code_search 放进 `query` 里。设计上更合理
   *  request_id 是考虑日志级别，每个 request 的日志应该记录进不同文件，而不是所有用户的处理日志糊到一起
   
## 文档

- [1. 如何运行（命令行、Swagger API、Gradio 三种方式）](docs/zh_cn/doc_how_to_run.md)
- [2. 目录结构功能](docs/zh_cn/doc_architecture.md)
- [环境、报错 **FAQ**](https://github.com/tpoisonooo/HuixiangDou2/issues/8)

## 致谢
- [SiliconCloud](https://siliconflow.cn/zh-cn/siliconcloud)    海量 LLM API，部分模型免费
- [KAG](https://github.com/OpenSPG/KAG)    基于推理的图谱检索
- [DB-GPT](https://github.com/eosphoros-ai/DB-GPT)    LLM 工具集合体
- [LightRAG](https://github.com/HKUDS/LightRAG)    简单高效的图谱检索方案

## 引用
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
