import os
import pdb

from huixiangdou.primitive import Chunk, Embedder, Faiss, Query
import random
from dataclasses import dataclass, field
import uuid

@dataclass
class Chunk:
    content_or_path: str
    metadata: dict
    modal: str = None
    _hash: str = field(default_factory=lambda: Chunk.generate_hash())

    @staticmethod
    def generate_hash():
        return str(uuid.uuid4())[0:6]

def test_faiss():
    chunks = []
    for i in range(300):
        content_or_path = f"This is chunk number {i}"  # Text content
        metadata = {'source': f'unittest_{i}' if i % 2 == 0 else f'test_text_{i}'}
        modal = 'text'  # Text type, no modal specified

        chunk = Chunk(content_or_path=content_or_path, metadata=metadata, modal=modal)
        chunks.append(chunk)
    
    a = Chunk(content_or_path='hello world', metadata={'source': 'unittest'}, modal = 'text')
    b = Chunk(content_or_path='/data/wangzhefan/HuixiangDou2/resource/figures/IMG_0040.JPG',  metadata={'source': 'unittest'},
              modal='image')
    c = Chunk(content_or_path='resource/figures/wechat.jpg',  metadata={'source': 'test image'},modal='image')
    # chunks = [a, b, c]
    chunks.append(a)
    chunks.append(b)
    chunks.append(c)
    # import pdb
    # pdb.set_trace()
    save_path = '/tmp/faiss'

    model_config = {
        # https://huggingface.co/BAAI/bge-visualized
        'embedding_model_path': '/data/wangzhefan/HuixiangDou2/model/BAAI/bge-m3'
    }
    embedder = Embedder(model_config)

    Faiss.save_local(folder_path=save_path, chunks=chunks, embedder=embedder)
    assert os.path.exists(os.path.join(save_path, 'embedding.faiss'))

    g = Faiss.load_local(save_path)
    for idx, c in enumerate(g.chunks):
        assert str(chunks[idx]) == str(c)

    target = '/data/wangzhefan/HuixiangDou2/resource/figures/IMG_0040.JPG'
    query = Query(image=target)
    pairs = g.similarity_search(query=query, embedder=embedder)
    chunk, score = pairs[0]
    assert chunk.content_or_path == target
    assert score >= 0.9999

    target1 = 'This is chunk number 100'
    query = Query(text=target1)
    pairs = g.similarity_search(query=query, embedder=embedder)
    chunk, score = pairs[0]
    assert chunk.content_or_path == target1
    assert score >= 0.9999


if __name__ == '__main__':
    test_faiss()
