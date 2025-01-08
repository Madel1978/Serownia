from typing import Optional, Any, List, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QComboBox, QMessageBox, QScrollArea
)
from PyQt5.QtCore import Qt
from datetime import date

from database.db_manager import DBManager  # zakładamy, że masz klasę DBManager


def parse_dosage(dosage_str: str) -> Tuple[float, str]:
    """
    Rozdziela tekst w stylu "30 g", "17 ml", "10" itp. na (wartość float, jednostka).
    Np. "100.5 g" -> (100.5, "g"), "3,7 ml" -> (3.7, "ml"), "17" -> (17.0, "")
    """
    parts = dosage_str.split()
    if len(parts) == 1:
        try:
            val = float(parts[0].replace(',', '.'))
        except ValueError:
            val = 0.0
        return val, ""
    elif len(parts) >= 2:
        try:
            val = float(parts[0].replace(',', '.'))
        except ValueError:
            val = 0.0
        unit = parts[1]
        return val, unit
    else:
        return 0.0, ""


class FermentedProductionProtocolScreen(QWidget):
    """
    Formularz protokołu produkcji "Napoje fermentowane" z obsługą:
      - load_from_record(record_data): wczytywanie danych z bazowych tablic
      - generowanie numeru serii,
      - sekcje: A (parametry), B (6 wierszy dodatków), C (4 czynności),
      - sekcję D (ewidencja partii) – 15 wierszy,
      - zapisywanie danych do bazy (production_records + fermented_production_details
        albo – jeśli używasz jednej wspólnej tabeli – do tamtej).
    """

    def __init__(
        self,
        parent: Optional[Any] = None,
        db_manager: Optional[DBManager] = None
    ):
        super().__init__(parent)
        print(
            ">>> FermentedProductionProtocolScreen - constructor called!",
            "isVisible=", self.isVisible()
        )
        self.parent = parent
        self.db_manager = db_manager

        self.setWindowTitle("Protokół Produkcji (Napoje fermentowane)")
        self.resize(800, 600)

        # Ustawiamy pastelowy styl (identyczny jak w protokole sera).
        self.setStyleSheet("""
            QWidget {
                background-color: #FFF9FA; /* bardzo jasny róż */
            }
            QGroupBox {
                background-color: #FFEFF2;
                border: 1px solid #FFC0CB;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 4px;
                color: #D02090;
                font-weight: bold;
            }
            QLabel {
                font-size: 14px;
                color: #333333;
            }
            QLineEdit, QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #FFB6C1;
                border-radius: 4px;
                padding: 2px 4px;
            }
            QPushButton {
                background-color: #FFB6C1;
                border: 1px solid #FF69B4;
                border-radius: 8px;
                padding: 6px 12px;
                font-weight: bold;
            }
        """)

        # Atrybut do przechowania aktualnie edytowanego protokołu (None => nowy)
        self.current_protocol_id: Optional[int] = None

        # ScrollArea + główny layout
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)

        # Sekcje
        self.create_section_a_params()
        self.create_section_b_additives()
        self.create_section_c_stages_fermented()
        self.create_section_d_parties()
        self.create_bottom_buttons()

        self.scroll_area.setWidget(self.main_widget)
        outer_layout = QVBoxLayout()
        outer_layout.addWidget(self.scroll_area)
        self.setLayout(outer_layout)

        print(">>> FermentedProductionProtocolScreen constructor END")

    # ----------------------------------------------------------------
    # A. PARAMETRY (filtrujemy produkty na "Napoje fermentowane")
    # ----------------------------------------------------------------
    def create_section_a_params(self):
        group = QGroupBox("Parametry wstępne")
        grid = QGridLayout()
        grid.setHorizontalSpacing(40)

        label_width = 195
        field_width = 195

        # 1) Nazwa produktu (Napój ferm.)
        lbl_prod = QLabel("Nazwa produktu (Napój ferm.):")
        lbl_prod.setFixedWidth(label_width)
        self.product_combo = QComboBox()
        self.product_combo.setFixedWidth(field_width)
        grid.addWidget(lbl_prod, 0, 0)
        grid.addWidget(self.product_combo, 0, 1)

        # 2) Data produkcji
        lbl_date = QLabel("Data produkcji (YYYY-MM-DD):")
        lbl_date.setFixedWidth(label_width)
        self.date_input = QLineEdit()
        self.date_input.setFixedWidth(field_width)
        grid.addWidget(lbl_date, 1, 0)
        grid.addWidget(self.date_input, 1, 1)

        # 3) Numer serii
        lbl_series = QLabel("Numer serii (xxxyy_zz):")
        lbl_series.setFixedWidth(label_width)
        self.series_input = QLineEdit()
        self.series_input.setFixedWidth(field_width)
        grid.addWidget(lbl_series, 2, 0)
        grid.addWidget(self.series_input, 2, 1)

        # 4) Rodzaj mleka (identycznie jak w protokole sera)
        lbl_milk_type = QLabel("Rodzaj mleka:")
        lbl_milk_type.setFixedWidth(label_width)
        self.milkType_combo = QComboBox()
        self.milkType_combo.addItems(["Krowie", "Owcze", "Kozie"])
        self.milkType_combo.setFixedWidth(field_width)
        grid.addWidget(lbl_milk_type, 3, 0)
        grid.addWidget(self.milkType_combo, 3, 1)

        # 5) Ilość surowca (litry)
        lbl_amt = QLabel("Ilość surowca (litry):")
        lbl_amt.setFixedWidth(label_width)
        self.milkAmount_input = QLineEdit()
        self.milkAmount_input.setFixedWidth(field_width)
        self.milkAmount_input.setPlaceholderText("np. 50.0")

        # Kluczowy fragment – podpinamy textChanged do update_doses:
        self.milkAmount_input.textChanged.connect(self.update_doses)

        grid.addWidget(lbl_amt, 4, 0)
        grid.addWidget(self.milkAmount_input, 4, 1)

        # 6) pH
        lbl_ph = QLabel("pH (x,xx):")
        lbl_ph.setFixedWidth(label_width)
        self.ph_input = QLineEdit()
        self.ph_input.setFixedWidth(field_width)
        grid.addWidget(lbl_ph, 5, 0)
        grid.addWidget(self.ph_input, 5, 1)

        # 7) Pasteryzacja / obróbka wstępna
        lbl_pasteur = QLabel("Obróbka wstępna (pasteryzacja):")
        lbl_pasteur.setFixedWidth(label_width)
        self.pasteur_combo = QComboBox()
        self.pasteur_combo.addItems(["Brak", "65°C/30min", "85°C/10min"])
        self.pasteur_combo.setFixedWidth(field_width)
        grid.addWidget(lbl_pasteur, 6, 0)
        grid.addWidget(self.pasteur_combo, 6, 1)

        group.setLayout(grid)
        self.main_layout.addWidget(group)

        # Tutaj wypełniamy listę produktów, np. tylko te z kategorii "Napoje fermentowane":
        self.fill_fermented_products()



    def fill_fermented_products(self):
        """
        Wypełnia product_combo WYŁĄCZNIE produktami o kategorii "Napoje fermentowane".
        """
        if not self.db_manager:
            return

        try:
            self.product_combo.currentIndexChanged.disconnect(self.on_product_changed)
        except TypeError:
            pass

        self.product_combo.clear()
        self.product_combo.addItem("Wybierz...", -1)

        products = self.db_manager.get_all_products()
        for p in products:
            cat_id = p.get("category_id")
            cat_name = self.get_category_name_by_id(cat_id)
            if cat_name.lower() == "napoje fermentowane":
                self.product_combo.addItem(p["name"], p["id"])

        self.product_combo.setCurrentIndex(0)
        self.product_combo.setEnabled(True)
        self.product_combo.currentIndexChanged.connect(self.on_product_changed)

    def get_category_name_by_id(self, cat_id: int) -> str:
        """
        Zwraca nazwę kategorii produktu (np. 'Napoje fermentowane') na podstawie cat_id.
        """
        if not self.db_manager:
            return ""
        all_prod_cats = self.db_manager.get_product_categories()
        for c in all_prod_cats:
            if c["id"] == cat_id:
                return c["name"]
        return ""

    def on_product_changed(self, index: int) -> None:
        """
        Gdy zmienimy produkt, możemy wypełnić dodatki z bazy (jak w ser).
        """
        pid = self.product_combo.currentData()
        if pid and pid != -1:
            self.fill_additives_from_db(pid)
            # self.update_doses()  # jeśli chcesz automatycznego przeliczenia
        else:
            self.clear_additives_fields()

    # ----------------------------------------------------------------
    # B. DODATKI – 6 wierszy, 3 kolumny (Kategoria, Dodatek, Dawka)
    # ----------------------------------------------------------------
    def create_section_b_additives(self):
        group = QGroupBox("Dodatki (maks. 6)")
        vbox = QVBoxLayout()

        # Rząd nagłówków
        header_layout = QHBoxLayout()
        lbl_cat = QLabel("Kategoria")
        lbl_cat.setFixedWidth(190)
        lbl_add = QLabel("Dodatek")
        lbl_add.setFixedWidth(140)
        lbl_dose = QLabel("Dawka")
        lbl_dose.setFixedWidth(80)

        header_layout.addWidget(lbl_cat)
        header_layout.addSpacing(30)
        header_layout.addWidget(lbl_add)
        header_layout.addSpacing(30)
        header_layout.addWidget(lbl_dose)
        vbox.addLayout(header_layout)

        self.additive_lines = []
        # Zapamiętujemy (base_value, unit) do przeliczeń
        self.additives_info: List[Tuple[float, str]] = [(0.0, "") for _ in range(6)]

        for i in range(6):
            row = QHBoxLayout()

            cat_edit = QLineEdit()
            cat_edit.setFixedWidth(190)

            add_edit = QLineEdit()
            add_edit.setFixedWidth(140)

            dose_edit = QLineEdit()
            dose_edit.setFixedWidth(80)
            # ewentualnie dose_edit.setReadOnly(True), jeśli automatyczne

            row.addWidget(cat_edit)
            row.addSpacing(30)
            row.addWidget(add_edit)
            row.addSpacing(30)
            row.addWidget(dose_edit)

            self.additive_lines.append((cat_edit, add_edit, dose_edit))
            vbox.addLayout(row)

        group.setLayout(vbox)
        self.main_layout.addWidget(group)

    def fill_additives_from_db(self, product_id: int):
        """
        Wczytuje potencjalne dodatki z bazy (product_additives)
        i uzupełnia (kategoria, dodatek, dawka). Brak "Godz. dodania".
        """
        self.clear_additives_fields()
        if not self.db_manager:
            return

        product_adds = self.db_manager.get_product_additives(product_id)
        for i, pa in enumerate(product_adds):
            if i >= 6:
                break
            add_id = pa["additive_id"]
            dosage_str = pa.get("dosage_per_100", "")
            base_val, unit = parse_dosage(dosage_str)

            add_info = self.db_manager.get_additive_by_id(add_id)
            if not add_info:
                continue

            cat_id = add_info.get("category_id", None)
            cat_name = self.get_additive_category_name_by_id(cat_id)
            add_name = add_info.get("name", "")

            (cat_edit, add_edit, dose_edit) = self.additive_lines[i]
            cat_edit.setText(cat_name)
            add_edit.setText(add_name)
            dose_edit.clear()  # albo wstaw domyślne final_val

            # Zapamiętujemy do update_doses
            self.additives_info[i] = (base_val, unit)

    def get_additive_category_name_by_id(self, cat_id: int) -> str:
        """
        Zwraca nazwę kategorii z tabeli "categories" (dodatków).
        """
        if not self.db_manager:
            return ""
        all_cats = self.db_manager.get_categories()
        for c in all_cats:
            if c["id"] == cat_id:
                return c["name"]
        return ""

    def clear_additives_fields(self):
        for i in range(6):
            (cat_edit, add_edit, dose_edit) = self.additive_lines[i]
            cat_edit.clear()
            add_edit.clear()
            dose_edit.clear()
            self.additives_info[i] = (0.0, "")

    # ----------------------------------------------------------------
    # C. ETAPY: 4 czynności (Dodanie kultur, Rozlewanie, Inkubacja, Chłodzenie)
    # ----------------------------------------------------------------
    def create_section_c_stages_fermented(self):
        """
        Sekcja C: 4 czynności (Dodanie kultur, Rozlewanie, Inkubacja, Chłodzenie).
        Każda czynność ma dwa pola:
        1) Dodanie kultur: (Temp. mleka, Godzina)
        2) Rozlewanie:     (Godzina, Czas trwania)
        3) Inkubacja:      (Temperatura, Czas trwania)
        4) Chłodzenie:     (Godzina, Temp. zadana)
        """

        groupC = QGroupBox("Etapy produkcji (Napoje fermentowane) – 4 czynności")
        gridC = QGridLayout()
        gridC.setHorizontalSpacing(20)

        label_width = 195
        field_width = 80

        # -- Wiersz 0: puste pole (po lewej), nagłówki dla 2 kolumn
        lbl_empty = QLabel("")
        lbl_empty.setFixedWidth(label_width)
        lbl_param1 = QLabel("Parametr 1")
        lbl_param2 = QLabel("Parametr 2")

        gridC.addWidget(lbl_empty,   0, 0)
        gridC.addWidget(lbl_param1,  0, 1)
        gridC.addWidget(lbl_param2,  0, 2)

        # ----------------------------------------------------------------
        # Wiersze 1–2: Dodanie kultur
        #   R1C0: "Dodanie kultur"
        #   R1C1 -> pole = self.dodanie_kultur_godzina_input (ale etykietę opisujemy jako "Temp. mleka")
        #   R1C2 -> pole = self.dodanie_kultur_czas_input    (etykieta: "Godzina")
        # ----------------------------------------------------------------

        # Wiersz 1 (etykiety „Temp. mleka” / „Godzina”)
        # – Tylko napisy, bez QLineEdit, żeby było widać nad polami, co to jest.
        lbl_empty2 = QLabel("")  # po lewej, pusty
        lbl_empty2.setFixedWidth(label_width)
        lbl_temp_mleka = QLabel("Temp. mleka")
        lbl_godzina    = QLabel("Godzina")

        gridC.addWidget(lbl_empty2,     1, 0)
        gridC.addWidget(lbl_temp_mleka, 1, 1)
        gridC.addWidget(lbl_godzina,    1, 2)

        # Wiersz 2 (rzeczywiste pole nazwy czynności + 2 x QLineEdit)
        lbl_dodanie = QLabel("Dodanie kultur")
        lbl_dodanie.setFixedWidth(label_width)

        self.dodanie_kultur_godzina_input = QLineEdit()  # w kodzie "godzina", ale etykietą opisaliśmy jako „Temp. mleka”
        self.dodanie_kultur_godzina_input.setFixedWidth(field_width)

        self.dodanie_kultur_czas_input = QLineEdit()     # w kodzie "czas", a etykieta to „Godzina”
        self.dodanie_kultur_czas_input.setFixedWidth(field_width)

        gridC.addWidget(lbl_dodanie,                   2, 0)
        gridC.addWidget(self.dodanie_kultur_godzina_input, 2, 1)
        gridC.addWidget(self.dodanie_kultur_czas_input,    2, 2)

        # ----------------------------------------------------------------
        # Wiersze 3–4: Rozlewanie
        #   Parametry: (Godzina, Czas trwania)
        # ----------------------------------------------------------------

        # Wiersz 3 (etykiety param1, param2)
        lbl_empty3 = QLabel("")
        lbl_empty3.setFixedWidth(label_width)
        lbl_godzina_rozl  = QLabel("Godzina")
        lbl_czas_rozl     = QLabel("Czas trwania")

        gridC.addWidget(lbl_empty3,      3, 0)
        gridC.addWidget(lbl_godzina_rozl, 3, 1)
        gridC.addWidget(lbl_czas_rozl,    3, 2)

        # Wiersz 4 (nazwa czynności + QLineEdit)
        lbl_rozlewanie = QLabel("Rozlewanie")
        lbl_rozlewanie.setFixedWidth(label_width)

        self.rozlewanie_start_input = QLineEdit()  # w kodzie "start", etykieta: „Godzina”
        self.rozlewanie_start_input.setFixedWidth(field_width)

        self.rozlewanie_end_input   = QLineEdit()  # w kodzie "end",   etykieta: „Czas trwania”
        self.rozlewanie_end_input.setFixedWidth(field_width)

        gridC.addWidget(lbl_rozlewanie,         4, 0)
        gridC.addWidget(self.rozlewanie_start_input, 4, 1)
        gridC.addWidget(self.rozlewanie_end_input,   4, 2)

        # ----------------------------------------------------------------
        # Wiersze 5–6: Inkubacja
        #   (Temperatura, Czas trwania)
        # ----------------------------------------------------------------

        lbl_empty4 = QLabel("")
        lbl_empty4.setFixedWidth(label_width)
        lbl_ink_temp = QLabel("Temperatura")
        lbl_ink_czas = QLabel("Czas trwania")

        gridC.addWidget(lbl_empty4,     5, 0)
        gridC.addWidget(lbl_ink_temp,   5, 1)
        gridC.addWidget(lbl_ink_czas,   5, 2)

        lbl_inkubacja = QLabel("Inkubacja")
        lbl_inkubacja.setFixedWidth(label_width)

        self.inkubacja_temp_input = QLineEdit()  # w kodzie "temp"
        self.inkubacja_temp_input.setFixedWidth(field_width)

        self.inkubacja_czas_input = QLineEdit()  # w kodzie "czas"
        self.inkubacja_czas_input.setFixedWidth(field_width)

        gridC.addWidget(lbl_inkubacja,           6, 0)
        gridC.addWidget(self.inkubacja_temp_input, 6, 1)
        gridC.addWidget(self.inkubacja_czas_input,  6, 2)

        # ----------------------------------------------------------------
        # Wiersze 7–8: Chłodzenie
        #   (Godzina, Temp. zadana)
        # ----------------------------------------------------------------

        lbl_empty5 = QLabel("")
        lbl_empty5.setFixedWidth(label_width)
        lbl_chlodz_godz = QLabel("Godzina")
        lbl_chlodz_temp = QLabel("Temp. zadana")

        gridC.addWidget(lbl_empty5,      7, 0)
        gridC.addWidget(lbl_chlodz_godz, 7, 1)
        gridC.addWidget(lbl_chlodz_temp, 7, 2)

        lbl_chlodzenie = QLabel("Chłodzenie")
        lbl_chlodzenie.setFixedWidth(label_width)

        self.chlodzenie_godzina_input = QLineEdit()
        self.chlodzenie_godzina_input.setFixedWidth(field_width)

        self.chlodzenie_temp_end_input = QLineEdit()
        self.chlodzenie_temp_end_input.setFixedWidth(field_width)

        gridC.addWidget(lbl_chlodzenie,               8, 0)
        gridC.addWidget(self.chlodzenie_godzina_input,   8, 1)
        gridC.addWidget(self.chlodzenie_temp_end_input,  8, 2)

        groupC.setLayout(gridC)
        self.main_layout.addWidget(groupC)



    # ----------------------------------------------------------------
    # D. Ewidencja partii (15 wierszy)
    # ----------------------------------------------------------------
    def create_section_d_parties(self):
        groupD = QGroupBox("Ewidencja partii z tej serii")
        vlayout = QVBoxLayout()

        self.parties_lines = []
        for i in range(15):
            row_layout = QHBoxLayout()

            lbl_part = QLabel(f"Partia {i+1}:")
            lbl_part.setFixedWidth(120)
            part_edit = QLineEdit()
            part_edit.setFixedWidth(120)

            row_layout.addWidget(lbl_part)
            row_layout.addWidget(part_edit)

            row_layout.addSpacing(20)

            lbl_weight = QLabel("Waga (kg):")
            lbl_weight.setFixedWidth(90)
            weight_edit = QLineEdit()
            weight_edit.setFixedWidth(60)
            row_layout.addWidget(lbl_weight)
            row_layout.addWidget(weight_edit)

            row_layout.addSpacing(20)

            lbl_comment = QLabel("Komentarz:")
            lbl_comment.setFixedWidth(80)
            comment_edit = QLineEdit()
            comment_edit.setFixedWidth(120)
            row_layout.addWidget(lbl_comment)
            row_layout.addWidget(comment_edit)

            self.parties_lines.append((part_edit, weight_edit, comment_edit))
            vlayout.addLayout(row_layout)

        groupD.setLayout(vlayout)
        self.main_layout.addWidget(groupD)

    # ----------------------------------------------------------------
    # Dolny pasek (Powrót / Zapisz)
    # ----------------------------------------------------------------
    def create_bottom_buttons(self):
        hbox = QHBoxLayout()

        btn_back = QPushButton("Powrót")
        btn_back.clicked.connect(self.go_back)
        hbox.addWidget(btn_back)

        self.btn_save = QPushButton("Zapisz protokół")
        self.btn_save.clicked.connect(self.save_protocol)
        hbox.addWidget(self.btn_save)

        self.main_layout.addLayout(hbox)

    def go_back(self):
        if hasattr(self.parent, "show_previous_screen"):
            self.parent.show_previous_screen()
        else:
            self.hide()

    # ----------------------------------------------------------------
    #  load_from_record(record_data) / save_protocol()
    #   – analogicznie do sera, ale z innymi polami w sekcji C
    # ----------------------------------------------------------------
    def load_from_record(self, record_data: Optional[dict]) -> None:
        """
        Wypełnia formularz danymi z 'record_data' (z production_records).
        Jeśli record_data=None => nowy, pusty protokół (bez ID).
        """
        if record_data is None:
            # NOWY protokół
            self.current_protocol_id = None

            today_str = date.today().strftime("%Y-%m-%d")
            self.date_input.setText(today_str)

            new_series = self.generate_series_number()
            self.series_input.setText(new_series)

            # Czyszczenie sekcji A
            self.milkAmount_input.clear()
            self.ph_input.clear()
            # Rodzaj mleka => ustaw domyślnie 0 (np. "Krowie" w QComboBox)
            if self.milkType_combo.count() > 0:
                self.milkType_combo.setCurrentIndex(0)
            if self.pasteur_combo.count() > 0:
                self.pasteur_combo.setCurrentIndex(0)

            # Czyszczenie sekcji C (4 czynności)
            self.dodanie_kultur_godzina_input.clear()
            self.dodanie_kultur_czas_input.clear()
            self.rozlewanie_start_input.clear()
            self.rozlewanie_end_input.clear()
            self.inkubacja_temp_input.clear()
            self.inkubacja_czas_input.clear()
            self.chlodzenie_godzina_input.clear()
            self.chlodzenie_temp_end_input.clear()

            # Sekcja D (partie)
            for (part_edit, weight_edit, comment_edit) in self.parties_lines:
                part_edit.clear()
                weight_edit.clear()
                comment_edit.clear()

            # Ustaw combo "Wybierz..." w sekcji A
            if self.product_combo.count() > 0:
                self.product_combo.setCurrentIndex(0)

            # Czyścimy dodatki (sekcja B)
            self.clear_additives_fields()

            print(">>> load_from_record(Napoje ferm.): NOWY / pusty protokół.")
            return

        # ----------------------------------------------------------------
        # ISTNIEJĄCY protokół
        # ----------------------------------------------------------------
        self.current_protocol_id = record_data.get("id", None)
        date_str   = record_data.get("date", "")
        series_str = record_data.get("series", "")
        product_id = record_data.get("product_id", None)

        # Sekcja A
        self.date_input.setText(date_str)
        self.series_input.setText(series_str)

        # Ustaw produkt w combobox
        found_index = -1
        for i in range(self.product_combo.count()):
            if self.product_combo.itemData(i) == product_id:
                found_index = i
                break
        if found_index >= 0:
            self.product_combo.setCurrentIndex(found_index)
        else:
            if product_id is not None:
                QMessageBox.warning(
                    self,
                    "Uwaga",
                    f"Produkt o ID={product_id} nie istnieje w bazie. Ustawiam Wybierz..."
                )
            if self.product_combo.count() > 0:
                self.product_combo.setCurrentIndex(0)

        # Pobierz szczegóły z fermented_production_details (lub innej Twojej metody)
        if self.db_manager and self.current_protocol_id is not None:
            details = self.db_manager.get_fermented_production_details(self.current_protocol_id)
            if details:
                # Ilość surowca, pH, Rodzaj mleka itp.
                amt_str = details.get("amt", "")  # Ilość surowca
                self.milkAmount_input.setText(amt_str)

                ph_str = details.get("ph", "")
                self.ph_input.setText(ph_str)

                # Rodzaj mleka (milk_type)
                milk_type_str = details.get("milk_type", "Krowie")
                # Wyszukaj w combobox
                idx_milk_type = self.milkType_combo.findText(milk_type_str)
                if idx_milk_type < 0:
                    idx_milk_type = 0
                self.milkType_combo.setCurrentIndex(idx_milk_type)

                # Pasteryzacja
                pasteur_str = details.get("pasteryzacja", "Brak")
                idx_pasteur = self.pasteur_combo.findText(pasteur_str)
                if idx_pasteur < 0:
                    idx_pasteur = 0
                self.pasteur_combo.setCurrentIndex(idx_pasteur)

                # Sekcja C – 4 czynności
                self.dodanie_kultur_godzina_input.setText(details.get("dod_kultur_godz", ""))
                self.dodanie_kultur_czas_input.setText(details.get("dod_kultur_czas", ""))

                self.rozlewanie_start_input.setText(details.get("rozl_start", ""))
                self.rozlewanie_end_input.setText(details.get("rozl_end", ""))

                self.inkubacja_temp_input.setText(details.get("ink_temp", ""))
                self.inkubacja_czas_input.setText(details.get("ink_czas", ""))

                self.chlodzenie_godzina_input.setText(details.get("chl_godz", ""))
                self.chlodzenie_temp_end_input.setText(details.get("chl_temp_end", ""))

            else:
                # Brak wiersza => czyścimy
                self.milkAmount_input.clear()
                self.ph_input.clear()
                if self.milkType_combo.count() > 0:
                    self.milkType_combo.setCurrentIndex(0)
                idx_p = self.pasteur_combo.findText("Brak")
                self.pasteur_combo.setCurrentIndex(idx_p if idx_p >= 0 else 0)

                self.dodanie_kultur_godzina_input.clear()
                self.dodanie_kultur_czas_input.clear()
                self.rozlewanie_start_input.clear()
                self.rozlewanie_end_input.clear()
                self.inkubacja_temp_input.clear()
                self.inkubacja_czas_input.clear()
                self.chlodzenie_godzina_input.clear()
                self.chlodzenie_temp_end_input.clear()

        # Wczytaj dodatki (sekcja B)
        if product_id:
            self.fill_additives_from_db(product_id)

        print(f">>> load_from_record(Napoje ferm.): ID={self.current_protocol_id}, "
            f"date={date_str}, series={series_str}, product_id={product_id}")

    def save_protocol(self) -> None:
        """
        Zapisuje / aktualizuje protokół w bazie:
        - production_records (date, series, product_id),
        - fermented_production_details (rodzaj mleka, pH, pasteryzacja, 4 czynności),
        - dodatki w 'ser_production_additives' (3 kolumny: cat, add, dose).
        """
        if not self.db_manager:
            QMessageBox.warning(self, "Błąd", "Brak db_manager – nie można zapisać.")
            return

        # ----------------------------------------------------------------
        # 1) Sekcja A: parametry
        # ----------------------------------------------------------------
        product_id  = self.product_combo.currentData()
        date_str    = self.date_input.text().strip()
        series_str  = self.series_input.text().strip()

        # Rodzaj mleka (milkType_combo) oraz ilość (milkAmount_input)
        milk_type_str = self.milkType_combo.currentText().strip()  # <-- Rodzaj mleka
        amt_str       = self.milkAmount_input.text().strip()       # np. "ilość mleka"
        ph_str        = self.ph_input.text().strip()
        pasteur_str   = self.pasteur_combo.currentText().strip()

        # Walidacja minimalna:
        if not date_str or not series_str or not amt_str:
            QMessageBox.warning(self, "Błąd", "Uzupełnij datę, numer serii i ilość mleka.")
            return
        if product_id is None or product_id == -1:
            QMessageBox.warning(self, "Błąd", "Nie wybrano poprawnego produktu (Napoje ferm.).")
            return

        # sprawdź, czy amt_str to liczba
        try:
            float(amt_str)
        except ValueError:
            QMessageBox.warning(self, "Błąd", "Ilość mleka musi być liczbą.")
            return

        # ----------------------------------------------------------------
        # 2) Sekcja C: 4 czynności
        # ----------------------------------------------------------------
        dod_kultur_godz_str = self.dodanie_kultur_godzina_input.text().strip()
        dod_kultur_czas_str = self.dodanie_kultur_czas_input.text().strip()

        rozl_start_str = self.rozlewanie_start_input.text().strip()
        rozl_end_str   = self.rozlewanie_end_input.text().strip()

        ink_temp_str = self.inkubacja_temp_input.text().strip()
        ink_czas_str = self.inkubacja_czas_input.text().strip()

        chl_godzina_str  = self.chlodzenie_godzina_input.text().strip()
        chl_temp_end_str = self.chlodzenie_temp_end_input.text().strip()

        try:
            # ----------------------------------------------------------------
            # 3) Zapis / aktualizacja w bazie
            # ----------------------------------------------------------------
            if self.current_protocol_id is None:
                # NOWY protokół
                new_id = self.db_manager.add_production_record_returning_id(
                    date_str, series_str, product_id
                )
                self.db_manager.add_fermented_production_details(
                    production_record_id=new_id,
                    # Rodzaj mleka i reszta
                    milk_type=milk_type_str,  # <-- kolumna w DB: milk_type
                    amt=amt_str,
                    ph=ph_str,
                    pasteryzacja=pasteur_str,

                    # 4 czynności:
                    dod_kultur_godz=dod_kultur_godz_str,
                    dod_kultur_czas=dod_kultur_czas_str,
                    rozl_start=rozl_start_str,
                    rozl_end=rozl_end_str,
                    ink_temp=ink_temp_str,
                    ink_czas=ink_czas_str,
                    chl_godz=chl_godzina_str,
                    chl_temp_end=chl_temp_end_str
                )
                self.current_protocol_id = new_id
                QMessageBox.information(
                    self,
                    "Sukces",
                    f"Protokół (Napoje fermentowane) '{series_str}' zapisany (NOWY)."
                )
            else:
                # EDYCJA
                self.db_manager.update_production_record(
                    self.current_protocol_id,
                    date_str,
                    series_str,
                    product_id
                )
                self.db_manager.update_fermented_production_details(
                    production_record_id=self.current_protocol_id,
                    milk_type=milk_type_str,
                    amt=amt_str,
                    ph=ph_str,
                    pasteryzacja=pasteur_str,
                    dod_kultur_godz=dod_kultur_godz_str,
                    dod_kultur_czas=dod_kultur_czas_str,
                    rozl_start=rozl_start_str,
                    rozl_end=rozl_end_str,
                    ink_temp=ink_temp_str,
                    ink_czas=ink_czas_str,
                    chl_godz=chl_godzina_str,
                    chl_temp_end=chl_temp_end_str
                )
                QMessageBox.information(
                    self,
                    "Sukces",
                    f"Zaktualizowano protokół (Napoje fermentowane) '{series_str}' "
                    f"(ID={self.current_protocol_id})."
                )

            # ----------------------------------------------------------------
            # 4) Zapis dodatków (sekcja B)
            # ----------------------------------------------------------------
            record_id = self.current_protocol_id
            self.db_manager.clear_ser_production_additives_for_record(record_id)

            for (cat_edit, add_edit, dose_edit) in self.additive_lines:
                cat_str  = cat_edit.text().strip()
                add_str  = add_edit.text().strip()
                dose_str = dose_edit.text().strip()

                # Pomijamy pusty wiersz
                if not cat_str and not add_str and not dose_str:
                    continue

                # Wstaw do ser_production_additives (3 kolumny)
                self.db_manager.add_ser_production_additive_3col(
                    record_id,
                    cat_str,
                    add_str,
                    dose_str
                )

        except Exception as e:
            QMessageBox.warning(
                self,
                "Błąd",
                f"Nie udało się zapisać protokołu: {e}"
            )

    def generate_series_number(self) -> str:
        """
        Generuje nr serii w formacie xxxyy_zz
        """
        if not self.db_manager:
            return "00000_00"
        today = date.today()
        mm = today.month
        yyyy = today.year
        current_count = self.db_manager.get_next_series_number_for_month(mm, yyyy)
        return f"{current_count:03d}{mm:02d}_{yyyy}"

    def showEvent(self, event):
        super().showEvent(event)
        print("FermentedProductionProtocolScreen.showEvent() - I'm being shown!")

    # ----------------------------------------------------------------
    # Metody do przeliczania dawek – analogicznie do protokołu 'Ser'
    # ----------------------------------------------------------------
    def update_doses(self):
        """
        Wywoływane przy zmianie ilości surowca (milkAmount_input).
        Przelicza wartości dawek w kolumnie 'Dawka' w oparciu o self.additives_info[i].
        """
        try:
            amt_str = self.milkAmount_input.text().strip()
            if not amt_str:
                self.clear_doses()
                return
            amt_val = float(amt_str)
        except ValueError:
            # Jeśli w polu nie ma liczby, czyścimy dawki
            self.clear_doses()
            return

        # Przykład: wzór factor = amt_val / 100.0 (jak w protokole sera)
        factor = amt_val / 100.0

        # Dla każdej linii dodatków (max 6 wierszy)
        for i, (cat_edit, add_edit, dose_edit) in enumerate(self.additive_lines):
            base_val, unit = self.additives_info[i]
            if base_val > 0:
                final_val = base_val * factor
                dose_edit.setText(f"{final_val:.1f} {unit}")
            else:
                dose_edit.clear()

    def clear_doses(self):
        """
        Czyści kolumnę 'Dawka' w 6 wierszach sekcji B.
        """
        for (cat_edit, add_edit, dose_edit) in self.additive_lines:
            dose_edit.clear()


