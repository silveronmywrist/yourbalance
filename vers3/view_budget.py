from db import get_connection
from input_help import read_month

def budgetview(): 

    def format_money(amount_kopeks):
        sign = ""

        if amount_kopeks < 0:
            sign = '-'

        amount_kopeks = abs(amount_kopeks)
        rubles = amount_kopeks // 100
        kopeks = amount_kopeks % 100

        return f"{sign}{rubles}.{kopeks:02d} p"

    month = read_month("Введите месяц бюджета в формате YYYY-MM: ")
    connection = get_connection()

    query = """
        SELECT
            categories.name,
            budgets.limit_kopeks,
            COALESCE(SUM(transactions.amount_kopeks), 0) AS spent
        FROM budgets
        JOIN categories ON budgets.category_id = categories.id
        LEFT JOIN transactions
            ON transactions.category_id = budgets.category_id
            AND strftime('%Y-%m', transactions.date) = budgets.month
        WHERE budgets.month = ?
        AND categories.kind = 'expense'
        GROUP BY budgets.id, categories.name, budgets.limit_kopeks
        ORDER BY categories.name"""

    rows = connection.execute(query, (month, )).fetchall()
    print(f"Бюджеты за {month}:")

    if not rows:
        print("На этот месяц бюджеты не установлены.")

    for category_name, limit, spent in rows:
        remaining = limit - spent

        print(f"\n{category_name}")
        print(f"Лимит: {format_money(limit)}")
        print(f"Потрачено: {format_money(spent)}")
        print(f"Остаток: {format_money(remaining)}")

        if remaining < 0:
            print("Бюджет превышен.")
    connection.close()

if __name__ == "__main__":
    budgetview()