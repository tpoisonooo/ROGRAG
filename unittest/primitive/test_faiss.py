import os
import pdb

from huixiangdou.primitive import Chunk, Embedder, Faiss, Query


def test_faiss():
    a = Chunk(content_or_path='hello world', metadata={'source': 'unittest'})
    b = Chunk(content_or_path='resource/figures/inside-mmpose.jpg',  metadata={'source': 'unittest'},
              modal='image')
    c = Chunk(content_or_path='resource/figures/wechat.jpg',  metadata={'source': 'test image'},modal='image')
    chunks = [a, b, c]

    save_path = '/tmp/faiss'

    model_config = {
        'embedding_model_path': '/data2/khj/bge-m3'
    }
    embedder = Embedder(model_config)

    Faiss.save_local(folder_path=save_path, chunks=chunks, embedder=embedder)
    assert os.path.exists(os.path.join(save_path, 'embedding.faiss'))

    g = Faiss.load_local(save_path)
    for idx, c in enumerate(g.chunks):
        assert str(chunks[idx]) == str(c)

    target = 'resource/figures/inside-mmpose.jpg'
    query = Query(image=target)
    pairs = g.similarity_search(query=query, embedder=embedder)
    chunk, score = pairs[0]
    assert chunk.content_or_path == target
    assert score >= 0.9999


if __name__ == '__main__':
    test_faiss()