from typing import Optional, Any, List

from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QInputDialog, QMessageBox, QHBoxLayout, QWidget
)
from PyQt5.QtCore import Qt


class AdditiveCategoriesScreen(QMainWindow):
    """
    Ekran zarządzania kategoriami dodatków. Wyświetla listę kategorii w tabeli
    i umożliwia dodawanie nowych kategorii (przycisk "Dodaj kategorię").
    """

    def __init__(
        self,
        parent: Optional[QMainWindow] = None,
        db_manager: Optional[Any] = None  # docelowo: Optional[DBManager]
    ) -> None:
        """
        Inicjalizuje ekran "Kategorie Dodatków", tworząc tabelę oraz przyciski
        (dodawanie kategorii, powrót).

        :param parent: Główne okno aplikacji (MainWindow).
        :param db_manager: Obiekt bazy danych (DBManager).
        """
        super().__init__(parent)
        self.setWindowTitle("Kategorie Dodatków")
        self.setGeometry(100, 100, 800, 600)

        self.parent = parent
        self.db_manager = db_manager

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        # Tabela kategorii dodatków
        self.category_table = QTableWidget(0, 2)
        self.category_table.setHorizontalHeaderLabels(["LP", "Nazwa kategorii"])
        layout.addWidget(self.category_table)

        # Przyciski (dodanie kategorii, powrót)
        button_layout = QHBoxLayout()
        add_button = QPushButton("Dodaj kategorię")
        add_button.setStyleSheet("""
            background-color: #ADD8E6;
            color: #000080;
            font-size: 14px;
            font-weight: bold;
            border-radius: 10px;
            padding: 10px;
        """)
        add_button.clicked.connect(self.add_category)
        button_layout.addWidget(add_button)

        back_button = QPushButton("Powrót")
        back_button.setStyleSheet("""
            background-color: #FFCCCC;
            color: #800000;
            font-size: 14px;
            font-weight: bold;
            border-radius: 10px;
            padding: 10px;
        """)
        # Jeśli w MainWindow masz metodę show_screen i obiekt settings_screen, możesz tak przejść:
        back_button.clicked.connect(lambda: self.parent.show_screen(self.parent.settings_screen))
        button_layout.addWidget(back_button)

        layout.addLayout(button_layout)
        self.setCentralWidget(central_widget)

        # Załaduj kategorie na starcie
        self.load_categories()

    def load_categories(self) -> None:
        """
        Ładuje kategorie dodatków z bazy (db_manager.get_categories()) i wyświetla
        w tabeli. Usuwa istniejące wiersze, a następnie dodaje od nowa.
        """
        if not self.db_manager:
            QMessageBox.critical(self, "Błąd", "Brak db_manager – nie można załadować kategorii.")
            return

        self.category_table.setRowCount(0)
        categories = self.db_manager.get_categories()  # lista słowników, np. [{"id": ..., "name": ...}, ...]

        for i, category in enumerate(categories):
            self.add_category_row(i + 1, category)

    def add_category_row(self, lp: int, category: dict) -> None:
        """
        Dodaje wiersz do tabeli, ustawiając:
          - LP (liczbę porządkową),
          - Nazwę kategorii (zablokowaną do edycji).

        :param lp: Liczba porządkowa (1, 2, 3, ...).
        :param category: Słownik zawierający co najmniej klucz "name".
        """
        row = self.category_table.rowCount()
        self.category_table.insertRow(row)

        # Kolumna 0: LP (nieedytowalne)
        lp_item = QTableWidgetItem(str(lp))
        lp_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.category_table.setItem(row, 0, lp_item)

        # Kolumna 1: Nazwa kategorii (nieedytowalne)
        name_item = QTableWidgetItem(category.get("name", ""))
        name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.category_table.setItem(row, 1, name_item)

    def add_category(self) -> None:
        """
        Otwiera QInputDialog w celu wprowadzenia nazwy nowej kategorii,
        a następnie wywołuje db_manager.add_category(...).
        Po sukcesie odświeża tabelę.
        """
        if not self.db_manager:
            QMessageBox.critical(self, "Błąd", "Brak db_manager – nie można dodać kategorii.")
            return

        name, ok = QInputDialog.getText(self, "Dodaj kategorię", "Nazwa nowej kategorii:")
        if ok and name.strip():
            try:
                self.db_manager.add_category(name.strip())
                QMessageBox.information(
                    self, "Sukces",
                    f"Kategoria '{name.strip()}' została dodana."
                )
                self.load_categories()
            except Exception as e:
                QMessageBox.warning(self, "Błąd", f"Nie udało się dodać kategorii: {e}")
