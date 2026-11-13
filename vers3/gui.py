import argparse
from contextlib import closing
from datetime import date
from pathlib import Path
import re
import sqlite3
import sys

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QDateEdit, QDialog,
    QDialogButtonBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QSizePolicy, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)


KINDS = {"income": "Доход", "expense": "Расход"}
POSITIVE = "#087b63"
NEGATIVE = "#a13b50"
ALIGN_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
MAX_SQLITE_INT = 2**63 - 1


def money(kopeks):
    rubles, cents = divmod(abs(kopeks), 100)
    sign = "−" if kopeks < 0 else ""
    return f"{sign}{rubles:,}".replace(",", " ") + f",{cents:02d} ₽"


def amount_text(kopeks):
    rubles, cents = divmod(kopeks, 100)
    return f"{rubles},{cents:02d}"


def parse_amount(text):
    text = text.strip()
    match = re.fullmatch(r"([0-9]{1,17})(?:[.,]([0-9]{1,2}))?", text)
    if match is None:
        raise ValueError("Введите сумму в рублях, например 350 или 350,50.")
    rubles, fraction = match.groups()
    kopeks = int(rubles) * 100 + int((fraction or "").ljust(2, "0"))
    if not 0 < kopeks <= MAX_SQLITE_INT:
        raise ValueError("Сумма должна быть положительной и помещаться в базе.")
    return kopeks


class Store:

    def __init__(self, path):
        self.path = Path(path).expanduser().resolve()
        self.uri = self.path.as_uri() + "?mode=rw"
        self.read("SELECT id, name, kind FROM categories LIMIT 0")
        self.read("SELECT id, category_id, amount_kopeks, date, comment FROM transactions LIMIT 0")
        self.read("SELECT id, category_id, month, limit_kopeks FROM budgets LIMIT 0")

    def connect(self):
        connection = sqlite3.connect(self.uri, uri=True, timeout=2)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def read(self, sql, params=()):
        with closing(self.connect()) as connection:
            return connection.execute(sql, params).fetchall()

    def write(self, sql, params=()):
        with closing(self.connect()) as connection, connection:
            return connection.execute(sql, params).rowcount

    def categories(self, kind=None):
        return self.read(
            "SELECT id, name, kind FROM categories WHERE (? IS NULL OR kind = ?) ORDER BY name, id",
            (kind, kind),
        )

    def history(self, start, end, kind=None, category_id=None):
        return self.read("""
            SELECT t.id, t.date, t.category_id, c.name, c.kind, t.amount_kopeks, t.comment
            FROM transactions AS t JOIN categories AS c ON c.id = t.category_id
            WHERE (? IS NULL OR t.date BETWEEN ? AND ?)
              AND (? IS NULL OR c.kind = ?)
              AND (? IS NULL OR t.category_id = ?)
            ORDER BY t.date DESC, t.id DESC
        """, (start, start, end, kind, kind, category_id, category_id))

    def save_transaction(self, category_id, kopeks, day, comment, transaction_id=None):
        values = (category_id, kopeks, day, comment)
        if transaction_id is None:
            self.write("""
                INSERT INTO transactions (category_id, amount_kopeks, date, comment)
                VALUES (?, ?, ?, ?)
            """, values)
        elif not self.write("""
            UPDATE transactions SET category_id = ?, amount_kopeks = ?, date = ?, comment = ?
            WHERE id = ?
        """, (*values, transaction_id)):
            raise ValueError("Эта операция уже удалена. Обновите историю.")

    def delete_transaction(self, transaction_id):
        return self.write("DELETE FROM transactions WHERE id = ?", (transaction_id,))

    def add_category(self, name, kind):
        self.write("INSERT INTO categories (name, kind) VALUES (?, ?)", (name, kind))

    def statistics(self, start, end):
        return self.read("""
            SELECT c.name, c.kind, SUM(t.amount_kopeks) AS total
            FROM transactions AS t JOIN categories AS c ON c.id = t.category_id
            WHERE (? IS NULL OR t.date BETWEEN ? AND ?)
            GROUP BY c.id, c.name, c.kind
            ORDER BY total DESC, c.name
        """, (start, start, end))

    def budget_months(self):
        return self.read("SELECT DISTINCT month FROM budgets ORDER BY month DESC")

    def budgets(self, month):
        return self.read("""
            SELECT b.category_id, c.name, b.limit_kopeks,
                   COALESCE(SUM(t.amount_kopeks), 0) AS spent
            FROM budgets AS b JOIN categories AS c ON c.id = b.category_id
            LEFT JOIN transactions AS t ON t.category_id = b.category_id
                AND strftime('%Y-%m', t.date) = b.month
            WHERE b.month = ? AND c.kind = 'expense'
            GROUP BY b.id, b.category_id, c.name, b.limit_kopeks
            ORDER BY c.name
        """, (month,))

    def budget_limit(self, category_id, month):
        rows = self.read(
            "SELECT limit_kopeks FROM budgets WHERE category_id = ? AND month = ?",
            (category_id, month),
        )
        return rows[0]["limit_kopeks"] if rows else None

    def save_budget(self, category_id, month, kopeks):
        if not self.write("""
            INSERT INTO budgets (category_id, month, limit_kopeks)
            SELECT id, ?, ? FROM categories WHERE id = ? AND kind = 'expense'
            ON CONFLICT (category_id, month) DO UPDATE SET limit_kopeks = excluded.limit_kopeks
        """, (month, kopeks, category_id)):
            raise ValueError("Выберите действующую категорию расходов.")


