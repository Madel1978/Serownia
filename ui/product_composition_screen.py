from typing import Optional, Any, List
from PyQt5.QtWidgets import (
    QLineEdit, QComboBox, QTableWidgetItem, QMessageBox, QDialog
)
from PyQt5.QtCore import Qt

# Zależnie od struktury projektu:
from .base_crud_list_screen import BaseCrudListScreen
from database.db_manager import DBManager

# Import dialogu do dodania składnika:
from .add_product_additive_dialog import AddProductAdditiveDialog


class ProductCompositionScreen(BaseCrudListScreen):
    """
    Ekran do zarządzania składem konkretnego produktu,
    czyli listą dodatków (z tabeli additives) oraz dawką na 100L (dosage_per_100)
    przechowywaną w tabeli product_additives.

    Kolumny:
      0) ID (z product_additives),
      1) Dodatek (QComboBox),
      2) Dawka/100L (QLineEdit),
      3) Edytuj/Zapisz,
      4) Usuń.
    """

    def __init__(
        self,
        parent: Optional[Any] = None,
        db_manager: Optional[DBManager] = None
    ) -> None:
        """
        Konstruktor ekranu zarządzania składem produktu. 
        Najpierw ustawiamy db_manager i current_product_id,
        potem wywołujemy konstruktor klasy bazowej, 
        który z kolei uruchamia load_data() (jeśli to zaprogramowano).
        """
        self.db_manager = db_manager
        self.current_product_id: Optional[int] = None

        super().__init__(
            parent=parent,
            title="Skład produktu",
            columns=["ID", "Kategoria", "Dodatek", "Dawka/100L", "Edytuj/Zapisz", "Usuń"]
        )

    def set_product_id(self, product_id: int) -> None:
        """
        Ustawia ID produktu, dla którego chcemy wyświetlać i edytować skład (product_additives).
        Następnie wczytuje dane z bazy.
        """
        self.current_product_id = product_id
        self.load_data()

    def load_data(self) -> None:
        if not self.db_manager or not self.current_product_id:
            return

        self.table.setRowCount(0)

        # Pobierz wiersze z product_additives
        comp_list = self.db_manager.get_product_additives(self.current_product_id)
        # Pobierz listę wszystkich dodatków, by mieć name oraz category_id
        all_additives = self.db_manager.get_all_additives()

        # Słownik do szybkiego wyszukiwania: additive_id -> (additive_name, category_id)
        additives_dict = {}
        for ad in all_additives:
            add_id = ad["id"]
            add_name = ad["name"]
            cat_id = ad["category_id"]
            additives_dict[add_id] = (add_name, cat_id)

        # Pobierz listę wszystkich kategorii dodatków, by mieć category_id -> category_name
        cat_list = self.db_manager.get_additive_categories()  # np. SELECT * FROM additive_categories
        cat_dict = {}
        for c in cat_list:
            cat_dict[c["id"]] = c["name"]

        for row_index, row_data in enumerate(comp_list):
            self.table.insertRow(row_index)

            # kol.0: ID (z product_additives)
            pa_id_item = QTableWidgetItem(str(row_data["id"]))
            pa_id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row_index, 0, pa_id_item)

            # kol.1: Kategoria (QLineEdit read-only – bo wybiera się przez Dodatek)
            cat_edit = QLineEdit()
            cat_edit.setEnabled(False)

            # kol.2: Dodatek (QComboBox, disabled)
            add_combo = QComboBox()
            add_combo.setEnabled(False)

            current_add_id = row_data["additive_id"]
            # ustalamy name i category_id
            if current_add_id in additives_dict:
                add_name, c_id = additives_dict[current_add_id]
                # Wpisz do cat_edit
                cat_name = cat_dict.get(c_id, "(brak)")
                cat_edit.setText(cat_name)
            else:
                add_name = ""
                cat_edit.setText("")

            # Uzupełniamy QComboBox (wszystkie dodatki) – jak dotychczas
            for ad in all_additives:
                add_combo.addItem(ad["name"], ad["id"])

            # Ustawiamy currentIndex do tego `current_add_id`
            idx = 0
            for i in range(add_combo.count()):
                if add_combo.itemData(i) == current_add_id:
                    idx = i
                    break
            add_combo.setCurrentIndex(idx)

            self.table.setCellWidget(row_index, 1, cat_edit)    # kol.1
            self.table.setCellWidget(row_index, 2, add_combo)   # kol.2

            # kol.3: Dawka/100L
            dosage_edit = QLineEdit(str(row_data.get("dosage_per_100", "")))
            dosage_edit.setEnabled(False)
            self.table.setCellWidget(row_index, 3, dosage_edit)

            # kol.4: Edytuj/Zapisz
            edit_btn = self.create_edit_button(row_index)
            self.table.setCellWidget(row_index, 4, edit_btn)

            # kol.5: Usuń
            del_btn = self.create_delete_button(row_index)
            self.table.setCellWidget(row_index, 5, del_btn)

        self.table.resizeColumnsToContents()


    def add_new_item(self) -> None:
        """
        Obsługa przycisku 'Nowy' (z paska narzędzi w BaseCrudListScreen).
        Dodaje kolejny wiersz w product_additives dla aktualnego produktu.
        """
        if not self.db_manager or not self.current_product_id:
            QMessageBox.warning(self, "Błąd", "Brak db_manager lub nieustawiony product_id.")
            return

        # Otwieramy dialog 'AddProductAdditiveDialog':
        dialog = AddProductAdditiveDialog(self, self.db_manager, self.current_product_id)
        if dialog.exec_() == QDialog.Accepted:
            # Po kliknięciu "Zapisz" w dialogu, odśwież tabelę:
            self.load_data()
        else:
            QMessageBox.information(
                self,
                "Nowy składnik",
                "Anulowano dodawanie składnika."
            )

    def update_item_in_db(self, pa_id: int, new_values: List[Any]) -> None:
        """
        Zapisuje zmiany w wierszu product_additives (rekord o ID=pa_id).
        new_values -> [additive_id, dosage_per_100].
        """
        if not self.db_manager:
            QMessageBox.warning(self, "Błąd", "Brak db_manager.")
            return

        if len(new_values) < 2:
            QMessageBox.warning(self, "Błąd", "Brak wystarczającej liczby wartości do aktualizacji.")
            return

        new_add_id = new_values[0]   # ID dodatku
        new_dosage = new_values[1]   # np. '17 ml' lub '30 g'

        try:
            # Przykładowa metoda w db_manager,
            # która aktualizuje zarówno additive_id, jak i dosage_per_100 w product_additives:
            self.db_manager.update_product_additive_full(pa_id, new_add_id, new_dosage)

        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się zapisać: {e}")
            raise

    def delete_item_in_db(self, pa_id: int) -> None:
        """
        Usuwa wiersz z product_additives (ID=pa_id).
        """
        if not self.db_manager:
            QMessageBox.warning(self, "Błąd", "Brak db_manager.")
            return

        try:
            self.db_manager.delete_product_additive(pa_id)
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się usunąć składnika: {e}")
            raise

    def save_changes(self, row: int) -> None:
        """
        Nadpisuje metodę z BaseCrudListScreen. 
        W kolumnie 1 jest QComboBox (dodatek), 
        w kolumnie 2 jest QLineEdit (dosage_per_100).
        """
        pa_id_item = self.table.item(row, 0)
        if not pa_id_item:
            return

        pa_id = int(pa_id_item.text())
        new_values: List[Any] = []

        # Odczytujemy QComboBox i QLineEdit w kolumnach 1 i 2
        for col in range(1, len(self.columns) - 2):
            widget = self.table.cellWidget(row, col)
            if col == 1 and isinstance(widget, QComboBox):
                add_id = widget.itemData(widget.currentIndex())
                new_values.append(add_id)
            elif col == 2 and isinstance(widget, QLineEdit):
                dosage = widget.text().strip()
                new_values.append(dosage)

        try:
            # Faktyczny zapis w bazie:
            self.update_item_in_db(pa_id, new_values)

            # Komunikat i odświeżenie widoku:
            QMessageBox.information(self, "Sukces", "Zaktualizowano rekord w bazie.")
            self.load_data()

        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się zapisać: {e}")

        # Przywracamy przycisk „Zapisz” na „Edytuj”
        self.enable_row_edit(row, False)
        edit_col_index = len(self.columns) - 2
        edit_button = self.table.cellWidget(row, edit_col_index)
        if edit_button:
            edit_button.setText("Edytuj")
