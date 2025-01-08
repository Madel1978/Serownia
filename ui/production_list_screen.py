from typing import Optional, Any, List, Dict
from PyQt5.QtWidgets import (
    QLineEdit, QTableWidgetItem, QMessageBox, QPushButton
)
from PyQt5.QtCore import Qt, QEvent

from ui.base_crud_list_screen import BaseCrudListScreen
from database.db_manager import DBManager

class ProductionListScreen(BaseCrudListScreen):
    """
    Ekran „Baza Produkcji” (lista protokołów w production_records).
    Funkcjonalność:
      - Filtrowanie po numerze serii,
      - Przycisk „Otwórz/Edytuj” do przejścia w protokół (z możliwością edycji),
      - Przycisk „Usuń” do kasowania protokołu,
      - Brak przycisków „Importuj” i „Nowy” (ukryte).
    """

    def __init__(
        self,
        parent: Optional[Any] = None,
        db_manager: Optional[DBManager] = None
    ) -> None:
        print(">>> ProductionListScreen: constructor START")
        self.db_manager = db_manager

        super().__init__(
            parent=parent,
            title="Baza Produkcji (lista protokołów)",
            columns=[
                "ID",
                "Data produkcji",
                "Numer serii",
                "Produkt",
                "Otwórz / Edytuj",
                "Usuń"
            ]
        )
        self.hide_import_and_new_buttons()
        print(">>> ProductionListScreen: constructor END")

    def create_toolbar_buttons(self) -> None:
        """
        Nadpisujemy, aby NIE tworzyć przycisków „Importuj” i „Nowy”.
        """
        print(">>> ProductionListScreen: create_toolbar_buttons => brak przycisków Importuj/Nowy.")

    def showEvent(self, event: QEvent) -> None:
        super().showEvent(event)
        print(">>> ProductionListScreen.showEvent => load_data_with_filter('')")
        self.load_data_with_filter("")

    def apply_filter(self) -> None:
        """
        Nadpisujemy metodę z BaseListScreen, aby filtr dotyczył samej 'ProductionListScreen'.
        """
        if not self.db_manager:
            QMessageBox.warning(self, "Błąd", "Brak db_manager.")
            return

        # Pobieramy tekst z self.filter_input
        if hasattr(self, "filter_input") and self.filter_input is not None:
            text = self.filter_input.text().strip()
            print(f"[DEBUG] ProductionListScreen.apply_filter: filter_text='{text}'")
            self.load_data_with_filter(text)
        else:
            self.load_data_with_filter("")

    def load_data_with_filter(self, filter_text: str) -> None:
        """
        Ładuje protokoły z uwzględnieniem filtra (numer serii).
        """
        print(">>> ProductionListScreen.load_data_with_filter() START")
        if not self.db_manager:
            QMessageBox.warning(self, "Błąd", "Brak db_manager – nie można załadować protokołów.")
            return

        self.table.setRowCount(0)
        ft_lower = filter_text.lower().strip()
        print(f"    filter_text='{ft_lower}'")

        productions = self.get_productions_joined(ft_lower)
        print(f"    Znaleziono {len(productions)} rekordów w production_records.")

        for row_index, rec in enumerate(productions):
            self.table.insertRow(row_index)

            # Kol.0: ID
            id_item = QTableWidgetItem(str(rec["id"]))
            id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row_index, 0, id_item)

            # Kol.1: Data produkcji
            date_item = QTableWidgetItem(rec["date"] or "")
            date_item.setFlags(date_item.flags() ^ Qt.ItemIsEditable)
            self.table.setItem(row_index, 1, date_item)

            # Kol.2: Numer serii
            series_item = QTableWidgetItem(rec["series"] or "")
            series_item.setFlags(series_item.flags() ^ Qt.ItemIsEditable)
            self.table.setItem(row_index, 2, series_item)

            # Kol.3: Nazwa produktu
            product_item = QTableWidgetItem(rec["product_name"] or "")
            product_item.setFlags(product_item.flags() ^ Qt.ItemIsEditable)
            self.table.setItem(row_index, 3, product_item)

            # Kol.4: Otwórz / Edytuj (przycisk)
            open_edit_btn = self.create_open_edit_button(row_index)
            self.table.setCellWidget(row_index, 4, open_edit_btn)

            # Kol.5: Usuń (przycisk)
            delete_btn = self.create_delete_button(row_index)
            self.table.setCellWidget(row_index, 5, delete_btn)

        self.table.resizeColumnsToContents()
        print(">>> ProductionListScreen.load_data_with_filter() END")

    def get_productions_joined(self, filter_text: str) -> List[Dict[str, Any]]:
        """
        Pobiera listę protokołów (production_records + dołączona nazwa produktu).
        Jeśli filter_text != "", filtruje po numerze serii (case-insensitive).
        """
        if not self.db_manager:
            return []
        with self.db_manager.create_connection() as conn:
            cursor = conn.cursor()
            if filter_text:
                sql = """
                  SELECT pr.id, pr.date, pr.series, pr.product_id, p.name AS product_name
                  FROM production_records pr
                  LEFT JOIN products p ON pr.product_id = p.id
                  WHERE LOWER(pr.series) LIKE :f
                     OR LOWER(p.name)  LIKE :f
                  ORDER BY pr.id
                """
                cursor.execute(sql, {"f": f"%{filter_text.lower()}%"})
            else:
                sql = """
                  SELECT pr.id, pr.date, pr.series, pr.product_id, p.name AS product_name
                  FROM production_records pr
                  LEFT JOIN products p ON pr.product_id = p.id
                  ORDER BY pr.id
                """
                cursor.execute(sql)
            rows = cursor.fetchall()
            results = []
            for row in rows:
                results.append({
                    "id": row[0],
                    "date": row[1],
                    "series": row[2],
                    "product_id": row[3],
                    "product_name": row[4],
                })
            return results

    def create_open_edit_button(self, row_index: int) -> QPushButton:
        btn = QPushButton("Otwórz / Edytuj")
        btn.setStyleSheet("""
            background-color: #ADD8E6;
            font-size: 12px;
            border-radius: 8px;
            padding: 5px 10px;
        """)
        btn.clicked.connect(lambda _: self.open_edit_protocol(row_index))
        return btn

    def open_edit_protocol(self, row_index: int) -> None:
        """
        Obsługa przycisku „Otwórz/Edytuj”.
        Pobieramy ID protokołu z tabeli. Sprawdzamy kategorię produktu i 
        sięgamy do parent's protocol_screens_by_name[cat_name], 
        tak jak w new_production_screen, zamiast if-else.
        """
        print(f">>> open_edit_protocol(row_index={row_index})")

        id_item = self.table.item(row_index, 0)
        if not id_item:
            return
        record_id = int(id_item.text())
        print(f"    record_id={record_id}")

        # Pobierz production_record + product_id
        record_data = self.get_production_record_by_id(record_id)
        if not record_data:
            QMessageBox.warning(self, "Błąd", f"Nie znaleziono protokołu o ID={record_id}.")
            return

        product_id = record_data.get("product_id", None)
        if not product_id:
            QMessageBox.warning(self, "Błąd", f"Protokół ID={record_id} nie ma product_id.")
            return

        product_info = self.db_manager.get_product_by_id(product_id)
        if not product_info:
            QMessageBox.warning(
                self, "Uwaga",
                f"Produkt o ID={product_id} nie istnieje w bazie. Ustawiam pierwszy z listy."
            )
            return

        # Ustal nazwę kategorii
        cat_id = product_info.get("category_id", None)
        cat_name = ""
        for c in self.db_manager.get_product_categories():
            if c["id"] == cat_id:
                cat_name = c["name"]
                break

        cat_name_str = cat_name.strip()
        print(f"    product_id={product_id}, cat_name='{cat_name_str}'")

        # Teraz zamiast if cat_name_lower == "ser": ... => sięgamy do protocol_screens_by_name
        if not hasattr(self.parent, "protocol_screens_by_name"):
            QMessageBox.information(
                self,
                "Brak ekranu",
                "MainWindow nie ma słownika 'protocol_screens_by_name'."
            )
            return

        proto_dict = self.parent.protocol_screens_by_name
        if cat_name_str in proto_dict:
            protocol_screen = proto_dict[cat_name_str]
        else:
            QMessageBox.information(
                self,
                "Brak ekranu",
                f"Nie zaimplementowano protokołu dla kategorii '{cat_name_str}'."
            )
            return

        # Wczytujemy do protokołu:
        if not hasattr(protocol_screen, "load_from_record"):
            QMessageBox.warning(
                self,
                "Błąd",
                f"Ekran protokołu nie ma metody 'load_from_record'."
            )
            return

        protocol_screen.load_from_record(record_data)
        self.parent.show_screen(protocol_screen)

    def get_production_record_by_id(self, record_id: int) -> Optional[dict]:
        """
        Pobiera z production_records (i ewent. zwraca dict z id, date, series, product_id).
        """
        if not self.db_manager:
            return None
        with self.db_manager.create_connection() as conn:
            cursor = conn.cursor()
            sql = """
              SELECT id, date, series, product_id
              FROM production_records
              WHERE id = ?
            """
            cursor.execute(sql, (record_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "date": row[1],
                    "series": row[2],
                    "product_id": row[3],
                }
            return None

    def add_new_item(self) -> None:
        """
        Nadpisujemy, bo w ProductionListScreen jest ukryty przycisk.
        """
        print(">>> add_new_item => nieużywane w ProductionListScreen (ukryte).")

    def import_items(self) -> None:
        print(">>> import_items => nieużywane w ProductionListScreen (ukryte).")

    def delete_item_in_db(self, item_id: int) -> None:
        """
        Usuwanie protokołu (kasuje w production_records i ewentualnie child-tabele).
        Jeśli w bazie jest ON DELETE CASCADE, wystarczy usunąć z production_records.
        """
        print(f">>> delete_item_in_db item_id={item_id}")
        if not self.db_manager:
            QMessageBox.warning(self, "Błąd", "Brak db_manager.")
            return

        reply = QMessageBox.question(
            self,
            "Potwierdzenie usunięcia",
            f"Czy na pewno chcesz USUNĄĆ protokół (ID={item_id})?\nOperacja nieodwracalna!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        try:
            with self.db_manager.create_connection() as conn:
                cursor = conn.cursor()

                # usuwamy protokół w production_records
                sql = "DELETE FROM production_records WHERE id = ?"
                cursor.execute(sql, (item_id,))

                conn.commit()

            QMessageBox.information(self, "Info", f"Protokół (ID={item_id}) został usunięty.")
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się usunąć protokołu: {e}")
            
    def clear_filter(self) -> None:
        """
        Nadpisujemy, bo chcemy wczytać CAŁĄ listę protokołów (bez filtra).
        """
        if hasattr(self, "filter_input"):
            self.filter_input.clear()
        print(">>> ProductionListScreen.clear_filter => load_data_with_filter('')")
        # Odtąd bez filtra
        self.load_data_with_filter("")