STYLE = """
QMainWindow, QDialog { background: #f5f7fb; }
QWidget { color: #18253c; font-size: 14px; }
QFrame#hero { background: #182740; border-radius: 13px; }
QLabel#brand { color: #ffffff; font-size: 26px; font-weight: 700; }
QLabel#tagline { color: #c7d4e8; font-size: 13px; }
QLabel#heroTag { color: #c6fae8; background: #25495a; padding: 5px 10px;
                border-radius: 8px; font-weight: 600; }
QLabel#section { font-size: 23px; font-weight: 700; }
QLabel#subsection { font-size: 17px; font-weight: 700; }
QLabel#muted { color: #53617a; font-size: 13px; }
QLabel#error { color: #a13b50; font-size: 13px; }
QFrame#metric { background: #ffffff; border: 1px solid #dce4ef; border-radius: 10px; }
QLabel#metricValue { font-size: 25px; font-weight: 700; }
QTabWidget::pane { border: 1px solid #dce4ef; border-radius: 10px; background: #ffffff; }
QTabBar::tab { background: #eaf0f7; color: #415371; border: 1px solid #dce4ef;
              padding: 9px 17px; margin-right: 5px; border-top-left-radius: 8px;
              border-top-right-radius: 8px; }
QTabBar::tab:selected { background: #ffffff; color: #0a6659; font-weight: 700;
                      border-bottom-color: #ffffff; }
QPushButton { background: #ffffff; color: #243955; border: 1px solid #cad6e5;
              border-radius: 7px; padding: 6px 12px; min-height: 20px; }
QPushButton:hover { background: #edf4fb; }
QPushButton:focus, QComboBox:focus, QDateEdit:focus, QLineEdit:focus { border-color: #157969; }
QPushButton#primary { background: #116c5c; color: #ffffff; border-color: #116c5c;
                      font-weight: 650; }
QPushButton#primary:hover { background: #0b574a; }
QPushButton#danger { color: #a13b50; }
QPushButton:disabled { background: #f0f3f7; color: #657188; border-color: #e0e6ef; }
QComboBox, QDateEdit, QLineEdit { background: #ffffff; border: 1px solid #cbd7e6;
                                border-radius: 6px; min-height: 22px; padding: 4px 7px; }
QComboBox { padding-right: 20px; }
QDateEdit { min-width: 103px; }
QComboBox:disabled, QDateEdit:disabled { background: #f0f3f7; color: #627089; }
QComboBox QAbstractItemView { background: #ffffff; color: #18253c;
                             selection-background-color: #d5f1e9; selection-color: #153e39; }
QTableWidget { background: #ffffff; alternate-background-color: #f5f8fc;
               border: 1px solid #dce4ef; border-radius: 7px;
               selection-background-color: #d5f1e9; selection-color: #153e39; }
QTableWidget::item { padding: 5px 9px; }
QHeaderView::section { background: #eaf0f7; color: #354968; border: 0;
                       border-bottom: 1px solid #dce4ef; padding: 9px 9px; font-weight: 650; }
QStatusBar { background: #f5f7fb; color: #53617a; }
"""


