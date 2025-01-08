# c:\serownia\ui\additives_register_screen.py

from typing import Optional, Any, List

from PyQt5.QtWidgets import (
    QDialog,
    QMessageBox,
    QVBoxLayout,
    QLineEdit,
    QLabel,
    QComboBox,
    QPushButton,
    QTableWidgetItem,
)
from PyQt5.QtCore import Qt

# Dziedziczymy po BaseCrudListScreen
from .base_crud_list_screen import BaseCrudListScreen
from database.db_manager import (
    DBManager,
)  # Dostosuj import, jeśli pliki są inaczej zorganizowane


class AdditivesRegisterScreen(BaseCrudListScreen):
    """
    Ekran "Rejestr Dodatków", umożliwiający:
      - przeglądanie wpisów w tabeli (ID, Data, Ilość, Rodzaj Dodatku, Edytuj/Zapisz, Usuń),
      - dodawanie nowego wpisu (przycisk "Nowy"),
      - edycję istniejących wpisów (kolumna "Edytuj/Zapisz"),
      - usuwanie wpisów (kolumna "Usuń").

    Obsługuje argument filter_text w load_data(filter_text=...),
    by klasa bazowa mogła wywołać self.load_data(filter_text="...") przy filtracji.
    """

    def __init__(
        self,
        parent: Optional[Any] = None,  # Najczęściej QMainWindow
        db_manager: Optional[DBManager] = None,
    ) -> None:
        """
        Inicjalizuje ekran rejestru dodatków, definiując kolumny:
          [ID, Data, Ilość, Rodzaj Dodatku, Edytuj/Zapisz, Usuń].

        :param parent: Widok-rodzic, np. MainWindow.
        :param db_manager: Obiekt dostarczający metod do komunikacji z bazą danych.
        """
        self.db_manager = db_manager
        super().__init__(
            parent=parent,
            title="Rejestr Dodatków",
            columns=[
                "ID",
                "Data przyjęcia",
                "Ilość",
                "Rodzaj Dodatku",
                "Edytuj/Zapisz",
                "Usuń",
            ],
        )

    def load_data(self, filter_text: str = "") -> None:
        """
        Ładuje dane z rejestru dodatków (db_manager.get_all_additives_register())
        i wypełnia tabelę.

        Każdy rekord może wyglądać np. tak:
          {
            "id": 1,
            "date": "2024-12-27",
            "quantity": "10",
            "additive_id": 2,
            "additive_name": "Kozieradka"
          }

        Jeśli filter_text niepuste, filtrujemy w Pythonie po "additive_name" (case-insensitive).
        """
        print(f"[DEBUG] AdditivesRegisterScreen.load_data(filter_text='{filter_text}')")

        self.table.setRowCount(0)
        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można załadować rejestru dodatków."
            )
            return

        rejestr_list = (
            self.db_manager.get_all_additives_register()
        )  # np. [{"id":..., "date":..., "quantity":..., "additive_name":...}, ...]

        # Filtrowanie po additive_name (opcjonalnie)
        ft_lower = filter_text.strip().lower()
        if ft_lower:
            rejestr_list = [
                rec
                for rec in rejestr_list
                if ft_lower in (rec.get("additive_name", "")).lower()
            ]

        print(
            f"[DEBUG] Znaleziono {len(rejestr_list)} wpisów w rejestrze (po filtrze='{filter_text}')"
        )

        for row_index, rec in enumerate(rejestr_list):
            self.table.insertRow(row_index)

            # Kol 0: ID (zablokowany do edycji)
            id_item = QTableWidgetItem(str(rec["id"]))
            id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row_index, 0, id_item)

            # Kol 1: Data
            date_edit = QLineEdit(str(rec.get("date", "")))
            date_edit.setEnabled(False)
            self.table.setCellWidget(row_index, 1, date_edit)

            # Kol 2: Ilość
            qty_edit = QLineEdit(str(rec.get("quantity", "")))
            qty_edit.setEnabled(False)
            self.table.setCellWidget(row_index, 2, qty_edit)

            # Kol 3: Rodzaj Dodatku (domyślnie QLineEdit, wyłączona edycja)
            additive_name_edit = QLineEdit(str(rec.get("additive_name", "")))
            additive_name_edit.setEnabled(False)
            self.table.setCellWidget(row_index, 3, additive_name_edit)

            # Kol 4: Edytuj/Zapisz (przycisk)
            edit_button = self.create_edit_button(row_index)
            self.table.setCellWidget(row_index, 4, edit_button)

            # Kol 5: Usuń (przycisk)
            delete_button = self.create_delete_button(row_index)
            self.table.setCellWidget(row_index, 5, delete_button)

        self.table.resizeColumnsToContents()

    def add_new_item(self) -> None:
        """
        Obsługa przycisku 'Nowy' (z paska narzędzi).
        Tworzy dialog AddAdditiveRegisterDialog i po zapisaniu (accept)
        odświeża tabelę (self.load_data).
        """
        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można dodać wpisu."
            )
            return

        dialog = AddAdditiveRegisterDialog(self, self.db_manager)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()
        else:
            QMessageBox.information(
                self, "Nowy", "Anulowano dodawanie wpisu w rejestrze dodatków."
            )

    def toggle_edit(self, row: int) -> None:
        """
        Przełącza tryb: 'Edytuj' <-> 'Zapisz'.
        Jeśli 'Edytuj' -> włączamy edycję wiersza (enable_row_edit),
                          zamieniamy QLineEdit w kolumnie 3 (Rodzaj Dodatku) na QComboBox.
        Jeśli 'Zapisz' -> odczytujemy dane, wywołujemy save_changes(row),
                          wyłączamy edycję wiersza.
        """
        edit_col_index = len(self.columns) - 2  # kolumna 'Edytuj/Zapisz'
        edit_button = self.table.cellWidget(row, edit_col_index)
        if not edit_button:
            return

        if edit_button.text() == "Edytuj":
            edit_button.setText("Zapisz")
            self.enable_row_edit(row, True)
            self.setup_combo_in_column_3(row)
        else:
            edit_button.setText("Edytuj")
            self.save_changes(row)
            self.enable_row_edit(row, False)

    def setup_combo_in_column_3(self, row: int) -> None:
        """
        Zastępuje QLineEdit w kolumnie 3 (Rodzaj Dodatku) -> QComboBox
        z listą dodatków (db_manager.get_all_additives()).
        Ustawiamy combo na dodatku, który był wpisany w QLineEdit.
        """
        old_widget = self.table.cellWidget(row, 3)
        old_text = old_widget.text().strip() if old_widget else ""

        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można wczytać listy dodatków."
            )
            return

        additives_list = self.db_manager.get_all_additives()
        combo = QComboBox()

        index_to_select = 0
        for i, add in enumerate(additives_list):
            combo.addItem(add["name"], add["id"])
            # Jeśli nazwa w bazie == old_text (case-insensitive)
            if add["name"].lower() == old_text.lower():
                index_to_select = i

        combo.setCurrentIndex(index_to_select)
        self.table.setCellWidget(row, 3, combo)

    def save_changes(self, row: int) -> None:
        """
        Nadpisuje metodę z BaseCrudListScreen, aby odczytać ID dodatku z QComboBox
        w kolumnie 3 (Rodzaj Dodatku).
        """
        item_id_item = self.table.item(row, 0)
        if not item_id_item:
            return
        register_id = int(item_id_item.text())

        new_values: List[Any] = []
        # Kolumny: 1=Data, 2=Ilość, 3=Rodzaj Dodatku
        for col in range(1, len(self.columns) - 2):
            widget = self.table.cellWidget(row, col)
            if col == 3 and isinstance(widget, QComboBox):
                # Odczytujemy ID dodatku
                chosen_id = widget.itemData(widget.currentIndex())
                new_values.append(chosen_id)
            else:
                text_value = widget.text().strip() if widget else ""
                new_values.append(text_value)

        # new_values -> [date_str, quantity_str, additive_id]
        self.update_item_in_db(register_id, new_values)

        QMessageBox.information(self, "Sukces", "Zaktualizowano rekord w bazie.")

    def update_item_in_db(self, register_id: int, new_values: List[Any]) -> None:
        """
        Domyślnie: [date_str, quantity_str, additive_id].
        Możesz wywołać np. db_manager.update_additive_register(register_id, date_str, quantity_str, additive_id).

        :param register_id: ID rekordu w tabeli additives_register.
        :param new_values: Lista [date_str, quantity_str, additive_id].
        """
        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można zaktualizować wpisu."
            )
            return

        date_str = new_values[0]
        quantity_str = new_values[1]
        additive_id = new_values[2]

        try:
            self.db_manager.update_additive_register(
                register_id, date_str, quantity_str, additive_id
            )
            # Po zapisie można odświeżyć dane (opcjonalnie)
            self.load_data()
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się zapisać zmian: {e}")

    def delete_item_in_db(self, item_id: int) -> None:
        """
        Usuwanie (po kliknięciu 'Usuń').
        Domyślnie: db_manager.delete_additive_register(item_id).
        """
        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można usunąć wpisu."
            )
            return

        # np.:
        # self.db_manager.delete_additive_register(item_id)
        # self.load_data()
        pass


