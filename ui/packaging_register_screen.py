# c:\serownia\ui\packaging_register_screen.py

from typing import Optional, List, Dict, Any

from PyQt5.QtWidgets import (
    QDialog,
    QMessageBox,
    QLineEdit,
    QComboBox,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QTableWidgetItem,
    QWidget,
)
from PyQt5.QtCore import Qt

from .base_crud_list_screen import BaseCrudListScreen
from database.db_manager import (
    DBManager,
)  # Dostosuj import, jeśli pliki są inaczej zorganizowane


class AddPackagingRegisterDialog(QDialog):
    """
    Dialog do dodania nowego wpisu w rejestrze opakowań:
      - Data przyjęcia (YYYY-MM-DD),
      - Ilość,
      - Opakowanie (z QComboBox).
    """

    def __init__(
        self, parent: Optional[QWidget] = None, db_manager: Optional[DBManager] = None
    ) -> None:
        super().__init__(parent)
        self.db_manager = db_manager

        self.setWindowTitle("Dodaj wpis w Rejestrze Opakowań")
        self.setGeometry(300, 300, 400, 200)

        layout = QVBoxLayout(self)

        # Pole: Data przyjęcia
        layout.addWidget(QLabel("Data przyjęcia (YYYY-MM-DD):"))
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("YYYY-MM-DD")
        layout.addWidget(self.date_input)

        # Pole: Ilość
        layout.addWidget(QLabel("Ilość przyjęta:"))
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Ilość przyjęta")
        layout.addWidget(self.quantity_input)

        # Wybór opakowania (QComboBox)
        layout.addWidget(QLabel("Wybierz opakowanie:"))
        self.packaging_combo = QComboBox()
        layout.addWidget(self.packaging_combo)

        # Wypełnienie comboBox
        self.fill_packaging_combo()

        # Przycisk Zapisz
        save_button = QPushButton("Zapisz")
        save_button.clicked.connect(self.save_data)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def fill_packaging_combo(self) -> None:
        """
        Pobiera listę opakowań z bazy i wypełnia QComboBox.
        """
        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można pobrać listy opakowań."
            )
            return

        all_packs = self.db_manager.get_all_packaging()
        if not all_packs:
            return  # Brak opakowań? Kombo będzie puste.

        for p in all_packs:
            self.packaging_combo.addItem(p["name"], p["id"])

    def save_data(self) -> None:
        """
        Zapisuje nowy wpis w rejestrze opakowań (packaging_register).
        Waliduje dane i wywołuje db_manager.add_packaging_register(...).
        """
        date_str = self.date_input.text().strip()
        quantity_str = self.quantity_input.text().strip()
        packaging_id = self.packaging_combo.itemData(
            self.packaging_combo.currentIndex()
        )

        if not date_str or not quantity_str:
            QMessageBox.warning(self, "Błąd", "Data i ilość są wymagane.")
            return

        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można zapisać wpisu."
            )
            return

        try:
            self.db_manager.add_packaging_register(date_str, quantity_str, packaging_id)
            QMessageBox.information(
                self,
                "Sukces",
                f"Nowy wpis w rejestrze opakowań:\n"
                f"Data={date_str}, Ilość={quantity_str}, ID opakowania={packaging_id}",
            )
            self.accept()

        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się dodać wpisu: {e}")


