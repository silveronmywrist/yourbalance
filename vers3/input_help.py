from decimal import Decimal, InvalidOperation
from datetime import datetime

def read_date(prompt):
    while True:
        date = input(prompt)

        try:
            parsed_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            print("Введите дату в корректном формате")
            continue
        return parsed_date.strftime('%Y-%m-%d')

def read_amount(prompt):
    while True:
        amount_text = input(prompt).replace(',', '.')

        try:
            amount_rub = Decimal(amount_text)
        except InvalidOperation:
            print("Введите число")
            continue
        if not amount_rub.is_finite():
            print("Введите конечное число")
            continue

        if amount_rub <= 0:
            print("Сумма должна быть больше 0")
            continue
        if amount_rub.as_tuple().exponent < -2:
            print("После запятой не более двух цифр")
            continue

        amount_kop = int(amount_rub * 100)
        return amount_kop

def read_month(prompt):
    while True:
        date = input(prompt)
        try:
            parsed = datetime.strptime(date, '%Y-%m')
        except ValueError:
            print("Месяц введен некорректно")
            continue
        return parsed.strftime('%Y-%m')