class AddAdditiveRegisterDialog(QDialog):
    """
    Dialog do dodania nowego wpisu w Rejestrze Dodatków:
      - Data przyjęcia
      - Ilość
      - Rodzaj Dodatku (QComboBox)
    """

    def __init__(
        self,
        parent: Optional[Any] = None,  # Najczęściej AdditivesRegisterScreen
        db_manager: Optional[Any] = None,  # Docelowo: Optional[DBManager]
    ) -> None:
        """
        Tworzy formularz do dodania wpisu w rejestrze dodatków.
        :param parent: Okno-rodzic, np. AdditivesRegisterScreen.
        :param db_manager: Obiekt bazy danych.
        """
        super().__init__(parent)
        self.db_manager = db_manager

        self.setWindowTitle("Dodaj wpis w Rejestrze Dodatków")
        self.setGeometry(300, 300, 400, 200)

        layout = QVBoxLayout(self)

        # Etykieta i pole: Data przyjęcia
        layout.addWidget(QLabel("Data przyjęcia (YYYY-MM-DD):"))
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("2024-12-27")
        layout.addWidget(self.date_input)

        # Etykieta i pole: Ilość
        layout.addWidget(QLabel("Ilość przyjęta:"))
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("np. 10")
        layout.addWidget(self.quantity_input)

        # Etykieta i ComboBox: Rodzaj Dodatku
        layout.addWidget(QLabel("Rodzaj Dodatku:"))
        self.additive_combo = QComboBox()
        layout.addWidget(self.additive_combo)

        # Wypełniamy listę dodatków
        self.fill_additives_combo()

        # Przycisk Zapisz
        save_button = QPushButton("Zapisz")
        save_button.clicked.connect(self.save_data)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def fill_additives_combo(self) -> None:
        """
        Wypełnia listę dodatków (np. z db_manager.get_all_additives()) w QComboBox.
        """
        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można wczytać listy dodatków."
            )
            return

        all_additives = self.db_manager.get_all_additives()
        for ad in all_additives:
            self.additive_combo.addItem(ad["name"], ad["id"])

    def save_data(self) -> None:
        """
        Po kliknięciu 'Zapisz' wstawia rekord do tabeli additives_register
        poprzez db_manager.add_additive_register(...), a następnie wywołuje self.accept().
        """
        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można zapisać wpisu."
            )
            return

        date_str = self.date_input.text().strip()
        quantity_str = self.quantity_input.text().strip()
        additive_id = self.additive_combo.itemData(self.additive_combo.currentIndex())

        if not date_str or not quantity_str:
            QMessageBox.warning(self, "Błąd", "Data i ilość są wymagane.")
            return

        try:
            self.db_manager.add_additive_register(date_str, quantity_str, additive_id)
            QMessageBox.information(
                self,
                "Sukces",
                f"Dodano wpis w rejestrze dodatków:\n"
                f"Data={date_str}, ilość={quantity_str}, ID dodatku={additive_id}",
            )
            self.accept()
        except Exception as e:
            QMessageBox.warning(
                self, "Błąd", f"Nie udało się dodać wpisu w rejestrze: {e}"
            )
