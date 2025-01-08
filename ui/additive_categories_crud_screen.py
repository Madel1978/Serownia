# c:\serownia\ui\additive_categories_crud_screen.py

from typing import Optional, Any, List
import sqlite3  # Możliwe, że używasz do łapania IntegrityError

from PyQt5.QtWidgets import (
    QLineEdit, QTableWidgetItem, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt

from ui.base_crud_list_screen import BaseCrudListScreen


class AdditiveCategoriesCrudScreen(BaseCrudListScreen):
    """
    Ekran z listą kategorii dodatków, z możliwością:
      - dodania nowej kategorii (przycisk "Nowy"),
      - edycji nazwy (Edytuj/Zapisz),
      - usunięcia danej kategorii (Usuń).

    Obsługuje argument filter_text w load_data(filter_text="..."),
    aby klasa bazowa mogła wywołać self.load_data(filter_text="cos") przy filtracji.
    """

    def __init__(
        self,
        parent: Optional[Any] = None,   # najczęściej QMainWindow
        db_manager: Optional[Any] = None  # docelowo: DBManager
    ) -> None:
        """
        Ustawiamy kolumny: [ID, Nazwa kategorii, Edytuj/Zapisz, Usuń].
        """
        self.db_manager = db_manager
        super().__init__(
            parent=parent,
            title="Kategorie Dodatków (CRUD)",
            columns=["ID", "Nazwa kategorii", "Edytuj/Zapisz", "Usuń"]
        )

    def load_data(self, filter_text: str = "") -> None:
        """
        Pobiera listę kategorii z bazy (np. db_manager.get_categories())
        i wypełnia tabelę. Jeśli filter_text niepuste, filtruje listę
        w Pythonie, sprawdzając wystąpienie w 'name'.

        Kolumny:
         - 0: ID (zablokowany)
         - 1: Nazwa (QLineEdit, disabled)
         - 2: Edytuj/Zapisz (przycisk)
         - 3: Usuń (przycisk)
        """
        print(f"[DEBUG] AdditiveCategoriesCrudScreen.load_data(filter_text='{filter_text}')")

        if not self.db_manager:
            QMessageBox.critical(self, "Błąd", "Brak db_manager.")
            return

        self.table.setRowCount(0)

        # 1. Pobieramy wszystkie kategorie dodatków
        categories = self.db_manager.get_categories()  # np. [{"id":1, "name":"Kultury starterowe"}, ...]

        # 2. (Opcjonalne) filtrowanie w Pythonie
        ft_lower = filter_text.strip().lower()
        if ft_lower:
            categories = [
                c for c in categories
                if ft_lower in c["name"].lower()
            ]

        print(f"[DEBUG] Znaleziono {len(categories)} kategorii (po filtrze='{filter_text}')")

        # 3. Wstawiamy dane do tabeli
        for row_index, cat in enumerate(categories):
            self.table.insertRow(row_index)

            # Kol 0: ID
            id_item = QTableWidgetItem(str(cat["id"]))
            id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row_index, 0, id_item)

            # Kol 1: Nazwa (QLineEdit, disabled)
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
        Obsługa przycisku 'Nowy' z paska narzędzi BaseCrudListScreen.
        Otwieramy np. QInputDialog, żeby wprowadzić nazwę nowej kategorii.
        """
        if not self.db_manager:
            QMessageBox.critical(self, "Błąd", "Brak db_manager.")
            return

        name, ok = QInputDialog.getText(
            self,
            "Dodaj kategorię",
            "Nazwa nowej kategorii dodatków:"
        )
        if ok and name.strip():
            try:
                # W db_manager może być np. add_category() dla kategorii dodatków
                self.db_manager.add_category(name.strip())
                QMessageBox.information(self, "Sukces", f"Dodano kategorię: {name.strip()}")
                self.load_data()
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Błąd",
                    f"Nie udało się dodać kategorii: {e}"
                )

    def update_item_in_db(self, item_id: int, new_values: List[Any]) -> None:
        """
        Gdy użytkownik kliknie 'Zapisz', BaseCrudListScreen wywołuje tę metodę.
        new_values -> [nazwa_kategorii].
        """
        if not self.db_manager:
            QMessageBox.critical(self, "Błąd", "Brak db_manager.")
            return

        new_name = new_values[0] if len(new_values) > 0 else ""

        try:
            # W db_manager pewnie jest update_category(item_id, new_name)
            self.db_manager.update_category(item_id, new_name)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Błąd",
                f"Nie udało się zaktualizować kategorii: {e}"
            )
            raise

    def delete_item_in_db(self, item_id: int) -> None:
        """
        Usunięcie kategorii z bazy. Wywołane z BaseCrudListScreen (delete_record).
        """
        if not self.db_manager:
            QMessageBox.critical(self, "Błąd", "Brak db_manager.")
            return

        try:
            # W db_manager: np. delete_category(item_id)
            self.db_manager.delete_category(item_id)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Błąd",
                f"Nie udało się usunąć kategorii: {e}"
            )
            raise
