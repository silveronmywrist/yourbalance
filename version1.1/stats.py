import sqlite3
from datetime import datetime

connection = sqlite3.connect("expenses.db")

while True:
    startdate = input("Введите начальную дату в формате YYYY-MM-DD: ")

    try:
        parsedstartdate = datetime.strptime(startdate, "%Y-%m-%d")
    except ValueError:
        print("Некорректно введена дата")
        continue

    startdate = parsedstartdate.strftime("%Y-%m-%d")
    break

while True:
    enddate = input("Введите конечную дату в формате YYYY-MM-DD: ")

    try:
        parsedenddate = datetime.strptime(enddate, "%Y-%m-%d")
    except ValueError:
        print("Некорректно введена дата")
        continue

    if parsedenddate < parsedstartdate:
        print("Начальная дата не может быть раньше конечной")
        continue

    enddate = parsedenddate.strftime("%Y-%m-%d")
    break

query = ("""
    SELECT COALESCE(SUM(transactions.amount_kopeks), 0)
    FROM transactions
    JOIN categories ON transactions.category_id = categories.id
    WHERE categories.kind = ? AND transactions.date BETWEEN ? AND ?
""")

result = connection.execute(query, ("expense", startdate, enddate)).fetchone()

total_expense = result[0]

rubles = total_expense // 100
kopeks = total_expense % 100

income_result = connection.execute(query, ("income", startdate, enddate)).fetchone()

total_income = income_result[0]
income_rub = total_income // 100
income_kop = total_income % 100

balance = total_income - total_expense

sign = ""
if balance < 0:
    sign = '-'

absolute_balance = abs(balance)

rub_abs_bal = absolute_balance // 100
kop_abs_bal = absolute_balance % 100

print(f"За период с {startdate} по {enddate}:")
print(f"Всего доходов: {income_rub}.{income_kop:02d} р")
print(f"Всего трат: {rubles}.{kopeks:02d} р")
print(f"Ваш баланс: {sign}{rub_abs_bal}.{kop_abs_bal:02d} р")

category_query = """
    SELECT 
        categories.name,
        SUM(transactions.amount_kopeks) AS total
        FROM transactions
        JOIN categories ON transactions.category_id = categories.id
        WHERE categories.kind = ? AND transactions.date BETWEEN ? and ?
        GROUP BY categories.id, categories.name
        ORDER BY total DESC 
"""

rows = connection.execute(category_query, ("expense", startdate, enddate)).fetchall()

print(f"Статистика за период с {startdate} по {enddate}:")
print("Расходы по категориям:")

if not rows:
    print("Расходов пока нет!")

for category_name, total in rows:
    rub = total // 100
    kop = total % 100

    print(f"{category_name}: {rub}.{kop:02d} р")


connection.close()