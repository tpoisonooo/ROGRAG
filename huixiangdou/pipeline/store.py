"""extract feature and search with user query."""
import argparse
import json
import os
import shutil
import time
from multiprocessing import Pool
from typing import Dict, List, Tuple, Iterator
import random
import pytoml
from loguru import logger
from tqdm import tqdm

from ..primitive import (ChineseRecursiveTextSplitter, Chunk, Faiss, FileName,
                         FileOperation, RecursiveCharacterTextSplitter,
                         nested_split_markdown, split_python_code, BM25Okapi,
                         always_get_an_event_loop)
from ..service import histogram, ChunkSQL, RetrieveResource, SharedRetrieverPool, parse_chunk_to_knowledge


def read_and_save(file: FileName):
    if os.path.exists(file.copypath):
        # already exists, return
        logger.info('already exist, skip load')
        return
    file_opr = FileOperation()
    logger.info('reading {}, would save to {}'.format(file.origin,
                                                      file.copypath))
    content, error = file_opr.read(file.origin)
    if error is not None:
        logger.error('{} load error: {}'.format(file.origin, str(error)))
        return

    if content is None or len(content) < 1:
        logger.warning('{} empty, skip save'.format(file.origin))
        return

    with open(file.copypath, 'w') as f:
        f.write(content)