def label(text="", role=None):
    widget = QLabel(text)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    if role:
        widget.setObjectName(role)
    return widget


def button(text, action, role=None):
    widget = QPushButton(text)
    if role:
        widget.setObjectName(role)
    widget.clicked.connect(action)
    return widget


def date_field(day, month_only=False):
    field = QDateEdit(day)
    field.setDateRange(QDate(1, 1, 1), QDate(9999, 12, 31))
    field.setDisplayFormat("yyyy-MM" if month_only else "dd.MM.yyyy")
    field.setCalendarPopup(not month_only)
    return field


def month_key(field):
    day = field.date()
    return f"{day.year():04d}-{day.month():02d}"


def parse_month(text):
    try:
        year, month = map(int, text.split("-"))
        return QDate(year, month, 1)
    except (ValueError, TypeError):
        return QDate()


def display_date(text):
    try:
        return date.fromisoformat(text).strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return text


def table(headers, stretch=(), right=()):
    widget = QTableWidget(0, len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    widget.setAlternatingRowColors(True)
    widget.setShowGrid(False)
    widget.verticalHeader().hide()
    widget.verticalHeader().setDefaultSectionSize(34)
    for index in range(len(headers)):
        widget.horizontalHeader().setSectionResizeMode(
            index, QHeaderView.ResizeMode.Stretch if index in stretch else
            QHeaderView.ResizeMode.ResizeToContents
        )
        if index in right:
            widget.horizontalHeaderItem(index).setTextAlignment(ALIGN_RIGHT)
    return widget


def fill_table(widget, rows, right=(), colors=None):
    widget.clearSelection()
    widget.clearContents()
    widget.setRowCount(len(rows))
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            value = str(value)
            item = QTableWidgetItem(value)
            item.setToolTip(value)
            if j in right:
                item.setTextAlignment(ALIGN_RIGHT)
            if colors and (color := colors(i, j)):
                item.setForeground(QColor(color))
            widget.setItem(i, j, item)


class Period(QWidget):

    def __init__(self):
        super().__init__()
        today = QDate.currentDate()
        self.mode = QComboBox()
        self.mode.addItem("Всё время", "all")
        self.mode.addItem("Текущий месяц", "month")
        self.mode.addItem("Свой период", "custom")
        self.start = date_field(QDate(today.year(), today.month(), 1))
        self.end = date_field(today)
        self.start.setAccessibleName("Начало периода")
        self.end.setAccessibleName("Конец периода")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label("Период"))
        layout.addWidget(self.mode)
        layout.addWidget(label("с"))
        layout.addWidget(self.start)
        layout.addWidget(label("по"))
        layout.addWidget(self.end)
        layout.addStretch()
        self.mode.currentIndexChanged.connect(self.toggle_dates)
        self.toggle_dates()

    def toggle_dates(self):
        custom = self.mode.currentData() == "custom"
        self.start.setEnabled(custom)
        self.end.setEnabled(custom)

    def bounds(self):
        mode = self.mode.currentData()
        if mode == "all":
            return None, None
        if mode == "month":
            today = QDate.currentDate()
            start = QDate(today.year(), today.month(), 1)
            end = QDate(today.year(), today.month(), today.daysInMonth())
        else:
            start, end = self.start.date(), self.end.date()
        if start > end:
            raise ValueError("Конечная дата не может быть раньше начальной.")
        return start.toString("yyyy-MM-dd"), end.toString("yyyy-MM-dd")


