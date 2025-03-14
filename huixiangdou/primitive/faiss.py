from __future__ import annotations

import time
import logging
import os
import pdb
import pickle
from pathlib import Path
from typing import (Any, Callable, Dict, Iterable, List, Optional, Sized,
                    Tuple, Union)

import numpy as np
from loguru import logger
from tqdm import tqdm

from .embedder import Embedder
from .query import Query, DistanceStrategy
from .chunk import Chunk
try:
    import faiss
except ImportError:
    raise ImportError(
        'Could not import faiss python package. '
        'Please install it with `pip install faiss-gpu` (for CUDA supported GPU) '
        'or `pip install faiss-cpu` (depending on Python version).')


class Faiss():

    def __init__(
            self,
            index: Any = None,
            chunks: List[Chunk] = [],
            strategy: DistanceStrategy = DistanceStrategy.EUCLIDEAN_DISTANCE,
            k: int = 30):
        """Initialize with necessary components."""
        self.chunks = []
        self.hash2index = dict()
        self.strategy = strategy
        for c in chunks:
            self.upsert(c)
        self.k = k
        self.strategy = strategy
        self.index = index
        self.offset = len(self.chunks)

    def upsert(self, c: Chunk):
        if c._hash in self.hash2index:
            return
        self.hash2index[c._hash] = len(self.chunks)
        self.chunks.append(c)

    def search(self, embedding: np.ndarray) -> List[Tuple[Chunk, float]]:
        """Return chunks most similar to query.

        Args:
            embedding: Embedding vector to look up chunk similar to.
            k: Number of Documents to return. Defaults to 30.

        Returns:
            List of chunks most similar to the query text and L2 distance
            in float for each. High score represents more similarity.
        """
        embedding = embedding.astype(np.float32)
        scores, indices = self.index.search(embedding, self.k)
        pairs = []
        for j, i in enumerate(indices[0]):
            if i == -1:
                # no enough chunks are returned.
                continue
            chunk = self.chunks[i]
            score = scores[0][j]

            if self.strategy == DistanceStrategy.EUCLIDEAN_DISTANCE:
                rel_score = DistanceStrategy.euclidean_relevance_score_fn(
                    score)
            elif self.strategy == DistanceStrategy.MAX_INNER_PRODUCT:
                rel_score = DistanceStrategy.max_inner_product_relevance_score_fn(
                    score)
            else:
                raise ValueError('self.strategy unset')
            pairs.append((chunk, rel_score))

        if len(pairs) >= 2:
            assert pairs[0][1] >= pairs[1][1]
        return pairs

    def similarity_search(self,
                          embedder: Embedder,
                          query: Query,
                          threshold: float = -1) -> List:
        """Return chunks most similar to query.

        Args:
            query: Multimodal query.
            k: Number of Documents to return. Defaults to 30.

        Returns:
            List of chunks most similar to the query text and L2 distance
            in float for each. Lower score represents more similarity.
        """
        if query.text is None and query.image is None:
            raise ValueError(f'Input query is None')

        if query.text is None and query.image is not None:
            if not embedder.support_image:
                logger.info('Embedder not support image')
                return []

        np_feature = embedder.embed_query(text=query.text, path=query.image)
        pairs = self.search(embedding=np_feature)
        # ret = list(filter(lambda x: x[1] >= threshold, pairs))

        highest_score = -1.0
        ret = []
        for pair in pairs:
            if pair[1] >= threshold:
                ret.append(pair)
            if highest_score < pair[1]:
                highest_score = pair[1]

        if len(ret) < 1:
            logger.info('highest score {}, threshold {}'.format(
                highest_score, threshold))
        return ret

    @classmethod
    def split_by_batchsize(self, chunks: List[Chunk] = [], batchsize: int = 4):
        texts = [c for c in chunks if c.modal == 'text']
        fastas = [c for c in chunks if c.modal == 'fasta']
        images = [c for c in chunks if c.modal == 'image']

        block_text = []
        for i in range(0, len(texts), batchsize):
            block_text.append(texts[i:i + batchsize])

        block_image = []
        for i in range(0, len(images), batchsize):
            block_image.append(images[i:i + batchsize])

        block_fasta = []
        for i in range(0, len(fastas), batchsize):
            block_fasta.append(fastas[i:i + batchsize])

        return block_text, block_image, block_fasta

    @classmethod
    def build_index(self, np_feature: np.ndarray,
                    distance_strategy: DistanceStrategy):
        dimension = np_feature.shape[-1]
        ef_construction = 64
        efSearch = 128
        M = 32 #邻居数
        m = 16 #子量化器数量
        pq_nbits = 8
        # max neighours for each node
        # see https://github.com/facebookresearch/faiss/wiki/Indexing-1M-vectors
        if distance_strategy == DistanceStrategy.EUCLIDEAN_DISTANCE:
            index = faiss.IndexHNSWPQ(dimension, m, M)  
            index.metric_type = faiss.METRIC_L2  # Set metric for Euclidean distance
        elif distance_strategy == DistanceStrategy.MAX_INNER_PRODUCT:
            index = faiss.IndexHNSWPQ(dimension, m, M)  
            index.metric_type = faiss.METRIC_IP  # Set metric for inner product
        else:
            raise ValueError('Unknown distance {}'.format(distance_strategy))
        index.hnsw.efSearch = efSearch
        index.hnsw.efConstruction = ef_construction

        return index

    @classmethod
    def save_local(self,
                   folder_path: str,
                   chunks: List[Chunk],
                   embedder: Embedder,
                   offset: int = 0) -> None:
        """Save FAISS index and store to disk.

        Args:
            folder_path: folder path to save.
            chunks: chunks to save.
            embedder: embedding function.
        """

        if len(chunks) < offset:
            raise ValueError(
                f'init offset {offset} while dump size {len(chunks)}')
        save_chunks = chunks[offset:]
        if len(save_chunks) < 1:
            return

        path = Path(folder_path)
        path.mkdir(exist_ok=True, parents=True)

        index_path = os.path.join(path, 'embedding.faiss')
        index = None
        if os.path.exists(index_path):
            index = faiss.read_index(index_path)
        batchsize = 1
        # max neighbours for each node
        try:
            batchsize_str = os.getenv('HUIXIANGDOU_BATCHSIZE')
            if batchsize_str is None:
                logger.info(
                    '`export HUIXIANGDOU_BATCHSIZE=64` for faster feature building.'
                )
            else:
                batchsize = int(batchsize_str)
        except Exception as e:
            logger.error(str(e))
            batchsize = 1

        if batchsize == 1:
            # 存储所有 np_feature
            all_features = []
            for chunk in tqdm(save_chunks, desc='chunks'):
                np_feature = None
                try:
                    if chunk.modal == 'text':
                        np_feature = embedder.embed_query(text=chunk.content_or_path)
                    elif chunk.modal == 'image':
                        np_feature = embedder.embed_query(path=chunk.content_or_path)
                    elif chunk.modal == 'fasta':
                        np_feature = embedder.embed_query(text=chunk.content_or_path)
                    else:
                        raise ValueError(f'Unimplemented chunk type: {chunk.modal}')
                except Exception as e:
                    logger.error(f'Error extracting feature: {e}')
                    continue  # 继续下一个数据

                if np_feature is None:
                    logger.error('np_feature is None')
                    continue               
                all_features.append(np_feature)

            all_features = np.vstack(all_features).astype('float32')  # 转成 (N, D) 矩阵
            if index is None:
                index = self.build_index(
                    np_feature=all_features,
                    distance_strategy=embedder.distance_strategy)
                # **步骤 3：训练索引**
                index.train(all_features)  # 先训练索引
            # **步骤 4：添加数据**
            index.add(all_features)
        else:
            # batching
            block_text, block_image, block_fasta = self.split_by_batchsize(
                chunks=save_chunks, batchsize=batchsize)
            all_features = []
            # 处理文本
            for subchunks in tqdm(block_text, desc='batching_build_text'):
                try:
                    np_features = embedder.embed_query_batch_text(chunks=subchunks)
                    if np_features is not None:
                        all_features.append(np_features)
                except Exception as e:
                    logger.error(f'Error processing text batch: {e}')

            # 处理FASTA
            for subchunks in tqdm(block_fasta, desc='batching_build_fasta'):
                try:
                    np_features = embedder.embed_query_batch_text(chunks=subchunks)
                    if np_features is not None:
                        all_features.append(np_features)
                except Exception as e:
                    logger.error(f'Error processing fasta batch: {e}')

            # 处理图像
            for subchunks in tqdm(block_image, desc='batching_build_image'):
                for chunk in subchunks:
                    try:
                        np_feature = embedder.embed_query(path=chunk.content_or_path)
                        if np_feature is not None:
                            all_features.append(np_feature)
                    except Exception as e:
                        logger.error(f'Error processing image batch: {e}')

            # 统一转换数据格式
            if all_features:
                all_features = np.vstack(all_features).astype('float32')

                if index is None:
                    index = self.build_index(
                        np_feature=all_features,
                        distance_strategy=embedder.distance_strategy)

                    index.train(all_features)  # 训练索引
                index.add(all_features)    # 添加数据
            else:
                logger.error('No valid features extracted, skipping index building.')

        # save index separately since it is not picklable
        faiss.write_index(index, index_path)

        # save chunks
        data = {'chunks': chunks, 'strategy': str(embedder.distance_strategy)}
        with open(path / 'chunks_and_strategy.pkl', 'wb') as f:
            pickle.dump(data, f)

    def save(self, folder_path: str, embedder: Embedder) -> None:
        self.save_local(folder_path=folder_path,
                        chunks=self.chunks,
                        embedder=embedder,
                        offset=self.offset)

    @classmethod
    def load_local(cls, folder_path: str) -> FAISS:
        """Load FAISS index and chunks from disk.

        Args:
            folder_path: folder path to load index and chunks from index.faiss
            index_name: for saving with a specific index file name
        """
        if not os.path.exists(folder_path):
            return cls()

        path = Path(folder_path)
        # load index separately since it is not picklable

        t1 = time.time()
        index = faiss.read_index(str(path / f'embedding.faiss'))
        strategy = DistanceStrategy.UNKNOWN
        t2 = time.time()

        # load docstore
        with open(path / f'chunks_and_strategy.pkl', 'rb') as f:
            data = pickle.load(f)
            chunks = data['chunks']
            strategy_str = data['strategy']

            if 'EUCLIDEAN_DISTANCE' in strategy_str:
                strategy = DistanceStrategy.EUCLIDEAN_DISTANCE
            elif 'MAX_INNER_PRODUCT' in strategy_str:
                strategy = DistanceStrategy.MAX_INNER_PRODUCT
            else:
                raise ValueError(
                    'Unknown strategy type {}'.format(strategy_str))

        t3 = time.time()
        logger.info(
            f'Load faiss, ntotal {index.ntotal}, read index timecost {int(t2-t1)}, read pkl timecost {int(t3-t2)}'
        )
        return cls(index, chunks, strategy)
