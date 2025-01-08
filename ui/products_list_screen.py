# c:\serownia\ui\products_list_screen.py

from typing import Optional, Any, List

from PyQt5.QtWidgets import (
    QLineEdit, QTableWidgetItem, QMessageBox, QComboBox, QPushButton
)
from PyQt5.QtCore import Qt

from .base_crud_list_screen import BaseCrudListScreen
from database.db_manager import DBManager


class ProductsListScreen(BaseCrudListScreen):
    """
    Ekran z listą produktów:
      0. ID (zablokowane),
      1. Nazwa produktu (QLineEdit),
      2. Kategoria produktu (QComboBox),
      3. Skład (przycisk prowadzący do ProductCompositionScreen),
      4. Edytuj/Zapisz,
      5. Usuń.

    Obsługuje filtr w load_data(filter_text).
    NIE tworzymy tutaj paska wyszukiwania (QLineEdit + „Szukaj”/„Wyczyść filtr”),
    aby uniknąć dublowania – zakładamy, że już istnieje w kodzie nadrzędnym.
    """

    def __init__(
        self,
        parent: Optional[Any] = None,
        db_manager: Optional[DBManager] = None
    ) -> None:
        """
        Inicjalizuje ekran "Lista Produktów" z kolumnami:
          0) ID
          1) Nazwa
          2) Kategoria
          3) Skład
          4) Edytuj/Zapisz
          5) Usuń

        Nie tworzy pól wyszukiwania, bo korzystamy z paska wyszukiwania w innej części aplikacji.
        """
        print("[DEBUG] ProductsListScreen __init__ start")
        self.db_manager = db_manager
        super().__init__(
            parent=parent,
            title="Lista Produktów",
            columns=[
                "ID",
                "Nazwa produktu",
                "Kategoria",
                "Skład",
                "Edytuj/Zapisz",
                "Usuń"
            ]
        )
        print(f"[DEBUG] ProductsListScreen __init__ done. db_manager={db_manager}")

        # Na start ładujemy wszystkie dane (bez filtra).
        self.load_data()

    def load_data(self, filter_text: str = "") -> None:
        """
        Wypełnia tabelę wierszami z bazy (products).
        Jeśli filter_text nie jest pusty – filtruje listę po nazwie (case-insensitive).
        """
        print(f"[DEBUG] load_data() wywołane z filter_text='{filter_text}'")

        if not self.db_manager:
            print("[DEBUG] Brak db_manager! Nie można załadować produktów.")
            QMessageBox.critical(self, "Błąd", "Brak db_manager – nie można załadować produktów.")
            return

        print("[DEBUG] Pobieram produkty z bazy...")
        self.table.setRowCount(0)

        # 1. Pobierz wszystkie produkty z bazy
        products = self.db_manager.get_all_products()
        print(f"[DEBUG] Pobrano {len(products)} produktów z bazy.")

        # 2. Filtruj po nazwie, jeśli filter_text podany
        if filter_text:
            ft_lower = filter_text.lower()
            before_count = len(products)
            products = [
                p for p in products
                if ft_lower in p["name"].lower()
            ]
            after_count = len(products)
            print(f"[DEBUG] Filtr '{filter_text}' – przed filtrem={before_count}, po filtrem={after_count}")

        # 3. Pobieramy listę kategorii do QComboBox
        print("[DEBUG] Pobieram listę kategorii produktu...")
        product_categories = self.db_manager.get_product_categories()
        cat_dict = {cat["id"]: cat["name"] for cat in product_categories}
        print(f"[DEBUG] Kategorii: {len(cat_dict)}")

        # 4. Wypełnij tabelę
        for row_index, product in enumerate(products):
            self.table.insertRow(row_index)

            # 0: ID (zablokowane)
            prod_id = product["id"]
            id_item = QTableWidgetItem(str(prod_id))
            id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row_index, 0, id_item)

            # 1: Nazwa produktu (QLineEdit, domyślnie disabled)
            name_str = str(product.get("name", ""))
            name_edit = QLineEdit(name_str)
            name_edit.setEnabled(False)
            self.table.setCellWidget(row_index, 1, name_edit)

            # 2: Kategoria (QComboBox, disabled)
            cat_combo = QComboBox()
            cat_combo.setEnabled(False)
            for c_id, c_name in cat_dict.items():
                cat_combo.addItem(c_name, c_id)

            current_cat_id = product.get("category_id", None)
            idx_to_select = 0
            for i in range(cat_combo.count()):
                if cat_combo.itemData(i) == current_cat_id:
                    idx_to_select = i
                    break
            cat_combo.setCurrentIndex(idx_to_select)
            self.table.setCellWidget(row_index, 2, cat_combo)

            # 3: Skład (przycisk -> ProductCompositionScreen)
            composition_button = QPushButton("Skład")
            composition_button.setStyleSheet("""
                background-color: #ADD8E6;
                font-size: 12px;
                border-radius: 8px;
                padding: 5px 10px;
            """)
            composition_button.clicked.connect(lambda _, r=row_index: self.show_composition(r))
            self.table.setCellWidget(row_index, 3, composition_button)

            # 4: Edytuj/Zapisz
            edit_button = self.create_edit_button(row_index)
            self.table.setCellWidget(row_index, 4, edit_button)

            # 5: Usuń
            delete_button = self.create_delete_button(row_index)
            self.table.setCellWidget(row_index, 5, delete_button)

            print(f"[DEBUG] Wstawiono produkt ID={prod_id}, name='{name_str}' do wiersza {row_index}.")

        print(f"[DEBUG] Wstawiono w tabeli {len(products)} wierszy.")
        self.table.resizeColumnsToContents()

    # --------------- Metody CRUD ---------------

    def add_new_item(self) -> None:
        """Obsługa przycisku 'Nowy' (BaseCrudListScreen)."""
        print("[DEBUG] add_new_item() – dodajemy nowy produkt.")
        if not self.db_manager:
            print("[DEBUG] Brak db_manager w add_new_item().")
            QMessageBox.critical(self, "Błąd", "Brak db_manager.")
            return

        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Nowy produkt", "Nazwa produktu:")
        if ok and name.strip():
            category_id = 1  # tymczasowo
            try:
                print(f"[DEBUG] add_new_item(): Dodaję produkt '{name.strip()}', cat_id={category_id}")
                self.db_manager.add_product(name.strip(), category_id)
                QMessageBox.information(self, "Sukces", f"Dodano produkt: {name.strip()}.")
                self.load_data()
            except Exception as e:
                print(f"[DEBUG] Błąd przy add_product: {e}")
                QMessageBox.warning(self, "Błąd", f"Nie udało się dodać produktu: {e}")
        else:
            print("[DEBUG] Użytkownik anulował dodawanie nowego produktu.")

    def show_composition(self, row_index: int) -> None:
        """Po kliknięciu przycisku 'Skład' w kolumnie 3."""
        print(f"[DEBUG] show_composition(row_index={row_index})")
        item_id_item = self.table.item(row_index, 0)
        if not item_id_item:
            print("[DEBUG] Nie znaleziono ID w wierszu.")
            return

        product_id = int(item_id_item.text())
        print(f"[DEBUG] show_composition() product_id={product_id}")

        if hasattr(self.parent, "product_composition_screen"):
            print("[DEBUG] Przełączam widok na product_composition_screen.")
            self.parent.product_composition_screen.set_product_id(product_id)
            self.parent.show_screen(self.parent.product_composition_screen)
        else:
            print("[DEBUG] Brak atrybutu product_composition_screen w parent.")
            QMessageBox.information(
                self,
                "Skład",
                f"Tu otworzymy ProductCompositionScreen dla product_id={product_id}"
            )

    def update_item_in_db(self, item_id: int, new_values: List[Any]) -> None:
        """Wywoływane, gdy user kliknie 'Zapisz' w kolumnie 4."""
        print(f"[DEBUG] update_item_in_db(item_id={item_id}, new_values={new_values})")
        if not self.db_manager:
            print("[DEBUG] Brak db_manager w update_item_in_db.")
            QMessageBox.critical(self, "Błąd", "Brak db_manager.")
            return

        new_name = new_values[0]
        cat_id = new_values[1]

        try:
            print(f"[DEBUG] update_product(item_id={item_id}, new_name='{new_name}', cat_id={cat_id})")
            self.db_manager.update_product(item_id, new_name, cat_id)
            QMessageBox.information(self, "Sukces", f"Zaktualizowano produkt (ID={item_id}).")
            self.load_data()
        except Exception as e:
            print(f"[DEBUG] Błąd przy update_product: {e}")
            QMessageBox.warning(self, "Błąd", f"Nie udało się zapisać: {e}")

    def delete_item_in_db(self, item_id: int) -> None:
        """Usuwa produkt z bazy (po kliknięciu 'Usuń')."""
        print(f"[DEBUG] delete_item_in_db(item_id={item_id})")
        if not self.db_manager:
            print("[DEBUG] Brak db_manager w delete_item_in_db.")
            QMessageBox.critical(self, "Błąd", "Brak db_manager.")
            return

        try:
            print(f"[DEBUG] db_manager.delete_product({item_id})")
            self.db_manager.delete_product(item_id)
            QMessageBox.information(self, "Info", f"Produkt (ID={item_id}) został usunięty.")
            self.load_data()
        except Exception as e:
            print(f"[DEBUG] Błąd przy delete_product: {e}")
            QMessageBox.warning(self, "Błąd", f"Nie udało się usunąć: {e}")
