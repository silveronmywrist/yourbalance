import sqlite3
from datetime import datetime

connection = sqlite3.connect("expenses.db")

while True:
    date = input("Начальная дата в формате YYYY-MM-DD: ")

    try:
        parseddate = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        print("Попробуйте еще раз")
        continue

    date = parseddate.strftime('%Y-%m-%d')
    break

while True:
    dateend = input("Конечная дата в формате YYYY-MM-DD: ")

    try:
        parseddateend = datetime.strptime(dateend, '%Y-%m-%d')
    except ValueError:
        print("Попробуйте еще раз")
        continue

    if parseddateend < parseddate:
        print("Конечная дата не может быть раньше начальной")
        continue

    dateend = parseddateend.strftime('%Y-%m-%d')
    break


while True:
    operation_type = input(
        "Тип операций: all — все, expense — расходы, income — доходы: "
    ).strip().lower()

    if operation_type in ("all", "expense", "income"):
        break

    print("Введите all, expense или income.")

query = """
    SELECT 
        transactions.id,
        transactions.date,
        categories.name,
        transactions.amount_kopeks,
        transactions.comment
    FROM transactions
    JOIN categories ON transactions.category_id = categories.id
    WHERE transactions.date BETWEEN ? and ? AND (? = 'all' OR categories.kind = ?)
    ORDER BY transactions.date DESC, transactions.id DESC
    """

rows = connection.execute(query, (date, dateend, operation_type, operation_type)).fetchall()


print(f"История операций с {date} по {dateend}:")

if not rows:
    print("Операций нет")

for transactions_id, date, category_name, amount, comment in rows:
    rubles = amount // 100
    kopeks = amount % 100

    print(f'№{transactions_id} | {date} | {category_name} | {rubles}.{kopeks:02d} p | {comment}')


connection.close()