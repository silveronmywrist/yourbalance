import sqlite3
from db import get_connection

connection = get_connection()

connection.execute("PRAGMA foreign_keys = ON")

connection.execute("""
    CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL CHECK (kind IN ('income', 'expense'))
    )
""")

connection.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    category_id INTEGER NOT NULL,
    amount_kopeks INTEGER NOT NULL CHECK (amount_kopeks > 0),
    date TEXT NOT NULL,
    comment TEXT,
    FOREIGN KEY (category_id) REFERENCES categories(id)
    )
""")

connection.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY,
    category_id INTEGER NOT NULL,
    month TEXT NOT NULL,
    limit_kopeks INTEGER NOT NULL CHECK (limit_kopeks > 0),
    
    FOREIGN KEY (category_id) REFERENCES categories(id),
    UNIQUE (category_id, month)
    )
""")

connection.commit()
connection.close()

