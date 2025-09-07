import sqlite3
import os
import json
from typing import List, Union, Set
from ...primitive import DB

# Just save/or load entity2chunk relation, not support LEFT JOIN the table.
class Entity2ChunkSQL:
    """Save the relationship between Named Entity and Chunk to sqlite"""

    def __init__(self, file_dir: str, ignore_case=True):
        self.file_dir = file_dir
        # case sensitive
        self.ignore_case = ignore_case
        os.makedirs(file_dir, exist_ok=True)
        self.file_name = os.path.join(self.file_dir, 'entity2chunk.sql')
        
        with DB(self.file_name) as db:
            db.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                entity TEXT PRIMARY KEY,
                chunk_ids TEXT
            )
            ''')

    def clean(self):
        with DB(self.file_name) as db:
            db.execute('''DROP TABLE entities;''')
            db.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                entity TEXT PRIMARY KEY,
                chunk_ids TEXT
            )
            ''')

    def insert_relation(self, entity: str, chunk_ids: Union[List[str], str]):
        """Insert the relationship between keywords id and List of chunk_id"""
        if self.ignore_case:
            entity = entity.lower()
        if type(chunk_ids) is not list:
            chunk_ids = [chunk_ids]
        chunk_ids_str = json.dumps(chunk_ids, ensure_ascii=False)
        
        with DB(self.file_name) as db:
            db.execute(
            'INSERT or IGNORE INTO entities (entity, chunk_ids) VALUES (?, ?)',
            (entity, chunk_ids_str))
            
    def get_chunk_ids(self, entities: List[str]) -> Set:
        """Query by entities"""

        counter = dict()
        
        with DB(self.file_name) as db:
            for entity in entities:
                if self.ignore_case:
                    entity = entity.lower()
                db.execute(
                    'SELECT chunk_ids FROM entities WHERE entity = ?', (entity, ))
                result = db.fetchone()
                if result:
                    chunk_ids = json.loads(result[0])
                    for chunk_id in chunk_ids:
                        if chunk_id not in counter:
                            counter[chunk_id] = 1
                        else:
                            counter[chunk_id] += 1

        counter_list = []
        for k, v in counter.items():
            counter_list.append((k, v))
        counter_list.sort(key=lambda item: item[1], reverse=True)
        return counter_list
