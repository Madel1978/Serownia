from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QInputDialog, QMessageBox, QHBoxLayout, QWidget
)
from PyQt5.QtCore import Qt


class ProductCategoriesScreen(QMainWindow):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.setWindowTitle("Kategorie Produktów")
        self.setGeometry(100, 100, 800, 600)
        self.parent = parent
        self.db_manager = db_manager

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        # Tabela kategorii produktów
        self.category_table = QTableWidget(0, 2)
        self.category_table.setHorizontalHeaderLabels(["LP", "Nazwa kategorii"])
        layout.addWidget(self.category_table)

        # Przyciski
        button_layout = QHBoxLayout()

        # Przycisk: Dodaj kategorię
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

        # Przycisk: Usuń kategorię (opcjonalny)
        remove_button = QPushButton("Usuń kategorię")
        remove_button.setStyleSheet("""
            background-color: #FFDAB9;
            color: #8B4513;
            font-size: 14px;
            font-weight: bold;
            border-radius: 10px;
            padding: 10px;
        """)
        remove_button.clicked.connect(self.remove_selected_category)
        button_layout.addWidget(remove_button)

        # Przycisk Powrót
        back_button = QPushButton("Powrót")
        back_button.setStyleSheet("""
            background-color: #FFCCCC;
            color: #800000;
            font-size: 14px;
            font-weight: bold;
            border-radius: 10px;
            padding: 10px;
        """)
        back_button.clicked.connect(lambda: self.parent.show_screen(self.parent.settings_screen))
        button_layout.addWidget(back_button)

        layout.addLayout(button_layout)
        self.setCentralWidget(central_widget)

        # Załaduj kategorie na starcie
        self.load_categories()

    def load_categories(self):
        """Ładuje kategorie produktów z bazy danych."""
        self.category_table.setRowCount(0)
        try:
            categories = self.db_manager.get_product_categories()
            for i, category in enumerate(categories):
                self.add_category_row(i + 1, category)
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się wczytać kategorii: {e}")

    def add_category_row(self, lp, category):
        """Dodaje wiersz do tabeli."""
        row = self.category_table.rowCount()
        self.category_table.insertRow(row)

        lp_item = QTableWidgetItem(str(lp))
        lp_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # Nieedytowalne
        self.category_table.setItem(row, 0, lp_item)

        name_item = QTableWidgetItem(category["name"])
        name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # Nieedytowalne
        self.category_table.setItem(row, 1, name_item)

    def add_category(self):
        """Dodaje nową kategorię."""
        name, ok = QInputDialog.getText(self, "Dodaj kategorię", "Nazwa nowej kategorii:")
        if ok and name.strip():
            try:
                self.db_manager.add_product_category(name.strip())
                QMessageBox.information(self, "Sukces", f"Kategoria '{name.strip()}' została dodana.")
                self.load_categories()
            except Exception as e:
                QMessageBox.warning(self, "Błąd", f"Nie udało się dodać kategorii: {e}")

    def remove_selected_category(self):
        """
        Usuwa zaznaczoną kategorię z bazy danych.
        (Opcjonalna funkcja, jeśli potrzebujesz takiej akcji.)
        """
        selected_row = self.category_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Błąd", "Wybierz kategorię do usunięcia.")
            return

        category_name = self.category_table.item(selected_row, 1).text()  # nazwa kategorii w kolumnie 1
        confirm = QMessageBox.question(
            self,
            "Potwierdzenie",
            f"Czy na pewno chcesz usunąć kategorię '{category_name}'?"
        )
        if confirm == QMessageBox.Yes:
            try:
                self.db_manager.delete_product_category(category_name)
                QMessageBox.information(
                    self,
                    "Sukces",
                    f"Kategoria '{category_name}' została usunięta."
                )
                self.load_categories()
            except Exception as e:
                QMessageBox.warning(self, "Błąd", f"Nie udało się usunąć kategorii: {e}")
