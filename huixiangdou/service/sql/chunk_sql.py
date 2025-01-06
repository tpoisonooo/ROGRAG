import sqlite3
import os
from dataclasses import asdict
from ...primitive import Chunk
from typing import List, Optional, Union
import json
import pdb
from loguru import logger


class ChunkSQL:

    def __init__(self, file_dir: str):
        os.makedirs(file_dir, exist_ok=True)
        self.file_dir = file_dir
        self.conn = sqlite3.connect(os.path.join(file_dir, 'chunks.sql'))
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                _hash TEXT PRIMARY KEY,
                content TEXT,
                metadata TEXT,
                modal TEXT
            )
        ''')
        self.conn.commit()

    def add(self, chunk: Union[List[Chunk], Chunk]):
        """Add a new chunk to the database."""
        if type(chunk) is not list:
            chunks = [chunk]
        else:
            chunks = chunk

        for c in chunks:
            self.cursor.execute(
                '''
                INSERT OR IGNORE INTO chunks (_hash, content, metadata, modal)
                VALUES (?, ?, ?, ?)
            ''', (c._hash, c.content_or_path,
                  json.dumps(c.metadata, ensure_ascii=False), c.modal))
        self.conn.commit()

    def get(self, _hash: str) -> Optional[Chunk]:
        """Retrieve a chunk by its ID."""
        self.cursor.execute(
            'SELECT _hash, content, metadata, modal FROM chunks WHERE _hash = ?',
            (_hash, ))
        r = self.cursor.fetchone()
        if r:
            c = Chunk(_hash=r[0],
                      content_or_path=r[1],
                      metadata=json.loads(r[2]),
                      modal=r[3])
            return c
        return None

    def exist(self, chunk: Chunk) -> bool:
        # hash `chunk.content_or_path` for faster `SELECT`
        self.cursor.execute('SELECT count(*) FROM chunks WHERE _hash = ?',
                            (chunk._hash, ))
        r = self.cursor.fetchone()
        try:
            count = int(r[0])
            if count > 0:
                return True
            return False
        except Exception as e:
            raise RuntimeError(e)
        return False

    def delete(self, _hash: str):
        """Delete a chunk by its ID."""
        self.cursor.execute('DELETE FROM chunks WHERE _hash = ?', (_hash, ))
        self.conn.commit()

    def __del__(self):
        try:
            self.cursor.close()
            self.conn.close()
        except Exception as e:
            logger.error(e)


# Example usage:
# chunk_manager = ChunkSQLManager('path_to_your_database_directory')
# new_chunk = Chunk(content_or_path="Hello, world!", metadata={"source": "https://example.com"})
# chunk_manager.add_chunk(new_chunk)
# retrieved_chunk = chunk_manager.get_chunk(new_chunk._hash)
# print(retrieved_chunk)
