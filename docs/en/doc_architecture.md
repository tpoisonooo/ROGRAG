# Code Structure Explanation

This document primarily explains the directories and their functions. The document may not always be updated in sync with the code, but once defined, the structure will not change.

## First Level: Project Introduction

At the outermost level of the project, there are only modules and one configuration file.

```bash
.
├── config.ini.example  # Configuration example
├── evaluation          # Pipeline accuracy testing tool
├── huixiangdou         # Implementation
├── tests               # Code snippet verification
└── unittest            # Unit tests
```

`config.ini.example` is actually in TOML format, but it is renamed to the more familiar `.ini` format commonly used in Windows to avoid confusion for users.

## Second Level: Modules

Inside `huixiangdou`:

```bash
.
.
├── frontend        # Front-end access methods, such as WeChat, Feishu
├── gradio_ui.py    # Gradio access method
├── main.py         # Command-line usage method
├── server.py       # HTTP API usage method
..
├── pipeline        # Higher-level logic. Implementation of building knowledge bases and query pipelines
├── primitive       # Very commonly used low-level tools, such as Chunk definitions, splitting methods, Embedder encapsulation. Can be copied and reused directly in another repository
├── service         # Middle-level logic closely related to HuixiangDou2. For example, graph implementation
```

## Third Level: Retriever

This is the specific retriever methods supported:

```bash
.
├── bm25.py         # BM25 method
├── dense.py        # Dense retrieval method
├── inverted.py     # Inverted index method
├── knowledge.py    # General graph method
├── logic           # Logical reasoning graph method
├── web.py          # Web retrieval method
└── pool.py         # Factory for all the above methods
```
