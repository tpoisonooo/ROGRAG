# ROGRAG (Robustly Optimized GraphRAG) - AI Agent Documentation

## Project Overview

ROGRAG is a sophisticated GraphRAG (Graph Retrieval-Augmented Generation) system developed by tpoisonooo. It represents an advanced RAG framework that leverages graph-based knowledge representation and retrieval, achieving a 15% performance boost on SeedBench benchmark compared to mainstream RAG methods.

**Key Features:**
- Two-stage retrieval mechanism (dual-level and logic form methods)
- Graph-based knowledge construction and retrieval
- Multiple retrieval methods: BM25, dense retrieval, graph-based, web search
- Multi-platform frontend support (WeChat, Lark/Feishu, web interface)
- Incremental database construction with enhanced fuzzy matching

## Technology Stack

**Core Technologies:**
- **Language**: Python 3.8-3.11
- **Graph Database**: TuGraph (Neo4j-compatible)
- **Vector Database**: FAISS (Facebook AI Similarity Search)
- **ML Framework**: PyTorch 2.0+
- **LLM Integration**: OpenAI-compatible APIs, VLLM for local serving

**Key Dependencies:**
- **AI/ML**: `torch`, `transformers`, `sentence_transformers`, `openai>=1.0.0`
- **Graph Processing**: `networkx>=3.0`, `neo4j`
- **Vector Search**: `faiss-gpu`
- **Document Processing**: `pymupdf`, `python-docx`, `beautifulsoup4`, `readability-lxml`
- **Web Framework**: `fastapi`, `uvicorn`, `gradio>=4.41`

## Project Structure

```
/data/khj/workspace/ttt/rograg/
├── huixiangdou/                    # Main Python package
│   ├── pipeline/                   # High-level logic (ParallelPipeline, SerialPipeline)
│   ├── primitive/                  # Low-level tools (Chunk, Embedder, Splitter, etc.)
│   ├── service/                    # Middle-level logic
│   │   ├── retriever/             # Retrieval implementations
│   │   │   ├── bm25.py            # BM25 retrieval
│   │   │   ├── dense.py           # Dense retrieval
│   │   │   ├── knowledge.py       # Graph-based knowledge retrieval
│   │   │   ├── logic/             # Logical reasoning graph methods
│   │   │   └── web.py             # Web retrieval
│   │   ├── graph_store.py         # Graph storage implementation
│   │   └── nlu.py                 # Natural Language Understanding
│   ├── frontend/                   # Chat platform integrations
│   ├── main.py                     # CLI entry point
│   ├── server.py                   # HTTP API server
│   └── gradio_ui.py               # Gradio web interface
├── evaluation/                     # Pipeline accuracy testing tools
├── tests/                         # Integration tests
├── unittest/                      # Unit tests
├── docs/                          # Documentation (English/Chinese)
└── workdir/                       # Working directory for data
```

## Build and Test Commands

### Build Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Setup script (installs dependencies)
./setup.sh

# Install package in development mode
pip install -e .

# Docker deployment
sudo docker load -i hxd-public.tar
sudo docker run --gpus all -p 17070:7070 -p 17687:7687 -p 19090:9090 -p 18888:8888 -it hxd-public /bin/bash
```

### Test Commands
```bash
# Run individual tests
python tests/test_*.py

# Run daily smoke tests
python unittest/service/daily_smoke.py

# Run unit tests
python unittest/primitive/test_*.py
```

### Startup Commands
```bash
# Start services (from run.sh)
/usr/local/bin/lgraph_server -d start -c /root/lgraph.json --log_dir ""
nohup vllm serve /root/Qwen2.5-7B-Instruct --enable-prefix-caching --served-model-name Qwen2.5-7B-Instruct --port 8000 --tensor-parallel-size 1 &

# Start main application
python -m huixiangdou.main

# Start web UI
python -m huixiangdou.gradio_ui

