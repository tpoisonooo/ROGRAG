import sqlite3

class DB:
    def __init__(self, filename):
        self.filename = filename
        
    def __enter__(self):
        self.conn = sqlite3.connect(self.filename)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()