class PackagingRegisterScreen(BaseCrudListScreen):
    """
    Ekran "Rejestr Opakowań" – dziedziczy po BaseCrudListScreen.
    Wyświetla kolumny: [ID, Data, Ilość, Nazwa opakowania, Edytuj/Zapisz, Usuń].
    Obsługuje argument filter_text w load_data(filter_text=...),
    aby klasa bazowa mogła wywoływać self.load_data(filter_text="...") podczas filtracji.
    """

    def __init__(
        self, parent: Optional[QWidget] = None, db_manager: Optional[DBManager] = None
    ) -> None:
        self.db_manager = db_manager
        super().__init__(
            parent=parent,
            title="Rejestr Opakowań",
            columns=["ID", "Data", "Ilość", "Opakowanie", "Edytuj/Zapisz", "Usuń"],
        )

    def load_data(self, filter_text: str = "") -> None:
        """
        Pobiera listę wpisów z bazy (packaging_register),
        ewentualnie filtruje po nazwie opakowania (case-insensitive),
        i wypełnia tabelę.

        Kolumny:
         - 0: ID
         - 1: Data
         - 2: Ilość
         - 3: Nazwa opakowania (packaging_name)
         - 4: Edytuj/Zapisz
         - 5: Usuń
        """
        print(f"[DEBUG] PackagingRegisterScreen.load_data(filter_text='{filter_text}')")

        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można załadować danych."
            )
            return

        self.table.setRowCount(0)
        # Pobieramy listę rekordów z rejestru opakowań
        records = (
            self.db_manager.get_all_packaging_register()
        )  # np. [{"id":..., "date":..., "quantity":..., "packaging_name":...}, ...]

        # Jeśli filter_text != "", filtrujemy w Pythonie po packaging_name
        ft_lower = filter_text.strip().lower()
        if ft_lower:
            records = [
                r for r in records if ft_lower in (r["packaging_name"] or "").lower()
            ]

        print(
            f"[DEBUG] Znaleziono {len(records)} rekordów w rejestrze opakowań (po filtrze='{filter_text}')"
        )

        for row_index, rec in enumerate(records):
            self.table.insertRow(row_index)

            # Kol 0: ID
            item_id = QTableWidgetItem(str(rec["id"]))
            item_id.setFlags(item_id.flags() ^ Qt.ItemIsEditable)
            self.table.setItem(row_index, 0, item_id)

            # Kol 1: Data
            date_edit = QLineEdit(str(rec.get("date", "")))
            date_edit.setEnabled(False)
            self.table.setCellWidget(row_index, 1, date_edit)

            # Kol 2: Ilość
            qty_edit = QLineEdit(str(rec.get("quantity", "")))
            qty_edit.setEnabled(False)
            self.table.setCellWidget(row_index, 2, qty_edit)

            # Kol 3: Nazwa opakowania
            pack_edit = QLineEdit(str(rec.get("packaging_name", "")))
            pack_edit.setEnabled(False)
            self.table.setCellWidget(row_index, 3, pack_edit)

            # Kol 4: Edytuj/Zapisz (przycisk)
            edit_button = self.create_edit_button(row_index)
            self.table.setCellWidget(row_index, 4, edit_button)

            # Kol 5: Usuń (przycisk)
            delete_button = self.create_delete_button(row_index)
            self.table.setCellWidget(row_index, 5, delete_button)

        self.table.resizeColumnsToContents()

    def add_new_item(self) -> None:
        """
        Obsługa przycisku 'Nowy' z BaseCrudListScreen.
        Otwiera dialog AddPackagingRegisterDialog, dodaje wpis i odświeża listę.
        """
        dialog = AddPackagingRegisterDialog(self, self.db_manager)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()
        else:
            QMessageBox.information(
                self, "Nowy", "Anulowano dodawanie wpisu w rejestrze opakowań."
            )

    def toggle_edit(self, row: int) -> None:
        """
        Przełącza między trybem 'Edytuj' i 'Zapisz' w danym wierszu.
        """
        edit_col_index = len(self.columns) - 2
        edit_button = self.table.cellWidget(row, edit_col_index)
        if not edit_button:
            return

        if edit_button.text() == "Edytuj":
            edit_button.setText("Zapisz")
            self.enable_row_edit(row, True)
            # Ewentualnie zamiana QLineEdit -> QComboBox dla opakowania (kol.3)
            # jeśli chcesz, by user zmieniał opakowanie
        else:
            edit_button.setText("Edytuj")
            self.save_changes(row)
            self.enable_row_edit(row, False)

    def save_changes(self, row: int) -> None:
        """
        Nadpisuje metodę z BaseCrudListScreen; odczytuje kolumny (1=Data, 2=Ilość, 3=Opakowanie?)
        i wywołuje update_item_in_db(register_id, new_values).
        """
        item_id_item = self.table.item(row, 0)
        if not item_id_item:
            return

        register_id = int(item_id_item.text())

        new_values = []
        # Kolumny 1=Data, 2=Ilość, 3=NazwaOpakowania (albo ID, jeśli zrobisz QComboBox)
        for col in range(1, len(self.columns) - 2):
            widget = self.table.cellWidget(row, col)
            text_value = widget.text().strip() if widget else ""
            new_values.append(text_value)

        # new_values -> [date_str, quantity_str, packaging_name/...]
        self.update_item_in_db(register_id, new_values)

        QMessageBox.information(self, "Sukces", "Zaktualizowano rekord w bazie.")

    def update_item_in_db(self, register_id: int, new_values: List[Any]) -> None:
        """
        Aktualizuje wpis w bazie danych, np. db_manager.update_packaging_register(register_id, date, quantity, packaging_id).
        Ale tu zależy od tego, jak chcesz przechowywać 'packaging_name' / 'packaging_id'.
        """
        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można zapisać zmian."
            )
            return

        date_str = new_values[0]
        quantity_str = new_values[1]
        packaging_name_or_id = new_values[2]

        # Tu do ustalenia, czy w bazie chcesz packaging_id czy packaging_name:
        # Przykład (jeśli w DB trzymasz packaging_id, musisz wyszukać ID po nazwie):
        # packaging_id = self.resolve_packaging_id_from_name(packaging_name_or_id)
        # self.db_manager.update_packaging_register(register_id, date_str, quantity_str, packaging_id)
        # self.load_data()

        print(
            f"[DEBUG] update_item_in_db ID={register_id}, date={date_str}, qty={quantity_str}, packaging=??? (dostosuj)"
        )

    def delete_item_in_db(self, item_id: int) -> None:
        """
        Usuwanie wpisu z rejestru opakowań.
        """
        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można usunąć wpisu."
            )
            return

        # np. self.db_manager.delete_packaging_register(item_id)
        # self.load_data()
        QMessageBox.information(
            self, "Info", f"Tu zaimplementuj usuwanie wpisu ID={item_id}."
        )
