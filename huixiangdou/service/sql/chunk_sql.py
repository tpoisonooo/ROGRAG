import sqlite3
import os
from dataclasses import asdict
from ...primitive import Chunk
from typing import List, Optional, Union
import json
from ...primitive import DB

class ChunkSQL:

    def __init__(self, file_dir: str):
        os.makedirs(file_dir, exist_ok=True)
        self.file_dir = file_dir
        self.file_name = os.path.join(self.file_dir, 'chunks.sql')
        with DB(self.file_name) as db:
            db.execute('''
                CREATE TABLE IF NOT EXISTS chunks (
                    _hash TEXT PRIMARY KEY,
                    content TEXT,
                    metadata TEXT,
                    modal TEXT
                )
            ''')

    def add(self, chunk: Union[List[Chunk], Chunk]):
        """Add a new chunk to the database."""
        if type(chunk) is not list:
            chunks = [chunk]
        else:
            chunks = chunk

        with DB(self.file_name) as db:
            for c in chunks:
                db.execute(
                    '''
                    INSERT OR IGNORE INTO chunks (_hash, content, metadata, modal)
                    VALUES (?, ?, ?, ?)
                ''', (c._hash, c.content_or_path,
                    json.dumps(c.metadata, ensure_ascii=False), c.modal))

    def get(self, _hash: str) -> Optional[Chunk]:
        """Retrieve a chunk by its ID."""
        
        with DB(self.file_name) as db:
            db.execute(
            'SELECT _hash, content, metadata, modal FROM chunks WHERE _hash = ?',
            (_hash, ))
            r = db.fetchone()
            if r:
                c = Chunk(_hash=r[0],
                        content_or_path=r[1],
                        metadata=json.loads(r[2]),
                        modal=r[3])
                return c
        return None

    def exist(self, chunk: Chunk) -> bool:
        # hash `chunk.content_or_path` for faster `SELECT`
        with DB(self.file_name) as db:
            db.execute('SELECT count(*) FROM chunks WHERE _hash = ?',
                            (chunk._hash, ))
            r = db.fetchone()
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
        with DB(self.file_name) as db:
            db.execute('DELETE FROM chunks WHERE _hash = ?', (_hash, ))

# Example usage:
# chunk_manager = ChunkSQLManager('path_to_your_database_directory')
# new_chunk = Chunk(content_or_path="Hello, world!", metadata={"source": "https://example.com"})
# chunk_manager.add_chunk(new_chunk)
# retrieved_chunk = chunk_manager.get_chunk(new_chunk._hash)
# print(retrieved_chunk)
