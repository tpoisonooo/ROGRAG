# ROGRAG (HuixiangDou2) - AI Coding Agent Guide

## Project Overview

ROGRAG (Robustly Optimized GraphRAG) is a sophisticated GraphRAG-based system that enhances LLM performance on specialized topics through a two-stage retrieval mechanism. Also known as HuixiangDou2, this project achieves a 15% score boost on SeedBench benchmark and outperforms mainstream RAG methods.

**Key Highlights:**
- Two-stage retrieval for robustness (dual-level and logic form methods)
- Incremental database construction
- Enhanced fuzzy matching and structured reasoning
- Graph-based knowledge retrieval with dense retrieval support

## Technology Stack

**Core Framework:** Python 3.8+ with asyncio support
**Key Dependencies:**
- **ML/AI**: PyTorch (≥2.0.0), Transformers (≥4.38), Sentence Transformers
- **Vector Search**: FAISS-GPU, Scikit-learn
- **Graph Database**: Neo4j with TuGraph support
- **Web Framework**: FastAPI, Uvicorn, Gradio (≥4.41)
- **Data Processing**: Pandas, NumPy (<2.0.0), OpenPyXL
- **Document Processing**: PyMuPDF, python-docx, BeautifulSoup4, readability-lxml
- **LLM Integration**: OpenAI (≥1.0.0), BCEmbedding, TikToken
- **Caching/Queue**: Redis
- **Utilities**: Loguru, Tenacity, NetworkX (≥3.0)

## Architecture & Code Organization

### Directory Structure
```
huixiangdou/                    # Main package
├── main.py                     # CLI entry point
├── server.py                   # HTTP API server
├── gradio_ui.py               # Gradio web interface
├── client.py                  # Client library
├── frontend/                  # Platform integrations
│   ├── lark.py               # Lark/Feishu integration
│   ├── wechat.py             # WeChat integration
│   └── lark_group.py         # Lark group chat support
├── pipeline/                  # Core processing pipelines
│   ├── parallel.py           # Parallel processing pipeline
│   ├── serial.py             # Serial processing pipeline
│   ├── store.py              # Knowledge storage management
│   └── session.py            # Session management
├── primitive/                 # Low-level utilities
│   ├── embedder.py           # Embedding implementations
│   ├── chunk.py              # Text chunking utilities
│   ├── faiss.py              # FAISS operations
│   ├── knowledge.py          # Knowledge graph operations
│   └── file_operation.py     # File handling utilities
└── service/                   # Business logic layer
    ├── retriever/            # Retrieval implementations
    │   ├── bm25.py          # BM25 retrieval
    │   ├── dense.py         # Dense vector retrieval
    │   ├── knowledge.py     # Graph-based retrieval
    │   ├── logic.py         # Logical reasoning retrieval
    │   └── web.py           # Web search integration
    └── llm/                  # LLM provider implementations
```

### Key Configuration Files

**config.ini** (TOML format):
- `[base]`: Working directory configuration
- `[store]`: Embedding and reranker model paths, API settings
- `[tugraph]`: Graph database connection settings
- `[web_search]`: Web search engine configuration (Serper)
- `[llm]`: LLM provider configurations (Alibaba Cloud, etc.)
- `[frontend]`: Platform-specific settings (Lark, WeChat)

## Build & Development Commands

### Installation
```bash
# Standard installation
pip install -r requirements.txt
pip install -e .

# Using uv (recommended for faster installs)
uv venv --python 3.13 --index https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate  # Windows
uv pip install -e . --index https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
```

### Running the Application
```bash
# CLI mode
huixiangdou --work_dir workdir --config_path config.ini

# API server mode (from server.py)
python -m huixiangdou.server

# Gradio UI mode
python -m huixiangdou.gradio_ui
```

### Docker Deployment
```bash
# Use the provided run script
docker run --privileged --gpus all -p 17070:7070 -p 17687:7687 -p 19090:9090 -p 18888:8888 -v /path/to/rograg:/rograg -it crpi-qbn8uku62pfgyukz.cn-shanghai.personal.cr.aliyuncs.com/seedllm/org.cn:20250407 /bin/bash
```

## Testing Strategy

### Test Structure
- **tests/**: Code snippet verification and integration tests
- **unittest/**: Unit tests for individual components
- **evaluation/**: Pipeline accuracy testing tools

### Running Tests
```bash
# Run specific test files
python tests/test_bce.py                    # Test BCE embedding
python tests/test_kimi.py                   # Test Kimi LLM integration
python tests/test_build_milvus_and_filter.py # Test vector database operations

# Run unit tests
python -m unittest discover unittest/
```

### Test Categories
- **Embedding Tests**: BCE, sentence transformers, visual embeddings
- **LLM Integration Tests**: OpenAI, Kimi, DeepSeek, InternLM2
- **Retrieval Tests**: BM25, dense retrieval, hybrid search
- **Database Tests**: Milvus, Neo4j, FAISS operations
- **Pipeline Tests**: End-to-end query processing

## Code Style Guidelines

### Python Standards
- Follow PEP 8 with 4-space indentation
- Use type hints for function parameters and return values
- Async/await pattern for I/O operations
- Loguru for logging with structured data

### Naming Conventions
- **Classes**: PascalCase (e.g., `ParallelPipeline`)
- **Functions/Methods**: snake_case (e.g., `generate_response()`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_TOKEN_SIZE`)
- **Private Methods**: Prefix with underscore (e.g., `_internal_method()`)

### Error Handling
- Use specific exception types
- Implement proper async error handling
- Log errors with context using Loguru
- Graceful degradation for external service failures

## Security Considerations

### Configuration Security
- **API Keys**: Store in environment variables, never commit to version control
- **Database Credentials**: Use connection strings with proper authentication
- **Model Paths**: Ensure secure file permissions for model directories

### Data Protection
- **User Data**: Implement proper data sanitization for chat inputs
- **File Operations**: Validate file types and sizes before processing
- **Network Security**: Use HTTPS for all external API calls

### Access Control
- **Frontend Integrations**: Implement proper webhook verification
- **API Rate Limiting**: Configure RPM/TPM limits in config.ini
- **Database Access**: Use authenticated connections with proper user roles

## API Compatibility

The project maintains backward compatibility with HuixiangDou v1 API while providing enhanced v2 capabilities:

**v1 API** (Legacy):
```python
async def generate(self, query: Union[Query, str], history: List[Tuple[str]]=[], language: str='zh', enable_web_search: bool=True, enable_code_search: bool=True)
```

**v2 API** (Current):
```python
async def generate(self, query: Union[Query, str], history: List[Pair] = [], request_id: str = 'default', language: str = 'zh_cn')
```

## Performance Optimization

### Two-Stage Retrieval
1. **Stage 1**: Dense retrieval for similar entities and relationships
2. **Stage 2**: Logical reasoning and structured query processing

### Caching Strategy
- Redis for session management and query caching
- FAISS for efficient vector similarity search
- Graph database for structured knowledge retrieval

### Model Optimization
- Support for GPU acceleration with CUDA
- Batched processing for embedding operations
- Incremental knowledge base construction

## Deployment Notes

### Prerequisites
- Python 3.8+ with pip/uv package manager
- CUDA-compatible GPU for optimal performance
- Redis server for caching
- Neo4j/TuGraph for graph database operations

### Production Considerations
- Configure proper logging levels
- Set up monitoring for API endpoints
- Implement health checks for external services
- Use environment-specific configuration files