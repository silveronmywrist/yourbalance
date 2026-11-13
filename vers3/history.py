from input_help import read_date
from db import get_connection

def show_history():

    connection = get_connection()

    date = read_date("Введите начальную дату в формате YYYY-MM-DD: ")

    while True:
        dateend = read_date("Введите конечную дату в том же формате: ")
        if dateend < date:
            print("Конечная дата не может быть меньше начальной!")
            continue

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

if __name__ == "__main__":
    show_history()