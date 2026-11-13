import sqlite3
from db import get_connection
from input_help import read_month, read_amount
def setbudget():
    connection = get_connection()

    categories = connection.execute("""
        SELECT id, name FROM categories WHERE kind = ? ORDER BY id""", ("expense", )).fetchall()

    print("Категория расходов: ")

    for category in categories:
        print(f"{category[0]} - {category[1]}")

    while True:
        try:
            category_id = int(input("Введите номер категории: "))
        except ValueError:
            print("Номер должен быть целым числом.")
            continue

        category = connection.execute("""
            SELECT id, name
            FROM categories
            WHERE id = ? AND kind = ?
        """, (category_id, "expense")).fetchone()

        if category is None:
            print("Выберите существующую категорию расходов.")
            continue

        break

    month = read_month("Введите месяц бюджета в формате YYYY-MM: ")
    limit_kopeks = read_amount("Введите ограничение: ")

    existing_budget = connection.execute("""
        SELECT id, limit_kopeks
        FROM budgets
        WHERE category_id = ? AND month = ?
    """, (category_id, month)).fetchone()

    if existing_budget is None:
        connection.execute("""
            INSERT INTO budgets (category_id, month, limit_kopeks)
            VALUES (?, ?, ?)
        """, (category_id, month, limit_kopeks))

        connection.commit()
        print("Новый бюджет сохранён.")

    else:
        budget_id, old_limit = existing_budget

        old_rubles = old_limit // 100
        old_kopeks = old_limit % 100

        new_rubles = limit_kopeks // 100
        new_kopeks = limit_kopeks % 100

        print(f"Категория: {category[1]}, месяц: {month}")
        print(f"Текущий лимит: {old_rubles}.{old_kopeks:02d} ₽")
        print(f"Новый лимит: {new_rubles}.{new_kopeks:02d} ₽")

        confirmation = input(
            "Изменить установленный лимит? Введите да: "
        ).strip().lower()

        if confirmation == "да":
            connection.execute("""
                UPDATE budgets
                SET limit_kopeks = ?
                WHERE id = ?
            """, (limit_kopeks, budget_id))

            connection.commit()
            print("Лимит изменён.")
        else:
            print("Изменение отменено.")

    connection.close()

if __name__ == "__main__":
    setbudget()