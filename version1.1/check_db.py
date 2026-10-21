import sqlite3

connection = sqlite3.connect("expenses.db")

c = connection.execute("""
    SELECT
    transactions.id,
    categories.name,
    transactions.amount_kopeks,
    transactions.date,
    transactions.comment
    FROM transactions
    JOIN categories ON transactions.category_id = categories.id
""").fetchall()

for ch in c:
    print(ch)

connection.close()