class FormDialog(QDialog):
    def __init__(self, title, parent):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(450)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 18)
        layout.setSpacing(13)
        layout.addWidget(label(title, "section"))
        self.form = QFormLayout()
        self.form.setSpacing(10)
        self.form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        layout.addLayout(self.form)
        self.error = label("", "error")
        self.error.setWordWrap(True)
        self.error.hide()
        layout.addWidget(self.error)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Сохранить")
        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("primary")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def show_error(self, message):
        self.error.setText(str(message))
        self.error.show()


class TransactionDialog(FormDialog):
    def __init__(self, store, categories, parent, row=None):
        super().__init__("Новая операция" if row is None else "Редактирование операции", parent)
        self.store, self.row = store, row
        self.category = QComboBox()
        for category in categories:
            self.category.addItem(
                f"{category['name']} · {KINDS[category['kind']].lower()}", category["id"]
            )
        self.amount = QLineEdit()
        self.amount.setPlaceholderText("Например, 350,50")
        self.amount.setMaxLength(23)
        self.day = date_field(QDate.currentDate())
        self.comment = QLineEdit()
        self.comment.setPlaceholderText("Необязательно")
        self.form.addRow("Категория", self.category)
        self.form.addRow("Сумма, ₽", self.amount)
        self.form.addRow("Дата", self.day)
        self.form.addRow("Комментарий", self.comment)
        if row is not None:
            self.category.setCurrentIndex(self.category.findData(row["category_id"]))
            self.amount.setText(amount_text(row["amount_kopeks"]))
            saved_date = QDate.fromString(row["date"], "yyyy-MM-dd")
            if saved_date.isValid():
                self.day.setDate(saved_date)
            else:
                self.show_error(f"Сохранённая дата некорректна: {row['date']}. Укажите верную дату.")
            self.comment.setText(row["comment"] or "")
        self.amount.setFocus()

    def save(self):
        try:
            self.store.save_transaction(
                self.category.currentData(), parse_amount(self.amount.text()),
                self.day.date().toString("yyyy-MM-dd"), self.comment.text().strip(),
                self.row["id"] if self.row is not None else None,
            )
        except (ValueError, sqlite3.Error) as error:
            self.show_error(error)
            return
        self.accept()


class CategoryDialog(FormDialog):
    def __init__(self, store, parent):
        super().__init__("Новая категория", parent)
        self.store = store
        self.name = QLineEdit()
        self.name.setPlaceholderText("Например, Транспорт")
        self.kind = QComboBox()
        self.kind.addItem("Расход", "expense")
        self.kind.addItem("Доход", "income")
        self.form.addRow("Название", self.name)
        self.form.addRow("Тип", self.kind)
        self.name.setFocus()

    def save(self):
        name = self.name.text().strip()
        if not name:
            self.show_error("Введите название категории.")
            return
        try:
            self.store.add_category(name, self.kind.currentData())
        except sqlite3.IntegrityError:
            self.show_error("Категория с таким названием уже существует.")
            return
        except sqlite3.Error as error:
            self.show_error(error)
            return
        self.accept()


