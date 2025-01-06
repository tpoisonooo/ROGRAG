# 代码结构说明

<img src="./figures/huixiangdou.png" width="400">

本文主要解释各目录和功能。文档可能无法随代码即时更新，但已有定义不会再变动。

## 第一层：项目介绍

项目最外层，只有 huixiangdou python module 和 1 个配置文件。

```bash
.
├── config.ini.example  # 配置样例
├── evaluation          # pipeline 精度测试工具
├── huixiangdou         # 实现
├── tests               # 代码片段验证
└── unittest            # 单元测试

`config.ini` 实际是 toml 格式，为了避免用户觉得陌生，改名 windows 常见的 .ini
```

## 第二层：module

huixiangdou 内：

```bash
.
.
├── frontend        # 前端接入方法，如微信、飞书
├── gradio_ui.py    # gradio 接入方法
├── main.py         # 命令行使用方法
├── server.py       # http API 使用方法
..
├── pipeline        # 比较上层的逻辑。即建知识库、查询 pipeline的实现
├── primitive       # 很公用的底层工具，例如 Chunk 定义、切分方法、Embedder 封装。换个 repo 也能 copy 走直接复用
├── service         # 和 HuixiangoDou2 联系比较紧密的中层逻辑。如图谱实现
```

## 第三层：retriever

这里是 HuixiangDou2 具体支持的 retriever 方法：

```bash
.
├── bm25.py         # BM25 方法
├── dense.py        # 稠密检索方法
├── inverted.py     # 倒排索引方法
├── knowledge.py    # 通用的图方法
├── logic           # 逻辑推理图方法
├── web.py          # 网络检索方法
└── pool.py         # 以上所有方法的 factory
```
