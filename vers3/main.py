from transactions_add import addtransaction
from transaction_edit import edittransaction
from transactions_delete import deletetransaction
from history import show_history
from stats import stats
from categories_add import addcategory
from setbudget import setbudget
from view_budget import budgetview


def main():
    while True:
        print("\nТрекер расходов")
        print("1 — Добавить операцию")
        print("2 — История операций")
        print("3 — Изменить операцию")
        print("4 — Удалить операцию")
        print("5 — Статистика")
        print("6 — Добавить категорию")
        print("7 — Установить или изменить бюджет")
        print("8 — Посмотреть бюджеты")
        print("0 — Выход")

        choice = input("Выберите действие: ").strip()

        if choice == "1":
            addtransaction()

        elif choice == "2":
            show_history()

        elif choice == "3":
            edittransaction()

        elif choice == "4":
            deletetransaction()

        elif choice == "5":
            stats()

        elif choice == "6":
            addcategory()

        elif choice == "7":
            setbudget()

        elif choice == "8":
            budgetview()

        elif choice == "0":
            print("Программа завершена.")
            break

        else:
            print("Такого пункта нет.")


if __name__ == "__main__":
    main()