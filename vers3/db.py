import sqlite3
from pathlib import Path


def get_connection():
    db_path = Path(__file__).resolve().parent / "expenses.db"
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection   

