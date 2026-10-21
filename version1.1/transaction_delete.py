import sqlite3

connection = sqlite3.connect("expenses.db")

while True:
    try:
        transaction_id = int(input('Введите номер операции для удаления: '))
    except ValueError:
        print("Номер должен быть числом")
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
        WHERE transactions.id = ?""", (transaction_id, )).fetchone()

    if transaction is None:
        print("Операция с таким номером не найдена")
        continue

    break

transaction_id, date, name, amount, comment = transaction

rubles = amount // 100
kopeks = amount % 100

print(f"№{transaction_id} | {date} | {name} | {rubles}.{kopeks:02d} p | comment")
while True:
    confirmation = input("Удалять эту операцию? y/n: ").strip().lower()
    if confirmation == 'y':
        connection.execute("DELETE from transactions WHERE id = ?", (transaction_id, ))
        connection.commit()
        print(f"Операция {transaction_id} была удалена")
    elif confirmation == 'n':
        print("Операция не была удалена")
    else:
        print("Повторите ввод")
        continue
    break

connection.close()