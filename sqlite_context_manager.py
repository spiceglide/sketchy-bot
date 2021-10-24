import sqlite3

class db():
    def __init__(self, file='data.db'):
        self.file = file
    def __enter__(self):
        self.connection = sqlite3.connect(self.file)
        return self.connection.cursor()
    def __exit__(self, type, value, traceback):
        self.connection.commit()
        self.connection.close()