# c:\serownia\ui\product_categories_crud_screen.py

from typing import Optional, Any, List
import sqlite3  # Możliwe, że używasz do łapania IntegrityError

from PyQt5.QtWidgets import (
    QLineEdit, QTableWidgetItem, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt

from ui.base_crud_list_screen import BaseCrudListScreen
# Jeśli plik jest inaczej zorganizowany, dostosuj ścieżkę powyżej.


class ProductCategoriesCrudScreen(BaseCrudListScreen):
    """
    Ekran z listą kategorii produktów (CRUD):
      - Dodawanie nowej kategorii (przycisk 'Nowy'),
      - Edycja nazwy kategorii (Edytuj/Zapisz),
      - Usuwanie (Usuń).

    Obsługuje argument filter_text w load_data(filter_text="..."),
    aby klasa bazowa mogła wywoływać self.load_data(filter_text="...") przy filtracji.
    """

    def __init__(
        self,
        parent: Optional[Any] = None,
        db_manager: Optional[Any] = None
    ) -> None:
        """
        Definiujemy kolumny: [ID, Nazwa kategorii produktów, Edytuj/Zapisz, Usuń].
        """
        self.db_manager = db_manager
        super().__init__(
            parent=parent,
            title="Kategorie Produktów (CRUD)",
            columns=["ID", "Nazwa kategorii produktów", "Edytuj/Zapisz", "Usuń"]
        )

    def load_data(self, filter_text: str = "") -> None:
        """
        Pobiera listę kategorii produktów z bazy i wypełnia tabelę.
        Jeśli filter_text niepuste, filtrujemy np. po 'name' (case-insensitive).

        columns = [0=ID, 1=Nazwa, 2=Edytuj/Zapisz, 3=Usuń]
        """
        print(f"[DEBUG] ProductCategoriesCrudScreen.load_data(filter_text='{filter_text}')")

        if not self.db_manager:
            QMessageBox.critical(self, "Błąd", "Brak db_manager.")
            return

        self.table.setRowCount(0)

        # 1. Pobieramy wszystkie kategorie
        categories = self.db_manager.get_product_categories()  # np. [{"id": 1, "name": "..."}]

        # 2. Filtrowanie w Pythonie (opcjonalnie)
        ft_lower = filter_text.strip().lower()
        if ft_lower:
            categories = [
                cat for cat in categories
                if ft_lower in cat["name"].lower()
            ]

        print(f"[DEBUG] Znaleziono {len(categories)} kategorii (po filtrze='{filter_text}')")

        # 3. Wstawiamy do tabeli
        for row_index, cat in enumerate(categories):
            self.table.insertRow(row_index)

            # Kol 0: ID
            id_item = QTableWidgetItem(str(cat["id"]))
            id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row_index, 0, id_item)

            # Kol 1: Nazwa kategorii
            name_edit = QLineEdit(cat["name"])
            name_edit.setEnabled(False)  # Domyślnie tylko do odczytu, odblokujemy przy "Edytuj"
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
        nowej kategorii produktów.
        """
        if not self.db_manager:
            QMessageBox.critical(self, "Błąd", "Brak db_manager.")
            return

        name, ok = QInputDialog.getText(
            self,
            "Dodaj kategorię produktów",
            "Nazwa nowej kategorii:"
        )
        if ok and name.strip():
            try:
                self.db_manager.add_product_category(name.strip())
                QMessageBox.information(self, "Sukces", f"Dodano kategorię: {name.strip()}")
                self.load_data()

            except sqlite3.IntegrityError:
                # Jeśli w bazie mamy klucz UNIQUE na kolumnie name,
                # przy próbie dodania duplikatu pojawia się IntegrityError
                QMessageBox.warning(
                    self,
                    "Błąd",
                    f"Kategoria '{name.strip()}' już istnieje w bazie!"
                )

            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Błąd",
                    f"Nie udało się dodać kategorii: {e}"
                )

    def update_item_in_db(self, item_id: int, new_values: List[Any]) -> None:
        """
        Zapisywanie zmienionej nazwy kategorii (1 kolumna: nazwa).

        :param item_id: ID kategorii produktów.
        :param new_values: [nazwa_kategorii].
        """
        if not self.db_manager:
            QMessageBox.critical(self, "Błąd", "Brak db_manager.")
            return

        new_name = new_values[0] if len(new_values) > 0 else ""

        try:
            self.db_manager.update_product_category(item_id, new_name)
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Błąd", f"Kategoria '{new_name}' już istnieje w bazie!")
            raise  # Możesz pominąć raise, jeśli wystarczy sam komunikat
        except Exception as e:
            QMessageBox.warning(
                self,
                "Błąd",
                f"Nie udało się zaktualizować kategorii: {e}"
            )
            raise

    def delete_item_in_db(self, item_id: int) -> None:
        """
        Usuwa kategorię produktów z bazy.

        :param item_id: ID kategorii w tabeli product_categories.
        """
        if not self.db_manager:
            QMessageBox.critical(self, "Błąd", "Brak db_manager.")
            return

        try:
            self.db_manager.delete_product_category(item_id)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Błąd",
                f"Nie udało się usunąć kategorii: {e}"
            )
            raise
