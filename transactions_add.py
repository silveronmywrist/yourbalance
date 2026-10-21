import sqlite3
from datetime import datetime
from decimal import Decimal, InvalidOperation

connection = sqlite3.connect("expenses.db")

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

while True:
        amount_text = input("Введите сумму в рублях: ")
        amount_text = amount_text.replace(',', '.')
        try:
            amount_rub = Decimal(amount_text)
        except ValueError:
            print("Сумма должна быть числом")
            continue

        if not amount_rub.is_finite():
            print("Сумма не может быть бесконечной, повторите ввод")
            continue

        if amount_rub.as_tuple().exponent < -2:
            print("После запятой не более двух знаков")
            continue

        if amount_rub <= 0:
            print("Сумма должна быть больше нуля")
            continue

        amount_kopeks = int(amount_rub * 100)
        break

while True:
    date = input("Введите дату в формате YYYY-MM-DD: ")

    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        print("Дата некорректна. Пример: 2026-10-14")
        continue

    date = parsed_date.strftime("%Y-%m-%d")
    break

comment = input("Введите комментарий к операции: ")

connection.execute("""
    INSERT INTO transactions (
        category_id, amount_kopeks, date, comment) VALUES (?, ?, ?, ?)
""", (category_id, amount_kopeks, date, comment))

print("Операция успешно введена!")

connection.commit()
connection.close()