# Start API server
python -m huixiangdou.server
```

## Code Style Guidelines

### Python Style
- **Linting**: pylint with comprehensive configuration (`.pylintrc`)
- **Line length**: 100 characters maximum
- **Indentation**: 4 spaces
- **Naming conventions**: snake_case for functions/variables, PascalCase for classes

### Documentation
- **Docstring format**: Google-style and NumPy-style supported via Sphinx Napoleon
- **Bilingual codebase**: Mixed Chinese and English comments acceptable
- **Type hints**: Encouraged but not strictly enforced

### Error Handling
```python
# Use custom error codes
from huixiangdou.service import ErrorCode

class ErrorCode(Enum):
    SUCCESS = 0, 'success'
    NOT_A_QUESTION = 1, 'query is not a question'
```

### Logging
```python
from loguru import logger

# Use contextual logging
logger.info(f'{__file__} {operation_info}')
logger.error(f'Error occurred: {str(e)}')
```

## Testing Instructions

### Test Structure
- **Integration tests**: `tests/` directory (35+ test files)
- **Unit tests**: `unittest/` directory
- **Daily smoke tests**: `unittest/service/daily_smoke.py`

### Test Categories
- LLM provider tests (OpenAI, Kimi, DeepSeek, etc.)
- Embedding model tests
- Document processing tests
- Graph operation tests
- Web search integration tests

### Running Tests
```bash
# Run specific test category
python tests/test_llm_client_openai.py
python tests/test_embeddings.py

# Run smoke tests
python unittest/service/daily_smoke.py
```

## Security Considerations

### ⚠️ CRITICAL SECURITY ISSUES IDENTIFIED

1. **Hardcoded Credentials**: Configuration files contain hardcoded sensitive information
2. **Input Validation**: Limited validation on file upload endpoints
3. **Path Traversal**: File operations lack proper sanitization
4. **No HTTPS**: API endpoints run on HTTP without TLS
5. **No Authentication**: Most API endpoints lack authentication

### Security Requirements
- Move all credentials to environment variables
- Implement comprehensive input validation
- Add HTTPS with proper TLS configuration
- Implement API authentication and authorization
- Add file type and size validation for uploads

### Configuration Security
- Never commit sensitive data to version control
- Use secure configuration management
- Implement credential rotation mechanisms

## Development Workflow

### Configuration
Main configuration file: `config.ini`
- TuGraph database settings
- LLM API configurations
- Embedding model settings
- Frontend integration settings

### Requirements
- GPU memory: 24GB total
- Python: 3.8-3.11
- CUDA: 12.4+ (for GPU support)

### Interfaces
- **CLI**: `python -m huixiangdou.main`
- **Web UI**: Gradio interface (port 7860)
- **API Server**: FastAPI with Swagger (port 8888)
- **Docker**: Pre-built image available

## Architecture Patterns

### Retrieval Pipeline
1. **Two-stage retrieval**: Dual-level and logic form methods
2. **Multiple retrieval sources**: BM25, dense, graph-based, web search
3. **Knowledge graph construction**: Incremental building with fuzzy matching
4. **Multi-modal support**: Text, documents, web content

### Frontend Integration
- WeChat integration
- Lark/Feishu support
- Web interface via Gradio
- RESTful API

## Common Development Tasks

### Adding New Retrieval Methods
1. Implement in `huixiangdou/service/retriever/`
2. Follow existing patterns (e.g., `bm25.py`, `dense.py`)
3. Add corresponding tests
4. Update pipeline configuration

### Adding New LLM Providers
1. Add client in appropriate module
2. Follow OpenAI-compatible API pattern
3. Add configuration in `config.ini`
4. Create integration tests

### Modifying Frontend
1. Web UI: Edit `huixiangdou/gradio_ui.py`
2. API endpoints: Modify `huixiangdou/server.py`
3. Chat integrations: Update `huixiangdou/frontend/`

## Notes for AI Agents

- This is a research project with production deployment capabilities
- Bilingual codebase (Chinese/English) is intentional and acceptable
- Security vulnerabilities need immediate attention before production use
- Graph database operations require careful handling for SQL injection prevention
- File operations need path traversal protection
- Always validate user inputs and sanitize data before processing