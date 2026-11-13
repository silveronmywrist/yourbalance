import sqlite3
from datetime import datetime
from input_help import read_amount, read_date
from db import get_connection
def addtransaction():
    connection = get_connection()

    connection.execute("PRAGMA foreign_keys = ON")

    categories = connection.execute("SELECT id, name, kind FROM categories").fetchall()

    print("Доступные категории:")

    for category in categories:
        print(f"{category[0]} — {category[1]} ({category[2]})")

    while True:
        try:
            category_id = int(input("Введите номер категории: "))
        except ValueError:
            print("Номер должен быть целым числом")
            continue

        category = connection.execute("SELECT id, name FROM categories WHERE id = ?", (category_id,)).fetchone()

        if category is None:
            print("Такой категории нет, Выберите номер из списка")
            continue

        print(f"Выбрана категория: {category[1]}")
        break

    amount_kopeks = read_amount("Введите сумму в рублях: ")

    date = read_date("Введите дату в формате YYYY-MM-DD: ")

    comment = input("Введите комментарий к операции: ")

    connection.execute("""
        INSERT INTO transactions (
            category_id, amount_kopeks, date, comment) VALUES (?, ?, ?, ?)
    """, (category_id, amount_kopeks, date, comment))

    print("Операция успешно введена!")

    connection.commit()
    connection.close()

if __name__ == "__main__":
    addtransaction()