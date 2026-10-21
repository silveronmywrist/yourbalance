import sqlite3

connection = sqlite3.connect("expenses.db")

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

connection.commit()
connection.close()

