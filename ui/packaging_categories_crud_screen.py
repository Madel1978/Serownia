# c:\serownia\ui\packaging_categories_crud_screen.py

from typing import Optional, Any, List

from PyQt5.QtWidgets import (
    QLineEdit, QTableWidgetItem, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt

from ui.base_crud_list_screen import BaseCrudListScreen


class PackagingCategoriesCrudScreen(BaseCrudListScreen):
    """
    Ekran z listą kategorii opakowań (CRUD):
      - Dodawanie nowej kategorii (przycisk 'Nowy'),
      - Edycja nazwy kategorii (Edytuj/Zapisz),
      - Usuwanie (Usuń).

    Obsługuje argument filter_text w load_data(filter_text="..."),
    aby klasa bazowa mogła wywoływać self.load_data(filter_text="cos") przy filtracji.
    """

    def __init__(
        self,
        parent: Optional[Any] = None,   # najczęściej QMainWindow
        db_manager: Optional[Any] = None
    ) -> None:
        """
        Definiujemy kolumny: [ID, Nazwa kategorii opakowań, Edytuj/Zapisz, Usuń].
        """
        self.db_manager = db_manager
        super().__init__(
            parent=parent,
            title="Kategorie Opakowań (CRUD)",
            columns=["ID", "Nazwa kategorii opakowań", "Edytuj/Zapisz", "Usuń"]
        )

    def load_data(self, filter_text: str = "") -> None:
        """
        Pobiera listę kategorii opakowań (db_manager.get_packaging_categories())
        i wypełnia tabelę. Ostatnie 2 kolumny na Edytuj/Zapisz i Usuń.

        Jeśli filter_text niepuste, filtrujemy w Pythonie po polu "name".

        columns = [0=ID, 1=Nazwa, 2=Edytuj/Zapisz, 3=Usuń].
        """
        print(f"[DEBUG] PackagingCategoriesCrudScreen.load_data(filter_text='{filter_text}')")

        if not self.db_manager:
            QMessageBox.critical(self, "Błąd", "Brak db_manager.")
            return

        self.table.setRowCount(0)
        # 1. Pobieramy wszystkie kategorie
        categories = self.db_manager.get_packaging_categories()  # np. [{"id": 1, "name": "..."}]

        # 2. (Opcjonalna) filtracja w Pythonie
        ft_lower = filter_text.strip().lower()
        if ft_lower:
            categories = [
                cat for cat in categories
                if ft_lower in cat["name"].lower()
            ]

        print(f"[DEBUG] Znaleziono {len(categories)} kategorii (po filtrze='{filter_text}')")

        # 3. Wypełniamy tabelę
        for row_index, cat in enumerate(categories):
            self.table.insertRow(row_index)

            # Kol 0: ID
            id_item = QTableWidgetItem(str(cat["id"]))
            id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row_index, 0, id_item)

            # Kol 1: Nazwa kategorii
            name_edit = QLineEdit(cat["name"])
            name_edit.setEnabled(False)
            self.table.setCellWidget(row_index, 1, name_edit)

            # Kol 2: Edytuj/Zapisz
            edit_button = self.create_edit_button(row_index)
            self.table.setCellWidget(row_index, 2, edit_button)

            # Kol 3: Usuń
            delete_button = self.create_delete_button(row_index)
            self.table.setCellWidget(row_index, 3, delete_button)

        self.table.resizeColumnsToContents()

    def add_new_item(self) -> None:
        """
        Obsługa przycisku 'Nowy' – wywołuje QInputDialog do wpisania nazwy
        nowej kategorii opakowań.
        """
        if not self.db_manager:
            QMessageBox.critical(self, "Błąd", "Brak db_manager.")
            return

        name, ok = QInputDialog.getText(
            self,
            "Dodaj kategorię opakowań",
            "Nazwa nowej kategorii:"
        )
        if ok and name.strip():
            try:
                self.db_manager.add_packaging_category(name.strip())
                QMessageBox.information(self, "Sukces", f"Dodano kategorię: {name.strip()}")
                self.load_data()
            except Exception as e:
                QMessageBox.warning(self, "Błąd", f"Nie udało się dodać kategorii: {e}")

    def update_item_in_db(self, item_id: int, new_values: List[Any]) -> None:
        """
        Zapisywanie zmienionej nazwy kategorii (1 kolumna: nazwa).

        :param item_id: ID kategorii.
        :param new_values: [nazwa_kategorii].
        """
        if not self.db_manager:
            QMessageBox.critical(self, "Błąd", "Brak db_manager.")
            return

        new_name = new_values[0] if len(new_values) > 0 else ""

        try:
            self.db_manager.update_packaging_category(item_id, new_name)
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się zaktualizować kategorii: {e}")
            raise

    def delete_item_in_db(self, item_id: int) -> None:
        """
        Usuwa kategorię opakowań z bazy.

        :param item_id: ID kategorii w tabeli packaging_categories.
        """
        if not self.db_manager:
            QMessageBox.critical(self, "Błąd", "Brak db_manager.")
            return

        try:
            self.db_manager.delete_packaging_category(item_id)
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się usunąć kategorii: {e}")
            raise
