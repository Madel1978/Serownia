# c:\serownia\ui\base_crud_list_screen.py

from typing import Optional, List, Any

from PyQt5.QtWidgets import (
    QPushButton,
    QTableWidgetItem,
    QMessageBox,
    QWidget,
    QLineEdit,
    QComboBox,
    QVBoxLayout,
)
from PyQt5.QtCore import Qt

from .base_list_screen import BaseListScreen


class BaseCrudListScreen(BaseListScreen):
    """
    Rozszerza BaseListScreen o uniwersalne kolumny 'Edytuj/Zapisz' i 'Usuń',
    a także dodaje przycisk 'Powrót' na dole layoutu.

    Dodatkowo zapewniamy self.main_layout, aby klasy potomne
    mogły np. wstawić pole wyszukiwania (search_lineedit).
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        title: str = "Lista",
        columns: Optional[List[str]] = None,
    ) -> None:
        """
        Inicjalizuje ekran z listą (CRUD). Dodaje też przycisk 'Powrót' na dole.
        """
        super().__init__(parent, title=title, columns=columns)

        # Upewniamy się, że pobieramy layout z centralWidget
        # i zapisujemy go w self.main_layout, aby klasy potomne
        # mogły np. insertLayout(0, top_hbox).
        self.main_layout = None
        central_widget = self.centralWidget()
        if central_widget is not None:
            layout = central_widget.layout()
            if layout is not None:
                # Przypisujemy layout do self.main_layout,
                # dzięki czemu np. ProductsListScreen może go używać.
                self.main_layout = layout

        # Dodajemy przycisk "Powrót" na dole
        self.add_back_button()

    def add_back_button(self) -> None:
        """
        Tworzy i dodaje przycisk 'Powrót' na dole layoutu (poniżej tabeli).
        """
        from PyQt5.QtWidgets import QPushButton

        # Używamy self.main_layout (lub fallback do centralWidget().layout())
        layout = self.main_layout
        if not layout and self.centralWidget():
            layout = self.centralWidget().layout()

        if layout is not None:
            back_button = QPushButton("Powrót")
            back_button.setStyleSheet(
                """
                background-color: #FFDAB9; /* pastelowy pomarańcz */
                color: #8B4513;            /* brąz */
                font-size: 14px;
                font-weight: bold;
                border-radius: 10px;
                padding: 10px;
            """
            )
            back_button.clicked.connect(self.go_back)
            layout.addWidget(back_button)

    def go_back(self) -> None:
        """
        Obsługuje kliknięcie przycisku 'Powrót'.
        Wywołuje show_previous_screen() w MainWindow, jeśli istnieje.
        """
        if self.parent and hasattr(self.parent, "show_previous_screen"):
            self.parent.show_previous_screen()

    # -------------- PRZYCISKI CRUD: Edytuj/Zapisz, Usuń --------------

    def create_edit_button(self, row: int) -> QPushButton:
        edit_button = QPushButton("Edytuj")
        edit_button.setStyleSheet(
            """
            background-color: #007bff;
            color: #FFFFFF;
            font-size: 12px;
            font-weight: bold;
            border-radius: 8px;
            padding: 5px 10px;
        """
        )
        edit_button.clicked.connect(lambda _, r=row: self.toggle_edit(r))
        return edit_button

    def create_delete_button(self, row: int) -> QPushButton:
        delete_button = QPushButton("Usuń")
        delete_button.setStyleSheet(
            """
            background-color: #FFCCCC;
            color: #800000;
            font-size: 12px;
            font-weight: bold;
            border-radius: 8px;
            padding: 5px 10px;
        """
        )
        delete_button.clicked.connect(lambda _, r=row: self.delete_record(r))
        return delete_button

    def toggle_edit(self, row: int) -> None:
        edit_col_index = len(self.columns) - 2
        edit_button = self.table.cellWidget(row, edit_col_index)
        if not edit_button:
            return

        if edit_button.text() == "Edytuj":
            edit_button.setText("Zapisz")
            self.enable_row_edit(row, True)
        else:
            edit_button.setText("Edytuj")
            self.save_changes(row)
            self.enable_row_edit(row, False)

    def enable_row_edit(self, row: int, enabled: bool) -> None:
        for col in range(1, len(self.columns) - 2):
            widget = self.table.cellWidget(row, col)
            if widget:
                widget.setEnabled(enabled)

    def save_changes(self, row: int) -> None:
        item_id_item = self.table.item(row, 0)
        if not item_id_item:
            return

        item_id = int(item_id_item.text())
        new_values: List[Any] = []

        from PyQt5.QtWidgets import QLineEdit, QComboBox

        for col in range(1, len(self.columns) - 2):
            widget = self.table.cellWidget(row, col)
            if widget:
                if isinstance(widget, QLineEdit):
                    new_values.append(widget.text().strip())
                elif isinstance(widget, QComboBox):
                    selected_data = widget.itemData(widget.currentIndex())
                    new_values.append(selected_data)
                else:
                    new_values.append("")
            else:
                new_values.append("")

        try:
            self.update_item_in_db(item_id, new_values)
            QMessageBox.information(self, "Sukces", "Zaktualizowano rekord w bazie.")
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się zapisać: {e}")

    def delete_record(self, row: int) -> None:
        item_id_item = self.table.item(row, 0)
        if not item_id_item:
            return

        item_id = int(item_id_item.text())

        confirm = QMessageBox.question(
            self, "Potwierdzenie", f"Czy na pewno usunąć rekord ID={item_id}?"
        )
        if confirm == QMessageBox.Yes:
            try:
                self.delete_item_in_db(item_id)
                QMessageBox.information(self, "Sukces", "Rekord został usunięty.")
                self.load_data()
            except Exception as e:
                QMessageBox.warning(self, "Błąd", f"Nie udało się usunąć: {e}")

    # -------------- Metody do nadpisania w potomnych ---------------

    def update_item_in_db(self, item_id: int, new_values: List[Any]) -> None:
        raise NotImplementedError("Nadpisz update_item_in_db w klasie potomnej!")

    def delete_item_in_db(self, item_id: int) -> None:
        raise NotImplementedError("Nadpisz delete_item_in_db w klasie potomnej!")
