import sqlite3
from db import get_connection

def addcategory():
    connection = get_connection()

    print("Уже доступные категории:")

    categories = connection.execute("SELECT name FROM categories")

    for c in categories:
        print(c[0])

    print('\n')
    while True:
        print("1 — Категория расходов")
        print("2 — Категория доходов")

        choice = input("Выберите тип категории: ").strip()

        if choice == "1":
            kind = "expense"
            break
        elif choice == "2":
            kind = "income"
            break

        print("Введите 1 или 2.")


    while True:
        name = input("Введите название категории: ").strip()

        if not name:
            print("Название не должно быть пустым.")
            continue

        try:
            connection.execute(
                "INSERT INTO categories (name, kind) VALUES (?, ?)",
                (name, kind)
            )
        except sqlite3.IntegrityError:
            connection.rollback()
            print("Категория с таким названием уже существует.")
            continue

        connection.commit()
        print(f"Категория «{name}» добавлена.")
        break

    rows = connection.execute("""
        SELECT id, name, kind FROM categories
    """).fetchall()

    for id, name, kind in rows:
        print(f"{id} | {name} | {kind}")

    connection.close()

if __name__ == "__main__":
    addcategory()