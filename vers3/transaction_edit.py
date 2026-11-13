import sqlite3
from db import get_connection
from input_help import read_amount, read_date
def edittransaction():
    connection = get_connection()

    categories = connection.execute("SELECT id, name, kind FROM categories").fetchall()

    while True:
        try:
            index = int(input("Введите номер операции: "))
        except ValueError:
            print("Номер должен быть числом ")
            continue

        transaction = connection.execute("""
        SELECT
            transactions.id,
            transactions.date,
            categories.name,
            transactions.amount_kopeks,
            transactions.comment
            FROM transactions
            JOIN categories ON transactions.category_id = categories.id
            WHERE transactions.id = ?""", (index, )).fetchone()

        if transaction is None:
            print("Операция с таким номером не найдена")
            continue

        break

    transaction_id, date, name, amount, comment = transaction
    rub = amount // 100
    kop = amount % 100
    print(f"№{transaction_id} | {date} | {name} | {rub}.{kop:02d} p | {comment}")

    while True:
        print("\nЧто вы хотите изменить в операции?")
        print("1 — Сумму")
        print("2 — Дату")
        print("3 — Категорию")
        print("4 — Комментарий")
        print("0 — Отменить редактирование")

        field_choice = input("Выберите пункт: ").strip()

        if field_choice in ("0", "1", "2", "3", "4"):
            break

        print("Такого пункта нет. Введите число от 0 до 4.")

    update_query = None
    new_value = None
    new_display = ""

    if field_choice == "0":
        print("Редактирование отменено.")

    elif field_choice == "1":
        new_value = read_amount("Введите новую сумму в рублях: ")
        rubles = new_value // 100
        kopeks = new_value % 100

        new_display = f"{rubles}.{kopeks:02d} ₽"

        update_query = """
            UPDATE transactions
            SET amount_kopeks = ?
            WHERE id = ?
        """

    elif field_choice == "2":
        new_value = read_date("Введите новую дату в формате YYYY-MM-DD: ")

        new_display = new_value

        update_query = """
            UPDATE transactions
            SET date = ?
            WHERE id = ?
        """

    elif field_choice == "3":
        categories = connection.execute(
            "SELECT id, name, kind FROM categories ORDER BY id"
        ).fetchall()

        print("Доступные категории:")

        for category in categories:
            print(f"{category[0]} — {category[1]} ({category[2]})")

        while True:
            try:
                new_category_id = int(input("Введите номер новой категории: "))
            except ValueError:
                print("Номер должен быть целым числом.")
                continue

            selected_category = connection.execute(
                "SELECT id, name, kind FROM categories WHERE id = ?",
                (new_category_id,)
            ).fetchone()

            if selected_category is None:
                print("Такой категории нет.")
                continue

            new_value = selected_category[0]
            new_display = f"{selected_category[1]} ({selected_category[2]})"
            break

        update_query = """
            UPDATE transactions
            SET category_id = ?
            WHERE id = ?
        """

    elif field_choice == "4":
        new_value = input("Введите новый комментарий: ")
        new_display = f"«{new_value}»"

        update_query = """
            UPDATE transactions
            SET comment = ?
            WHERE id = ?
        """

    while True:
        if update_query is not None:
            print(f"Новое значение: {new_display}")

            confirmation = input(
                "Сохранить изменение? y/n: "
            ).strip().lower()

            if confirmation == "y":
                connection.execute(
                    update_query,
                    (new_value, transaction_id)
                )

                connection.commit()
                print("Операция изменена.")
            elif confirmation == 'n':
                print("Изменение отменено.")
            else:
                print("Выберите y или n")
                continue
        break
    connection.close()

if __name__ == "__main__":
    edittransaction()