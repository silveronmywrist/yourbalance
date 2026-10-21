import sqlite3

connection = sqlite3.connect("expenses.db")

print("Уже доступные категории:")

categories = connection.execute("SELECT name FROM categories")

for c in categories:
    print(c)

while True:
    try:
        name = input("Введите название категории: ")
    except ValueError:
        print("название категории должно быть словом")
        continue

    break

while True:
    try:
        kind = input("трата/прибыль? ")
        if kind == 'трата' or kind == 'Трата' or kind == 'Трата ' or kind == 'трата ':
            kind = 'expense'
        elif kind == 'прибыль' or kind == 'Прибыль' or kind == 'прибыль ' or kind == 'Прибыль ':
            kind = 'income'
        else:
            print("Неизвестная категория")
            continue

        
    except ValueError:
        print("Неправильно введена категория, попробуйте заново ")
        continue

    break


connection.execute("INSERT INTO categories (name, kind) VALUES (?, ?)", (name, kind))

connection.commit()

rows = connection.execute("""
    SELECT id, name, kind FROM categories
""").fetchall()

for row in rows:
    print(row)

connection.close()