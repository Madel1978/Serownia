# c:\serownia\ui\packaging_list_screen.py

from typing import Optional, Any, List

from PyQt5.QtWidgets import (
    QLineEdit, QDialog, QMessageBox, QComboBox, QTableWidgetItem
)
from PyQt5.QtCore import Qt

from ui.base_crud_list_screen import BaseCrudListScreen
from .add_packaging_dialog import AddPackagingDialog  # <-- Upewnij się, że ścieżka jest poprawna

class PackagingListScreen(BaseCrudListScreen):
    """
    Ekran wyświetlający listę opakowań (bez kolumn 'Ilość' i 'Data').
    Kolumny: [ID, Nazwa, Kategoria, Edytuj/Zapisz, Usuń].
    
    Obsługuje opcjonalny argument filter_text w load_data, 
    aby klasa bazowa mogła wywoływać load_data(filter_text="...") 
    i przefiltrować nazwy opakowań.
    """

    def __init__(
        self,
        parent: Optional[Any] = None,
        db_manager: Optional[Any] = None
    ) -> None:
        """
        Inicjalizuje ekran "Lista Opakowań", ograniczony do kolumn
        [ID, Nazwa, Kategoria, Edytuj/Zapisz, Usuń].

        :param parent: Widok-rodzic (np. MainWindow).
        :param db_manager: Obiekt bazy danych (DBManager).
        """
        self.db_manager = db_manager
        # Definiujemy kolumny bez ilości i daty
        super().__init__(
            parent=parent,
            title="Lista Opakowań",
            columns=["ID", "Nazwa", "Kategoria", "Edytuj/Zapisz", "Usuń"]
        )

    def load_data(self, filter_text: str = "") -> None:
        """
        Wypełnia tabelę wierszami z bazy.
        Kolumny:
         - 0: ID (zablokowany),
         - 1: Nazwa (QLineEdit, disabled),
         - 2: Kategoria (QComboBox, disabled),
         - 3: Edytuj/Zapisz,
         - 4: Usuń.
         
        Jeśli 'filter_text' nie jest pusty, filtrujemy opakowania po 'name' 
        (case-insensitive).
        """
        print(f"[DEBUG] PackagingListScreen.load_data(filter_text='{filter_text}')")

        if not self.db_manager:
            QMessageBox.critical(self, "Błąd", "Brak db_manager – nie można załadować opakowań.")
            return

        # Czyścimy tabelę
        self.table.setRowCount(0)

        # Pobieramy wszystkie opakowania z bazy
        # Każdy wpis to np. {"id":..., "name":..., "quantity":..., "date":..., "packaging_category_id":...}
        packaging_list = self.db_manager.get_all_packaging()

        # Pobieramy kategorie
        categories = self.db_manager.get_packaging_categories()
        cat_dict = {cat["id"]: cat["name"] for cat in categories}

        # 1. Jeżeli filter_text niepuste, filtrujemy w Pythonie po 'name'
        ft_lower = filter_text.strip().lower()
        if ft_lower:
            packaging_list = [
                p for p in packaging_list
                if ft_lower in (p["name"] or "").lower()
            ]

        print(f"[DEBUG] Znaleziono {len(packaging_list)} opakowań (po filtrze='{filter_text}').")

        # 2. Wypełniamy tabelę
        for row_index, pack in enumerate(packaging_list):
            self.table.insertRow(row_index)

            # Kol 0: ID (zablokowany)
            id_item = QTableWidgetItem(str(pack["id"]))
            id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row_index, 0, id_item)

            # Kol 1: Nazwa (QLineEdit, disabled)
            name_edit = QLineEdit(str(pack.get("name", "")))
            name_edit.setEnabled(False)
            self.table.setCellWidget(row_index, 1, name_edit)

            # Kol 2: Kategoria (QComboBox, disabled)
            cat_combo = QComboBox()
            cat_combo.setEnabled(False)
            for c_id, c_name in cat_dict.items():
                cat_combo.addItem(c_name, c_id)

            current_cat_id = pack.get("packaging_category_id")
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

    def add_new_item(self) -> None:
        """
        Obsługa przycisku 'Nowy' (z klasy bazowej).
        Otwiera dialog do dodania nowego opakowania (bez ilości i daty).
        """
        if not self.db_manager:
            QMessageBox.warning(self, "Błąd", "Brak db_manager – nie można dodać opakowania.")
            return

        # Tworzymy instancję dialogu AddPackagingDialog
        dialog = AddPackagingDialog(parent=self, db_manager=self.db_manager)

        # Wywołujemy go modalnie
        if dialog.exec_() == QDialog.Accepted:
            # Po kliknięciu „Zapisz” w dialogu i poprawnym dodaniu w bazie
            self.load_data()  # odśwież listę
        else:
            QMessageBox.information(self, "Nowe opakowanie", "Anulowano dodawanie opakowania.")

    def update_item_in_db(self, item_id: int, new_values: List[Any]) -> None:
        """
        Wywoływane przy zapisie (po 'Zapisz'). new_values -> [nazwa, category_id].
        """
        if not self.db_manager:
            QMessageBox.critical(self, "Błąd", "Brak db_manager – nie można zaktualizować opakowania.")
            return

        new_name = new_values[0]
        cat_id = new_values[1]

        # Ponieważ usunęliśmy "Ilość" i "Data" z UI, możemy przekazać puste ciągi
        quantity_placeholder = ""
        date_placeholder = ""

        try:
            self.db_manager.update_packaging(item_id, new_name, quantity_placeholder, date_placeholder, cat_id)
            # (Opcjonalnie) nie wywołuj self.load_data() tu, bo base_crud_list_screen może to robić
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się zapisać: {e}")
            return

    def save_changes(self, row: int) -> None:
        """
        Nadpisuje metodę z BaseCrudListScreen, by rozpoznać QComboBox w kolumnie 2.
        """
        item_id_item = self.table.item(row, 0)
        if not item_id_item:
            return
        packaging_id = int(item_id_item.text())

        new_values: List[Any] = []
        # Kolumny 1..(len(columns)-2) to editable (Nazwa, Kategoria)
        for col in range(1, len(self.columns) - 2):
            widget = self.table.cellWidget(row, col)
            if col == 2 and isinstance(widget, QComboBox):
                cat_id = widget.itemData(widget.currentIndex())
                new_values.append(cat_id)
            else:
                text_value = widget.text().strip()
                new_values.append(text_value)

        try:
            self.update_item_in_db(packaging_id, new_values)
            QMessageBox.information(self, "Sukces", "Zaktualizowano rekord w bazie.")
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się zapisać: {e}")
            return

        # Wyłącz edycję
        self.enable_row_edit(row, False)
        edit_col_index = len(self.columns) - 2
        edit_button = self.table.cellWidget(row, edit_col_index)
        if edit_button:
            edit_button.setText("Edytuj")

    def delete_item_in_db(self, item_id: int) -> None:
        """
        Usuwa opakowanie (bez pytania o ilość i datę, bo ich nie ma w UI).
        """
        if not self.db_manager:
            QMessageBox.critical(self, "Błąd", "Brak db_manager – nie można usunąć opakowania.")
            return

        self.db_manager.delete_packaging(item_id)