class BudgetDialog(FormDialog):
    def __init__(self, store, categories, month, parent, category_id=None):
        super().__init__("Лимит категории", parent)
        self.store = store
        self.category = QComboBox()
        for row in categories:
            self.category.addItem(row["name"], row["id"])
        if category_id is not None:
            index = self.category.findData(category_id)
            if index >= 0:
                self.category.setCurrentIndex(index)
        self.month = date_field(parse_month(month), month_only=True)
        self.amount = QLineEdit()
        self.amount.setPlaceholderText("Например, 15000")
        self.amount.setMaxLength(23)
        self.previous = label("", "muted")
        self.form.addRow("Категория", self.category)
        self.form.addRow("Месяц", self.month)
        self.form.addRow("Лимит, ₽", self.amount)
        self.form.addRow("", self.previous)
        self.category.currentIndexChanged.connect(self.load_limit)
        self.month.dateChanged.connect(self.load_limit)
        self.load_limit()
        self.amount.setFocus()

    def load_limit(self):
        try:
            previous = self.store.budget_limit(self.category.currentData(), month_key(self.month))
        except sqlite3.Error as error:
            self.show_error(error)
            return
        self.error.hide()
        self.previous.setText(
            "Текущий лимит: " + money(previous) if previous is not None
            else "Для этой категории и месяца лимит ещё не задан."
        )
        self.amount.setText(amount_text(previous) if previous is not None else "")

    def save(self):
        try:
            self.store.save_budget(
                self.category.currentData(), month_key(self.month), parse_amount(self.amount.text())
            )
        except (ValueError, sqlite3.Error) as error:
            self.show_error(error)
            return
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self, store):
        super().__init__()
        self.store = store
        self.setWindowTitle("YourBalance — учёт личных финансов")
        self.resize(1070, 720)
        self.setMinimumSize(780, 600)

        shell = QWidget()
        root = QVBoxLayout(shell)
        root.setContentsMargins(20, 18, 20, 10)
        root.setSpacing(16)
        self.setCentralWidget(shell)

        hero = QFrame()
        hero.setObjectName("hero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(20, 13, 20, 13)
        identity = QVBoxLayout()
        identity.setSpacing(3)
        identity.addWidget(label("YourBalance", "brand"))
        identity.addWidget(label("Учёт личных финансов", "tagline"))
        hero_layout.addLayout(identity)
        hero_layout.addStretch()
        hero_layout.addWidget(label("₽  Рубли", "heroTag"))
        root.addWidget(hero)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        root.addWidget(self.tabs, 1)
        self.make_history_page()
        self.make_statistics_page()
        self.make_budgets_page()
        self.make_categories_page()
        self.statusBar().setSizeGripEnabled(False)
        database_label = label(f"База: {self.store.path.name}", "muted")
        database_label.setToolTip(str(self.store.path))
        self.statusBar().addPermanentWidget(database_label, 0)
        self.refresh_all()

    def new_page(self, tab_name, title, subtitle):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 15, 18, 16)
        layout.setSpacing(12)
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        title_box.addWidget(label(title, "section"))
        title_box.addWidget(label(subtitle, "muted"))
        header.addLayout(title_box)
        header.addStretch()
        layout.addLayout(header)
        self.tabs.addTab(page, tab_name)
        return layout, header

    def make_history_page(self):
        layout, header = self.new_page(
            "Операции", "История операций", "Доходы и расходы с фильтрами по периоду, типу и категории."
        )
        header.addWidget(button("+ Добавить операцию", self.add_transaction, "primary"))
        self.history_period = Period()
        layout.addWidget(self.history_period)
        toolbar = QHBoxLayout()
        self.history_kind = QComboBox()
        self.history_kind.addItem("Все операции", None)
        self.history_kind.addItem("Расходы", "expense")
        self.history_kind.addItem("Доходы", "income")
        self.history_category = QComboBox()
        self.history_category.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.history_category.setMinimumContentsLength(15)
        self.history_kind.setAccessibleName("Тип операций")
        self.history_category.setAccessibleName("Категория")
        toolbar.addWidget(self.history_kind)
        toolbar.addWidget(self.history_category)
        toolbar.addWidget(button("Показать", lambda: self.safe(self.refresh_history)))
        toolbar.addStretch()
        self.edit_button = button("Изменить", self.edit_transaction)
        self.delete_button = button("Удалить", self.delete_transaction, "danger")
        toolbar.addWidget(self.edit_button)
        toolbar.addWidget(self.delete_button)
        layout.addLayout(toolbar)
        self.history_table = table(
            ("№", "Дата", "Категория", "Тип", "Сумма", "Комментарий"),
            stretch=(2, 5), right=(4,),
        )
        self.history_table.itemSelectionChanged.connect(self.update_history_actions)
        self.history_table.cellDoubleClicked.connect(lambda _row, _column: self.edit_transaction())
        layout.addWidget(self.history_table, 1)
        self.history_hint = label("", "muted")
        layout.addWidget(self.history_hint)

    def make_statistics_page(self):
        layout, _ = self.new_page(
            "Статистика", "Сводка за период", "Сколько поступило, сколько ушло и на что."
        )
        filters = QHBoxLayout()
        self.stats_period = Period()
        filters.addWidget(self.stats_period, 1)
        filters.addWidget(button("Рассчитать", lambda: self.safe(self.refresh_statistics), "primary"))
        layout.addLayout(filters)
        metrics = QHBoxLayout()
        self.metric_values = {}
        for key, title in (("income", "Доходы"), ("expense", "Расходы"), ("balance", "Разница")):
            card = QFrame()
            card.setObjectName("metric")
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(13, 10, 13, 10)
            card_layout.addWidget(label(title, "muted"))
            value = label(money(0), "metricValue")
            card_layout.addWidget(value)
            self.metric_values[key] = value
            metrics.addWidget(card)
        layout.addLayout(metrics)
        layout.addWidget(label("Расходы по категориям", "subsection"))
        self.stats_table = table(("Категория", "Потрачено", "Доля расходов"), stretch=(0,), right=(1, 2))
        layout.addWidget(self.stats_table, 1)
        self.stats_hint = label("", "muted")
        layout.addWidget(self.stats_hint)

    def make_budgets_page(self):
        layout, header = self.new_page(
            "Бюджеты", "Месячные бюджеты", "Лимиты по категориям, фактические расходы и остатки."
        )
        header.addWidget(button("Установить лимит", self.edit_budget, "primary"))
        filters = QHBoxLayout()
        self.budget_month = date_field(QDate.currentDate(), month_only=True)
        self.budget_month.setAccessibleName("Месяц бюджета")
        months = self.store.budget_months()
        if months and not any(row["month"] == month_key(self.budget_month) for row in months):
            recent = parse_month(months[0]["month"])
            if recent.isValid():
                self.budget_month.setDate(recent)
        filters.addWidget(label("Месяц"))
        filters.addWidget(self.budget_month)
        filters.addWidget(button("Показать", lambda: self.safe(self.refresh_budgets)))
        filters.addStretch()
        layout.addLayout(filters)
        self.budget_table = table(
            ("Категория", "Лимит", "Потрачено", "Остаток", "Состояние"),
            stretch=(0, 4), right=(1, 2, 3),
        )
        self.budget_table.cellDoubleClicked.connect(lambda _row, _column: self.edit_budget())
        layout.addWidget(self.budget_table, 1)
        self.budget_hint = label("", "muted")
        layout.addWidget(self.budget_hint)

    def make_categories_page(self):
        layout, header = self.new_page(
            "Категории", "Категории", "Категория определяет, будет операция доходом или расходом."
        )
        header.addWidget(button("+ Новая категория", self.add_category, "primary"))
        self.category_table = table(("№", "Название", "Тип"), stretch=(1, 2))
        layout.addWidget(self.category_table, 1)
        self.category_hint = label("", "muted")
        layout.addWidget(self.category_hint)

    def safe(self, action):
        try:
            return action()
        except (ValueError, sqlite3.Error) as error:
            QMessageBox.warning(self, "YourBalance", str(error))
            return None

    def refresh_all(self):
        self.refresh_categories()
        self.refresh_history()
        self.refresh_statistics()
        self.refresh_budgets()

    def refresh_categories(self):
        categories = self.store.categories()
        previous = self.history_category.currentData()
        self.history_category.clear()
        self.history_category.addItem("Все категории", None)
        for row in categories:
            self.history_category.addItem(row["name"], row["id"])
        index = self.history_category.findData(previous)
        self.history_category.setCurrentIndex(max(0, index))
        fill_table(self.category_table, [
            (row["id"], row["name"], KINDS[row["kind"]]) for row in categories
        ])
        self.category_hint.setText(f"Категорий: {len(categories)}")

    def refresh_history(self):
        self.history_rows = self.store.history(
            *self.history_period.bounds(),
            self.history_kind.currentData(), self.history_category.currentData(),
        )
        fill_table(self.history_table, [
            (row["id"], display_date(row["date"]), row["name"], KINDS[row["kind"]],
             ("+" if row["kind"] == "income" else "−") + money(row["amount_kopeks"]),
             row["comment"] or "—")
            for row in self.history_rows
        ], right=(4,), colors=lambda i, j: (
            POSITIVE if self.history_rows[i]["kind"] == "income" else NEGATIVE
        ) if j == 4 else None)
        self.history_hint.setText(
            f"Найдено операций: {len(self.history_rows)}  ·  Двойной щелчок — изменить"
            if self.history_rows else "По этим фильтрам операций нет."
        )
        self.update_history_actions()

    def update_history_actions(self):
        has_selection = bool(self.history_table.selectedItems())
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def refresh_statistics(self):
        rows = self.store.statistics(*self.stats_period.bounds())
        income = sum(row["total"] for row in rows if row["kind"] == "income")
        expenses = [row for row in rows if row["kind"] == "expense"]
        expense = sum(row["total"] for row in expenses)
        for key, total, color in (
            ("income", income, POSITIVE), ("expense", expense, NEGATIVE),
            ("balance", income - expense, POSITIVE if income >= expense else NEGATIVE),
        ):
            self.metric_values[key].setText(money(total))
            self.metric_values[key].setStyleSheet(f"color: {color};")
        fill_table(self.stats_table, [
            (row["name"], money(row["total"]), f"{row['total'] / expense:.1%}".replace(".", ","))
            for row in expenses
        ], right=(1, 2))
        self.stats_hint.setText("Доли рассчитаны от общей суммы расходов." if expenses
                                else "В выбранном периоде нет расходов.")

    def refresh_budgets(self):
        self.budget_rows = self.store.budgets(month_key(self.budget_month))
        remaining = [row["limit_kopeks"] - row["spent"] for row in self.budget_rows]
        fill_table(self.budget_table, [
            (row["name"], money(row["limit_kopeks"]), money(row["spent"]), money(left),
             "Лимит превышен" if left < 0 else "Лимит исчерпан" if left == 0 else "В пределах лимита")
            for row, left in zip(self.budget_rows, remaining)
        ], right=(1, 2, 3), colors=lambda i, j: (
            NEGATIVE if remaining[i] < 0 else POSITIVE
        ) if j in (3, 4) else None)
        self.budget_hint.setText(
            f"Бюджетов: {len(self.budget_rows)}  ·  Двойной щелчок — изменить лимит"
            if self.budget_rows else "На выбранный месяц бюджеты не установлены."
        )

    def open_transaction(self, row=None):
        categories = self.safe(self.store.categories)
        if categories is None:
            return
        if not categories:
            QMessageBox.information(self, "Нужна категория", "Сначала добавьте категорию.")
            self.tabs.setCurrentIndex(3)
            return
        dialog = TransactionDialog(self.store, categories, self, row)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.safe(self.refresh_all)

    def add_transaction(self):
        self.open_transaction()

    def selected_transaction(self):
        selection = self.history_table.selectionModel().selectedRows()
        return self.history_rows[selection[0].row()] if selection else None

    def edit_transaction(self):
        row = self.selected_transaction()
        if row is not None:
            self.open_transaction(row)

    def delete_transaction(self):
        row = self.selected_transaction()
        if row is None:
            return
        box = QMessageBox(QMessageBox.Icon.Warning, "Удалить операцию?",
                          f"№{row['id']} · {row['name']} · {money(row['amount_kopeks'])}", parent=self)
        box.setTextFormat(Qt.TextFormat.PlainText)
        remove = box.addButton("Удалить", QMessageBox.ButtonRole.DestructiveRole)
        cancel = box.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(cancel)
        box.setEscapeButton(cancel)
        box.exec()
        if box.clickedButton() == remove:
            deleted = self.safe(lambda: self.store.delete_transaction(row["id"]))
            if deleted is not None:
                self.safe(self.refresh_all)
                self.statusBar().showMessage("Операция удалена." if deleted
                                             else "Операция уже была удалена.", 4000)

    def add_category(self):
        if CategoryDialog(self.store, self).exec() == QDialog.DialogCode.Accepted:
            self.safe(self.refresh_all)

    def edit_budget(self):
        categories = self.safe(lambda: self.store.categories("expense"))
        if categories is None:
            return
        if not categories:
            QMessageBox.information(self, "Нужна категория", "Сначала добавьте категорию расходов.")
            self.tabs.setCurrentIndex(3)
            return
        selection = self.budget_table.selectionModel().selectedRows()
        category_id = self.budget_rows[selection[0].row()]["category_id"] if selection else None
        dialog = BudgetDialog(self.store, categories, month_key(self.budget_month), self, category_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.budget_month.setDate(dialog.month.date())
            self.safe(self.refresh_budgets)


def make_application():
    app = QApplication([sys.argv[0]])
    app.setApplicationName("YourBalance")
    app.setStyle("Fusion")
    palette = QPalette()
    for role, color in (
        (QPalette.ColorRole.Window, "#f5f7fb"),
        (QPalette.ColorRole.WindowText, "#18253c"),
        (QPalette.ColorRole.Base, "#ffffff"),
        (QPalette.ColorRole.AlternateBase, "#f5f8fc"),
        (QPalette.ColorRole.Text, "#18253c"),
        (QPalette.ColorRole.Button, "#ffffff"),
        (QPalette.ColorRole.ButtonText, "#18253c"),
        (QPalette.ColorRole.Highlight, "#d5f1e9"),
        (QPalette.ColorRole.HighlightedText, "#153e39"),
        (QPalette.ColorRole.ToolTipBase, "#ffffff"),
        (QPalette.ColorRole.ToolTipText, "#18253c"),
    ):
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    app.setStyleSheet(STYLE)
    return app


def main():
    parser = argparse.ArgumentParser(description="YourBalance — интерфейс Qt для существующей базы.")
    parser.add_argument("--db", type=Path, help="Путь к базе expenses.db")
    args = parser.parse_args()
    app = make_application()
    database = args.db
    if database is None:
        nearby = Path(__file__).resolve().with_name("expenses.db")
        if nearby.is_file():
            database = nearby
        else:
            selected, _ = QFileDialog.getOpenFileName(
                None, "Выберите существующую базу YourBalance", str(Path.home()),
                "Базы SQLite (*.db *.sqlite *.sqlite3);;Все файлы (*)",
            )
            if not selected:
                return 0
            database = Path(selected)

    try:
        window = MainWindow(Store(database))
    except (ValueError, sqlite3.Error) as error:
        QMessageBox.critical(
            None, "Не удалось открыть базу",
            f"Выберите существующий файл expenses.db с таблицами проекта YourBalance.\n\n{error}"
        )
        return 1
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
