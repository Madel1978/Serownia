from typing import Optional, List, Dict, Any

from PyQt5.QtWidgets import QTableWidgetItem, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt

# Dostosuj ścieżkę importu do struktury swojego projektu.
from ui.base_list_screen import BaseListScreen


class AdditivesScreen(BaseListScreen):
    """
    Ekran prezentujący listę dodatków (Additives).
    Dziedziczy po BaseListScreen, co zapewnia:
      - tabelę z możliwością sortowania,
      - pasek akcji (Import, Nowy),
      - pasek filtra (Szukaj, Wyczyść filtr).

    Korzysta z db_manager do komunikacji z bazą danych,
    np. poprzez metodę db_manager.get_all_additives().
    """

    def __init__(
        self,
        parent: Optional[Any] = None,  # Najczęściej QMainWindow
        db_manager: Optional[Any] = None,  # Docelowo: Optional[DBManager]
    ) -> None:
        """
        Inicjalizuje ekran 'Lista Dodatków' z kolumnami:
        [ID, Nazwa, Waga, Dawkowanie, Kategoria, Data utworzenia].

        :param parent: Widok-rodzic (najczęściej MainWindow).
        :param db_manager: Obiekt do komunikacji z bazą danych.
        """
        super().__init__(
            parent=parent,
            title="Lista Dodatków",
            columns=[
                "ID",
                "Nazwa",
                "Waga",
                "Dawkowanie",
                "Kategoria",
                "Data utworzenia",
            ],
        )
        self.db_manager = db_manager

    def load_data(self) -> None:
        """
        Pobiera listę dodatków z bazy (db_manager.get_all_additives)
        i wyświetla je w tabeli. Nadpisuje metodę 'load_data' z BaseListScreen.
        """
        self.table.setRowCount(0)

        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można załadować dodatków."
            )
            return

        # Przykładowo, db_manager.get_all_additives() zwraca listę słowników, np.:
        # [
        #   {"id": 1, "name": "Dodatek A", "weight": "100g", "dosage": "10g", "category_id": 2, ...},
        #   ...
        # ]
        additives = self.db_manager.get_all_additives()

        for row_index, additive in enumerate(additives):
            self.table.insertRow(row_index)

            # Kolumna 0: ID
            item_id = QTableWidgetItem(str(additive["id"]))
            # ID zablokowane do edycji (tylko do wyświetlania)
            item_id.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row_index, 0, item_id)

            # Kolumna 1: Nazwa
            item_name = QTableWidgetItem(str(additive["name"]))
            self.table.setItem(row_index, 1, item_name)

            # Kolumna 2: Waga
            item_weight = QTableWidgetItem(str(additive.get("weight", "")))
            self.table.setItem(row_index, 2, item_weight)

            # Kolumna 3: Dawkowanie
            item_dosage = QTableWidgetItem(str(additive.get("dosage", "")))
            self.table.setItem(row_index, 3, item_dosage)

            # Kolumna 4: Kategoria
            # Jeśli potrzebujesz pobrać rzeczywistą nazwę kategorii, użyj metody get_category_name(category_id).
            category_id = additive.get("category_id", None)
            category_name = self.get_category_name(category_id)
            self.table.setItem(row_index, 4, QTableWidgetItem(category_name))

            # Kolumna 5: Data utworzenia (o ile istnieje w bazie)
            created_at = additive.get("created_at", "2024-01-01")
            self.table.setItem(row_index, 5, QTableWidgetItem(str(created_at)))

        self.table.resizeColumnsToContents()

    def get_category_name(self, category_id: Optional[int]) -> str:
        """
        Pomocnicza metoda do zmapowania category_id -> nazwa kategorii.
        Zwraca placeholder, jeśli kategoria nie istnieje.

        :param category_id: ID kategorii z bazy (np. 2).
        :return: Nazwa kategorii (str) lub 'Brak kategorii' (placeholder).
        """
        if not category_id:
            return "Brak kategorii"
        # Przykładowo (odkomentuj i dostosuj do swojej bazy):
        # categories = self.db_manager.get_categories()  # lista słowników: [{"id":..., "name":...}, ...]
        # for cat in categories:
        #     if cat["id"] == category_id:
        #         return cat["name"]
        return f"Kategoria {category_id}"

    def import_data(self) -> None:
        """
        Obsługa przycisku 'Importuj'. Tu możesz zaimplementować
        wczytanie pliku CSV i dodanie nowych rekordów do bazy.
        """
        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można importować."
            )
            return

        file_dialog = QFileDialog(self, "Wybierz plik CSV z dodatkami")
        file_dialog.setNameFilter("Pliki CSV (*.csv)")
        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            # Tu logika wczytania i parsowania pliku CSV,
            # np. db_manager.add_additive(...) w pętli
            # Na koniec odśwież tabelę:
            self.load_data()
        else:
            QMessageBox.information(self, "Import", "Nie wybrano pliku do importu.")

    def add_new_item(self) -> None:
        """
        Obsługa przycisku 'Nowy'. Otwiera okno/dialog do dodawania nowego dodatku
        i po zapisaniu w bazie wywołuje self.load_data().
        """
        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można dodać dodatku."
            )
            return

        QMessageBox.information(
            self, "Nowy dodatek", "Tu otwórz formularz do dodania dodatku."
        )
        # Po zapisaniu w bazie:
        # self.load_data()

    def apply_filter(self) -> None:
        """
        Obsługa przycisku 'Szukaj'.
        Możesz wykonać wyszukiwanie w bazie (SELECT z WHERE name LIKE '%tekst%'),
        albo filtrować w pamięci, jak w tym przykładzie.
        """
        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – filtrowanie niemożliwe."
            )
            return

        filter_text = self.filter_input.text().strip().lower()
        if not filter_text:
            # Jeśli puste, ładujemy wszystko
            self.load_data()
            return

        all_additives = self.db_manager.get_all_additives()
        filtered: List[Dict[str, Any]] = []

        for ad in all_additives:
            # Filtrowanie według nazwy (case-insensitive)
            if filter_text in ad["name"].lower():
                filtered.append(ad)

        self.table.setRowCount(0)
        for row_index, additive in enumerate(filtered):
            self.table.insertRow(row_index)
            self.table.setItem(row_index, 0, QTableWidgetItem(str(additive["id"])))
            self.table.setItem(row_index, 1, QTableWidgetItem(str(additive["name"])))
            self.table.setItem(
                row_index, 2, QTableWidgetItem(str(additive.get("weight", "")))
            )
            self.table.setItem(
                row_index, 3, QTableWidgetItem(str(additive.get("dosage", "")))
            )

            category_id = additive.get("category_id", None)
            self.table.setItem(
                row_index, 4, QTableWidgetItem(self.get_category_name(category_id))
            )

            created_at = additive.get("created_at", "2024-01-01")
            self.table.setItem(row_index, 5, QTableWidgetItem(str(created_at)))

        self.table.resizeColumnsToContents()
