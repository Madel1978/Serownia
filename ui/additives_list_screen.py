# c:\serownia\ui\additives_list_screen.py

from typing import Optional, Any, List

from PyQt5.QtWidgets import QLineEdit, QComboBox, QTableWidgetItem, QMessageBox, QDialog
from PyQt5.QtCore import Qt

from .base_crud_list_screen import BaseCrudListScreen
from .add_additive_dialog import (
    AddAdditiveDialog,
)  # <-- Upewnij się, że ścieżka jest poprawna


class AdditivesListScreen(BaseCrudListScreen):
    """
    Ekran wyświetlający listę dodatków (Additives) bez wagi, dawkowania i daty.
    Kolumny: [ID, Nazwa, Kategoria, Edytuj/Zapisz, Usuń].

    Obsługuje argument filter_text w load_data(filter_text="..."),
    aby klasa bazowa mogła wywoływać self.load_data(filter_text=coś) przy filtrowaniu.
    """

    def __init__(
        self, parent: Optional[Any] = None, db_manager: Optional[Any] = None
    ) -> None:
        """
        Inicjalizuje ekran "Lista Dodatków", bez wagi, dawkowania i daty.

        :param parent: Widok-rodzic (zazwyczaj MainWindow).
        :param db_manager: Obiekt bazy danych (DBManager).
        """
        self.db_manager = db_manager
        # Definiujemy nowe kolumny, bez wagi, dawkowania i daty
        super().__init__(
            parent=parent,
            title="Lista Dodatków",
            columns=["ID", "Nazwa", "Kategoria", "Edytuj/Zapisz", "Usuń"],
        )

    def load_data(self, filter_text: str = "") -> None:
        """
        Wypełnia tabelę wierszami z bazy. Kolumny:
         - 0: ID,
         - 1: Nazwa (QLineEdit, disabled),
         - 2: Kategoria (QComboBox, disabled),
         - 3: Edytuj/Zapisz,
         - 4: Usuń.

        Jeśli filter_text niepuste, filtrujemy dodatki np. po polu 'name' (case-insensitive).
        """
        print(f"[DEBUG] AdditivesListScreen.load_data(filter_text='{filter_text}')")

        self.table.setRowCount(0)
        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można załadować dodatków."
            )
            return

        # 1. Pobieramy wszystkie dodatki i kategorie
        additives = (
            self.db_manager.get_all_additives()
        )  # "id", "name", "weight", "dosage", "category_id"
        categories = self.db_manager.get_categories()  # "id", "name"

        # 2. Filtrowanie w Pythonie (opcjonalnie)
        ft_lower = filter_text.strip().lower()
        if ft_lower:
            # Przykład: filtrujemy w polu 'name'
            additives = [
                ad for ad in additives if ft_lower in ad.get("name", "").lower()
            ]

        print(
            f"[DEBUG] Znaleziono {len(additives)} dodatków (po filtrze='{filter_text}')"
        )

        # 3. Tworzymy mapowanie category_id -> category_name
        cat_dict = {cat["id"]: cat["name"] for cat in categories}

        # 4. Wypełniamy tabelę
        for row_index, ad in enumerate(additives):
            self.table.insertRow(row_index)

            # Kol 0: ID (zablokowane)
            id_item = QTableWidgetItem(str(ad["id"]))
            id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row_index, 0, id_item)

            # Kol 1: Nazwa (QLineEdit)
            name_edit = QLineEdit(str(ad.get("name", "")))
            name_edit.setEnabled(False)
            self.table.setCellWidget(row_index, 1, name_edit)

            # Kol 2: Kategoria (QComboBox)
            cat_combo = QComboBox()
            cat_combo.setEnabled(False)

            for c_id, c_name in cat_dict.items():
                cat_combo.addItem(c_name, c_id)

            current_cat_id = ad.get("category_id")
            idx_to_select = 0
            for i in range(cat_combo.count()):
                if cat_combo.itemData(i) == current_cat_id:
                    idx_to_select = i
                    break
            cat_combo.setCurrentIndex(idx_to_select)
            self.table.setCellWidget(row_index, 2, cat_combo)

            # Kol 3: Edytuj/Zapisz (przycisk)
            edit_button = self.create_edit_button(row_index)
            self.table.setCellWidget(row_index, 3, edit_button)

            # Kol 4: Usuń (przycisk)
            delete_button = self.create_delete_button(row_index)
            self.table.setCellWidget(row_index, 4, delete_button)

        self.table.resizeColumnsToContents()

    def update_item_in_db(self, item_id: int, new_values: List[Any]) -> None:
        """
        Wywoływana przy zapisie (po 'Zapisz'). new_values -> [nazwa, cat_id].
        """
        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można zapisać dodatku."
            )
            return

        new_name = new_values[0]
        cat_id = new_values[1]

        # Ponieważ usunęliśmy w UI pola 'Waga', 'Dawkowanie',
        # przekazujemy puste wartości do bazy:
        weight_placeholder = ""
        dosage_placeholder = ""

        try:
            self.db_manager.update_additive(
                item_id, new_name, weight_placeholder, dosage_placeholder, cat_id
            )
            QMessageBox.information(self, "Sukces", "Zaktualizowano rekord w bazie.")
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się zapisać: {e}")
            return

    def save_changes(self, row: int) -> None:
        """
        Nadpisuje metodę z BaseCrudListScreen, żeby rozpoznać QComboBox w kolumnie 2.
        """
        item_id_item = self.table.item(row, 0)
        if not item_id_item:
            return
        item_id = int(item_id_item.text())

        # Nazwa i kategoria to kolumny 1,2
        new_values: List[Any] = []
        for col in range(1, len(self.columns) - 2):
            widget = self.table.cellWidget(row, col)
            if col == 2 and isinstance(widget, QComboBox):
                cat_id = widget.itemData(widget.currentIndex())
                new_values.append(cat_id)
            else:
                text_value = widget.text().strip()
                new_values.append(text_value)

        try:
            self.update_item_in_db(item_id, new_values)
            QMessageBox.information(self, "Sukces", "Zaktualizowano rekord w bazie.")
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się zapisać: {e}")

        self.enable_row_edit(row, False)
        edit_col_index = len(self.columns) - 2
        edit_button = self.table.cellWidget(row, edit_col_index)
        if edit_button:
            edit_button.setText("Edytuj")

    def delete_item_in_db(self, item_id: int) -> None:
        """
        Usuwa dodatek na podstawie ID.
        """
        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można usunąć dodatku."
            )
            return

        self.db_manager.delete_additive(item_id)

    def add_new_item(self) -> None:
        """
        Obsługa przycisku 'Nowy' (z klasy bazowej).
        Otwiera dialog do dodania nowego dodatku (bez wagi, dawkowania).
        """
        if not self.db_manager:
            QMessageBox.warning(
                self, "Błąd", "Brak db_manager – nie można dodać dodatku."
            )
            return

        dialog = AddAdditiveDialog(parent=self, db_manager=self.db_manager)

        if dialog.exec_() == QDialog.Accepted:
            self.load_data()
        else:
            QMessageBox.information(self, "Nowy", "Anulowano dodawanie dodatku.")
