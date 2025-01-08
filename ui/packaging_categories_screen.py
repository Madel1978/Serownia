from typing import Optional, List, Dict, Any

from PyQt5.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QInputDialog,
    QMessageBox,
    QHBoxLayout,
    QWidget,
)
from PyQt5.QtCore import Qt

# Jeśli DBManager jest w innym miejscu, należy dostosować import:
# from database.db_manager import DBManager


class PackagingCategoriesScreen(QMainWindow):
    """
    Ekran zarządzania kategoriami opakowań. Wyświetla listę kategorii w tabeli
    i umożliwia dodawanie nowych kategorii za pomocą QInputDialog.
    """

    def __init__(
        self,
        parent: Optional[QMainWindow] = None,
        db_manager: Optional[Any] = None,  # docelowo: Optional[DBManager]
    ) -> None:
        """
        Inicjalizuje ekran "Kategorie Opakowań", zawierający tabelę
        z listą kategorii oraz przyciski (dodawanie, powrót).

        :param parent: Okno-rodzic, najczęściej MainWindow.
        :param db_manager: Obiekt zarządzający bazą danych.
        """
        super().__init__(parent)
        self.parent = parent
        self.db_manager = db_manager

        self.setWindowTitle("Kategorie Opakowań")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        # Tabela kategorii opakowań
        self.category_table = QTableWidget(0, 2)  # 2 kolumny: LP, Nazwa
        self.category_table.setHorizontalHeaderLabels(["LP", "Nazwa kategorii"])
        layout.addWidget(self.category_table)

        # Przyciski (dodawanie, powrót)
        button_layout = QHBoxLayout()

        add_button = QPushButton("Dodaj kategorię")
        add_button.setStyleSheet(
            """
            background-color: #ADD8E6;
            color: #000080;
            font-size: 14px;
            font-weight: bold;
            border-radius: 10px;
            padding: 10px;
        """
        )
        add_button.clicked.connect(self.add_category)
        button_layout.addWidget(add_button)

        back_button = QPushButton("Powrót")
        back_button.setStyleSheet(
            """
            background-color: #FFCCCC;
            color: #800000;
            font-size: 14px;
            font-weight: bold;
            border-radius: 10px;
            padding: 10px;
        """
        )
        # Możesz zastosować jednolite podejście _navigate_to_screen("settings_screen"),
        # jeśli masz taką metodę w parent
        back_button.clicked.connect(
            lambda: self.parent.show_screen(self.parent.settings_screen)
        )
        button_layout.addWidget(back_button)

        layout.addLayout(button_layout)
        self.setCentralWidget(central_widget)

        # Na starcie ładujemy kategorie z bazy
        self.load_categories()

    def load_categories(self) -> None:
        """
        Ładuje kategorie opakowań z bazy i wypełnia tabelę (self.category_table).
        """
        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można załadować kategorii."
            )
            return

        self.category_table.setRowCount(0)
        categories = (
            self.db_manager.get_packaging_categories()
        )  # Zakładamy istnienie tej metody w db_manager

        # Wypełniamy tabelę wierszami
        for i, cat in enumerate(categories):
            self.add_category_row(i + 1, cat)

    def add_category_row(self, lp: int, category: Dict[str, Any]) -> None:
        """
        Dodaje wiersz do tabeli.

        :param lp: Liczba porządkowa (LP).
        :param category: Słownik zawierający dane kategorii, np. {"id": int, "name": str}.
        """
        row = self.category_table.rowCount()
        self.category_table.insertRow(row)

        # Kol 0: LP (zablokowane do edycji)
        lp_item = QTableWidgetItem(str(lp))
        lp_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.category_table.setItem(row, 0, lp_item)

        # Kol 1: Nazwa kategorii (zablokowane do edycji)
        name_item = QTableWidgetItem(category["name"])
        name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.category_table.setItem(row, 1, name_item)

    def add_category(self) -> None:
        """
        Obsługa dodania nowej kategorii opakowań (wywołana po kliknięciu w przycisk).
        Wyświetla QInputDialog, pobiera nazwę i dodaje do bazy.
        """
        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można dodać kategorii."
            )
            return

        name, ok = QInputDialog.getText(
            self, "Dodaj kategorię", "Nazwa nowej kategorii:"
        )
        if ok and name.strip():
            name_str = name.strip()
            try:
                self.db_manager.add_packaging_category(name_str)
                QMessageBox.information(
                    self, "Sukces", f"Kategoria '{name_str}' została dodana."
                )
                self.load_categories()  # odświeżamy tabelę
            except Exception as e:
                QMessageBox.warning(self, "Błąd", f"Nie udało się dodać kategorii: {e}")