class FeatureStore:
    """Build knowledge graph for multiple retrievers."""

    def __init__(self,
                 resource: RetrieveResource,
                 language: str = 'zh',
                 chunk_size=900,
                 work_dir: str = 'workdir') -> None:
        """Init with model device type and config."""
        self.language = language
        logger.debug('loading text2vec model..')
        self.embedder = resource.embedder
        self.llm = resource.llm
        self.graph_store = resource.graph_store
        self.chunk_size = chunk_size
        self.work_dir = work_dir
        self.file_opr = FileOperation()

        logger.info('init dense retrieval database with chunk_size {}'.format(
            chunk_size))

        if language == 'zh':
            self.text_splitter = ChineseRecursiveTextSplitter(
                keep_separator=True,
                is_separator_regex=True,
                chunk_size=chunk_size,
                chunk_overlap=32)
        else:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=32)

    def parse_markdown(self, file: FileName,
                       metadata: Dict) -> Tuple[List[Chunk], int]:
        length = 0
        text = file.basename + '\n'

        with open(file.copypath, encoding='utf-8') as f:
            text += f.read()
        if len(text) <= 1:
            return [], length

        chunks = nested_split_markdown(file.origin,
                                       text=text,
                                       chunksize=self.chunk_size,
                                       metadata=metadata)
        for c in chunks:
            length += len(c.content_or_path)
        return chunks, length

    async def build_bm25(self, files: Iterator[FileName]) -> None:
        """Use BM25 for building code feature"""
        # split by function, class and annotation, remove blank
        # build bm25 pickle
        fileopr = FileOperation()
        chunks = []

        for file in files:
            content, error = fileopr.read(file.origin)
            if error is not None:
                continue
            file_chunks = split_python_code(filepath=file.origin,
                                            text=content,
                                            metadata={'source': file.origin})
            chunks += file_chunks

        sparse_dir = os.path.join(self.work_dir, 'db_code')
        bm25 = BM25Okapi()
        bm25.save(chunks, sparse_dir)
        return None

    def split_to_chunks(self, file: FileName) -> Tuple[List[Chunk]]:
        metadata = {'source': file.origin}
        chunks = []
        if file._type == 'md':
            size = 0
            text = file.basename + '\n'

            with open(file.copypath, encoding='utf-8') as f:
                text += f.read()

            chunks = nested_split_markdown(file.origin,
                                           text=text,
                                           chunksize=self.chunk_size,
                                           metadata=metadata)
            for c in chunks:
                size += len(c.content_or_path)
            file.reason = str(size)
            return chunks

        # now read pdf/word/excel/ppt text
        text, error = self.file_opr.read(file.copypath)
        text = file.basename + '\n' + text
        if error is not None:
            file.state = False
            file.reason = str(error)
            raise RuntimeError(f'{file} read error {error}')

        file.reason = str(len(text))
        return self.text_splitter.create_chunks(texts=[text],
                                                metadatas=[metadata])

    async def build_knowledge(self, files: Iterator[FileName]) -> None:
        """Split docs into chunks, build knowledge graph and base based on them."""
        entityDB = Faiss.load_local(
            os.path.join(self.work_dir, 'db_kag_entity'))
        relationDB = Faiss.load_local(
            os.path.join(self.work_dir, 'db_kag_relation'))

        entityDB_mix = Faiss.load_local(
            os.path.join(self.work_dir, 'db_kag_entity_mix'))
        relationDB_mix = Faiss.load_local(
            os.path.join(self.work_dir, 'db_kag_relation_mix'))

        chunkDB = ChunkSQL(file_dir=os.path.join(self.work_dir, 'db_chunk'))

        for file in tqdm(files, 'build knowledge'):
            if not file.state:
                logger.error(f'unknown file state {file}')
                continue

            raw_chunks = self.split_to_chunks(file)
            chunks = []
            for c in raw_chunks:
                if not chunkDB.exist(c):
                    chunks.append(c)
            if len(chunks) < 1:
                logger.info('skip')
                continue

            try:
                await parse_chunk_to_knowledge(chunks=chunks,
                                               llm=self.llm,
                                               entityDB=entityDB,
                                               relationDB=relationDB,
                                               entityDB_mix=entityDB_mix,
                                               relationDB_mix=relationDB_mix,
                                               graph_store=self.graph_store)
                chunkDB.add(chunks)
            except Exception as e:
                logger.error(str(e))
                import pdb
                pdb.set_trace()
                pass
        # dump results
        entityDB.save(folder_path=os.path.join(self.work_dir, 'db_kag_entity'),
                      embedder=self.embedder)
        relationDB.save(folder_path=os.path.join(self.work_dir,
                                                 'db_kag_relation'),
                        embedder=self.embedder)

        entityDB_mix.save(folder_path=os.path.join(self.work_dir,
                                                   'db_kag_entity_mix'),
                          embedder=self.embedder)
        relationDB_mix.save(folder_path=os.path.join(self.work_dir,
                                                     'db_kag_relation_mix'),
                            embedder=self.embedder)
        return None

    async def build_dense(self, files: Iterator[FileName]) -> None:
        """Split docs into chunks, build knowledge graph and base based on them."""
        denseDB = Faiss.load_local(os.path.join(self.work_dir, 'db_dense'))
        for file in tqdm(files, 'build dense'):
            if not file.state:
                logger.error(f'unknown file state {file}')
                continue

            raw_chunks = self.split_to_chunks(file)
            for c in raw_chunks:
                denseDB.upsert(c)
        denseDB.save_local()

    def analyze(self, chunks: List[Chunk]):
        """Output documents length mean, median and histogram."""
        MAX_COUNT = 10000
        if len(chunks) > MAX_COUNT:
            chunks = random.sample(chunks, MAX_COUNT)

        text_lens = []
        token_lens = []
        text_chunk_count = 0
        image_chunk_count = 0

        if self.embedder is None:
            logger.info('self.embedder is None, skip `anaylze_output`')
            return
        for chunk in tqdm(chunks, 'analyze distribution'):
            if chunk.modal == 'image':
                image_chunk_count += 1
            elif chunk.modal == 'text':
                text_chunk_count += 1

            content = chunk.content_or_path
            text_lens.append(len(content))
            token_lens.append(self.embedder.token_length(content))

        logger.info('text_chunks {}, image_chunks {}'.format(
            text_chunk_count, image_chunk_count))
        logger.info('text histogram, {}'.format(histogram(text_lens)))
        logger.info('token histogram, {}'.format(histogram(token_lens)))

    def preprocess(self, repo_dir: str, files: List[FileName]):
        """Preprocesses files in a given directory. Copies each file to
        'preprocess' with new name formed by joining all subdirectories with
        '_'.

        Args:
            files (list): original file list.

        Returns:
            str: Path to the directory where preprocessed markdown files are saved.

        Raises:
            Exception: Raise an exception if no markdown files are found in the provided repository directory.  # noqa E501
        """
        preproc_dir = os.path.join(self.work_dir, 'preprocess')
        os.makedirs(preproc_dir, exist_ok=True)

        pool = Pool(processes=8)
        for _, file in tqdm(enumerate(files), 'preprocess'):
            if not os.path.exists(file.origin):
                file.state = False
                file.reason = 'skip not exist'
                continue

            if file._type == 'image':
                file.state = False
                file.reason = 'skip image'

            elif file._type in ['pdf', 'word', 'excel', 'ppt', 'html']:
                # read pdf/word/excel file and save to text format
                md5 = self.file_opr.md5(file.origin)
                file.copypath = os.path.join(preproc_dir,
                                             '{}.text'.format(md5))
                pool.apply_async(read_and_save, (file, ))

            elif file._type in ['code']:
                md5 = self.file_opr.md5(file.origin)
                file.copypath = os.path.join(preproc_dir,
                                             '{}.code'.format(md5))
                read_and_save(file)

            elif file._type in ['md', 'text', 'json']:
                # rename text files to new dir
                md5 = self.file_opr.md5(file.origin)
                file.copypath = os.path.join(
                    preproc_dir,
                    file.origin.replace(repo_dir + "/", '').replace('/',
                                                                    '_')[-84:])
                try:
                    shutil.copy(file.origin, file.copypath)
                    file.state = True
                    file.reason = 'preprocessed'
                except Exception as e:
                    file.state = False
                    file.reason = str(e)
            else:
                file.state = False
                file.reason = 'skip unknown format'
        pool.close()
        logger.debug('waiting for file preprocess finish..')
        pool.join()

        # check process result
        for file in files:
            if file._type in ['pdf', 'word', 'excel']:
                if os.path.exists(file.copypath):
                    file.state = True
                    file.reason = 'preprocessed'
                else:
                    file.state = False
                    file.reason = 'read error'

    async def init(self, files: List[FileName], args):
        """Initializes response feature store.

        Only needs to be called once. Also calculates the optimal threshold
        based on provided good and bad question examples, and saves it in the
        configuration file.
        """

        code = filter(lambda x: x._type == 'code', files)
        documents = filter(lambda x: x._type != 'code', files)

        await self.build_knowledge(files=documents)
        return
        # tasks = []
        # if 'bm25' in args.method:
        #     tasks.append(self.build_bm25(files=code))

        # if 'knowledge' in args.method:
        #     tasks.append(self.build_knowledge(files=documents))

        # if 'inverted' in args.method:
        #     fasta = Fasta(work_dir=self.work_dir, embedder=self.embedder)
        #     tasks.append(fasta.init(ner_path=args.fasta_ner, file_dir=args.fasta_file))

        # if 'dense' in args.method:
        #     tasks.append(self.build_dense(files=documents))

        # await asyncio.gather(*tasks, return_exceptions=True)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Feature store for processing directories.')
    parser.add_argument('--work_dir',
                        type=str,
                        default='workdir',
                        help='Working directory.')
    parser.add_argument(
        '--method',
        nargs='+',
        choices=['knowledge', 'dense', 'inverted', 'bm25'],
        default=['knowledge', 'inverted', 'bm25'],
        help='Supported retrieve method, use knowledge and sparse by default.')
    parser.add_argument(
        '--repo_dir',
        type=str,
        default='repodir',
        help='Root directory where the repositories are located.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        help='Feature store configuration path. Default value is config.ini')
    parser.add_argument(
        '--fasta_ner',
        default=None,
        help=
        'The path of NER file, which is a dumped json list. HuixiangDou would build relationship between entities and chunks for retrieve.'
    )
    parser.add_argument(
        '--fasta_file',
        default=None,
        help='Path of .fasta file, which is a dumped json list.')
    args = parser.parse_args()
    return args


async def write_back_config_threshold(resource: RetrieveResource,
                                      work_dir: str, config_path: str):
    """Update reject threshold based on positive and negative examples."""
    from sklearn.metrics import precision_recall_curve
    import numpy as np

    with open(os.path.join('resource', 'good_questions.json'), encoding='utf-8') as f:
        good_questions = json.load(f)
    with open(os.path.join('resource', 'bad_questions.json'), encoding='utf-8') as f:
        bad_questions = json.load(f)
    if len(good_questions) == 0 or len(bad_questions) == 0:
        raise Exception('good and bad question examples cat not be empty.')

    questions = good_questions + bad_questions
    predictions = []

    # retrieve score
    pool = SharedRetrieverPool(resource=resource)
    retriever = pool.get(work_dir=work_dir)

    for question in questions:
        score = await retriever.similarity_score(query=question)
        predictions.append(max(0, score))

    labels = [1 for _ in range(len(good_questions))
              ] + [0 for _ in range(len(bad_questions))]
    precision, recall, thresholds = precision_recall_curve(labels, predictions)

    # get the best index for sum(precision, recall)
    sum_precision_recall = precision[:-1] + recall[:-1]
    index_max = np.argmax(sum_precision_recall)
    optimal_threshold = max(thresholds[index_max], 0.0)

    with open(config_path, encoding='utf-8') as f:
        config = pytoml.load(f)
    config['store']['reject_threshold'] = float(optimal_threshold)
    with open(config_path, 'w', encoding='utf-8') as f:
        pytoml.dump(config, f)
    logger.info(
        f'The optimal threshold is: {optimal_threshold}, saved it to {config_path}'  # noqa E501
    )


if __name__ == '__main__':
    args = parse_args()
    # build embedding/reranker models
    resource = RetrieveResource(config_path=args.config_path)
    store = FeatureStore(resource=resource, work_dir=args.work_dir)

    # convert pdf/excel/ppt to markdown
    files = store.file_opr.scan_dir(repo_dir=args.repo_dir)
    store.preprocess(repo_dir=args.repo_dir, files=files)

    loop = always_get_an_event_loop()

    before = resource.llm.sum_input_token_size, resource.llm.sum_output_token_size, time.time(
    )
    loop.run_until_complete(store.init(files=files, args=args))
    store.file_opr.summarize(files)

    after = resource.llm.sum_input_token_size, resource.llm.sum_output_token_size, time.time(
    )
    logger.info('input token {}, output token {}, timecost {}'.format(after[0]-before[0], after[1]-before[1], after[2]-before[2]))
    del store

    # calculate config threshold, write it back
    loop.run_until_complete(write_back_config_threshold(resource=resource, work_dir=args.work_dir, config_path=args.config_path))