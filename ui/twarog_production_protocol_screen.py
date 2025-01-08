from typing import Optional, Any, List, Tuple
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QMessageBox,
    QScrollArea,
)
from PyQt5.QtCore import Qt
from datetime import date

from database.db_manager import DBManager


def parse_dosage(dosage_str: str) -> Tuple[float, str]:
    """
    Rozdziela tekst typu "30 g", "17 ml", "10" itp. na (wartość float, jednostka).
    """
    parts = dosage_str.split()
    if len(parts) == 1:
        # Np. "10"
        try:
            val = float(parts[0].replace(",", "."))
        except ValueError:
            val = 0.0
        return val, ""
    elif len(parts) >= 2:
        # Np. "17 ml", "30 g"
        try:
            val = float(parts[0].replace(",", "."))
        except ValueError:
            val = 0.0
        unit = parts[1]
        return val, unit
    else:
        return 0.0, ""


class TwarogProductionProtocolScreen(QWidget):
    """
    Formularz protokołu produkcji 'Ser Twarogowy':
      - Sekcja A: Parametry (nazwa produktu, data, numer serii, rodzaj mleka, ilość mleka, pH, pasteryzacja).
      - Sekcja B: Dodatki (6 wierszy, 3 kolumny).
      - Sekcja C: 4 czynności (Krojenie, Dogrzewanie, Formy, Solenie).
      - Sekcja D: Ewidencja partii (15 wierszy).
      - Zapis/odczyt do/do bazy w metodach save_protocol i load_from_record.
      - Pastelowy styl jak w protokołach 'Ser'/'Napoje ferm.'.
      - Przeliczanie dawek w update_doses (faktor = ilość_litrow / 100.0).
    """

    def __init__(
        self, parent: Optional[Any] = None, db_manager: Optional[DBManager] = None
    ):
        super().__init__(parent)
        self.parent = parent
        self.db_manager = db_manager

        self.setWindowTitle("Protokół Produkcji (Ser Twarogowy)")
        self.resize(800, 600)

        # Pastelowy styl
        self.setStyleSheet(
            """
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
        """
        )

        # Aktualnie edytowany protokół (None => nowy)
        self.current_protocol_id: Optional[int] = None

        # Informacje o dodatkach – (wartość_bazowa, jednostka)
        # – by móc przeliczać dawki w update_doses.
        self.additives_info: List[Tuple[float, str]] = [(0.0, "") for _ in range(6)]

        # ScrollArea + główny layout
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)

        # Sekcje A, B, C, D
        self.create_section_a_params()
        self.create_section_b_additives()
        self.create_section_c_stages()
        self.create_section_d_parties()

        # Dolne przyciski
        self.create_bottom_buttons()

        # Wrzucamy main_layout -> scroll_area
        self.scroll_area.setWidget(self.main_widget)
        outer_layout = QVBoxLayout()
        outer_layout.addWidget(self.scroll_area)
        self.setLayout(outer_layout)

    # ----------------------------------------------------------------
    # A. PARAMETRY
    # ----------------------------------------------------------------
    def create_section_a_params(self):
        group = QGroupBox("Parametry wstępne")
        grid = QGridLayout()
        grid.setHorizontalSpacing(40)

        label_width = 195
        field_width = 195

        # 1) Nazwa produktu (Twarogowy)
        lbl_prod = QLabel("Nazwa produktu (Ser twarogowy):")
        lbl_prod.setFixedWidth(label_width)
        self.product_combo = QComboBox()
        self.product_combo.setFixedWidth(field_width)
        grid.addWidget(lbl_prod, 0, 0)
        grid.addWidget(self.product_combo, 0, 1)

        # 2) Data
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

        # 4) Rodzaj mleka
        lbl_milk_type = QLabel("Rodzaj mleka:")
        lbl_milk_type.setFixedWidth(label_width)
        self.milkType_combo = QComboBox()
        self.milkType_combo.addItems(["Krowie", "Owcze", "Kozie"])
        self.milkType_combo.setFixedWidth(field_width)
        grid.addWidget(lbl_milk_type, 3, 0)
        grid.addWidget(self.milkType_combo, 3, 1)

        # 5) Ilość mleka
        lbl_amt = QLabel("Ilość mleka (litry):")
        lbl_amt.setFixedWidth(label_width)
        self.milkAmount_input = QLineEdit()
        self.milkAmount_input.setFixedWidth(field_width)
        self.milkAmount_input.setPlaceholderText("np. 50.0")
        self.milkAmount_input.textChanged.connect(
            self.update_doses
        )  # przeliczanie dawek
        grid.addWidget(lbl_amt, 4, 0)
        grid.addWidget(self.milkAmount_input, 4, 1)

        # 6) pH
        lbl_ph = QLabel("pH (x,xx):")
        lbl_ph.setFixedWidth(label_width)
        self.ph_input = QLineEdit()
        self.ph_input.setFixedWidth(field_width)
        grid.addWidget(lbl_ph, 5, 0)
        grid.addWidget(self.ph_input, 5, 1)

        # 7) Pasteryzacja
        lbl_pasteur = QLabel("Pasteryzacja:")
        lbl_pasteur.setFixedWidth(label_width)
        self.pasteur_combo = QComboBox()
        self.pasteur_combo.addItems(["Brak", "65°C/30min", "85°C/10min"])
        self.pasteur_combo.setFixedWidth(field_width)
        grid.addWidget(lbl_pasteur, 6, 0)
        grid.addWidget(self.pasteur_combo, 6, 1)

        group.setLayout(grid)
        self.main_layout.addWidget(group)

        # Po utworzeniu comboboxa – wypełnij produktami z bazy:
        self.fill_twarog_products()

    def fill_twarog_products(self):
        """
        Wypełnia product_combo WYŁĄCZNIE produktami o kategorii "Ser twarogowy" (po nazwie).
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
            if cat_name.lower() == "ser twarogowy":
                self.product_combo.addItem(p["name"], p["id"])

        self.product_combo.setCurrentIndex(0)
        self.product_combo.setEnabled(True)
        self.product_combo.currentIndexChanged.connect(self.on_product_changed)

    def get_category_name_by_id(self, cat_id: int) -> str:
        if not self.db_manager:
            return ""
        cats = self.db_manager.get_product_categories()
        for c in cats:
            if c["id"] == cat_id:
                return c["name"]
        return ""

    def on_product_changed(self, index: int) -> None:
        pid = self.product_combo.currentData()
        if pid and pid != -1:
            self.fill_additives_from_db(pid)
            self.update_doses()
        else:
            self.clear_additives_fields()

    # ----------------------------------------------------------------
    # B. DODATKI – 6 wierszy, 3 kolumny (Kategoria, Dodatek, Dawka)
    # ----------------------------------------------------------------
    def create_section_b_additives(self):
        group = QGroupBox("Dodatki (maks. 6)")
        vbox = QVBoxLayout()

        # Nagłówki
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
        for i in range(6):
            row = QHBoxLayout()

            cat_edit = QLineEdit()
            cat_edit.setFixedWidth(190)
            add_edit = QLineEdit()
            add_edit.setFixedWidth(140)
            dose_edit = QLineEdit()
            dose_edit.setFixedWidth(80)

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
        Wypełnia pola Kategoria, Dodatek, Dawka (bazowo) z relacji product_additives.
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

            # Nie wstawiamy od razu base_val do dose_edit, bo jest przeliczane
            dose_edit.clear()

            self.additives_info[i] = (base_val, unit)

    def get_additive_category_name_by_id(self, cat_id: int) -> str:
        if not self.db_manager:
            return ""
        cat_list = self.db_manager.get_categories()
        for c in cat_list:
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
    # C. ETAPY – 4 czynności: Krojenie, Dogrzewanie, Formy, Solenie
    # ----------------------------------------------------------------
    def create_section_c_stages(self):
        """
        Sekcja C – 4 czynności, każda w układzie 2-wierszowym x 3-kolumnowym:
        1) Krojenie:   (R1: [puste, "Godzina", "Temperatura"],
                        R2: ["Krojenie", QLineEdit (krojenie_start_input), QLineEdit (krojenie_end_input)])
        2) Dogrzewanie:(R3: [puste, "Początek", "Koniec"],
                        R4: ["Dogrzewanie", QLineEdit (dogrzewanie_start_input), QLineEdit (dogrzewanie_end_input)])
        3) Formy:      (R5: [puste, "Ilość", "Wielkość"],
                        R6: ["Formy", QLineEdit (formy_ilosc_input), QLineEdit (formy_wielkosc_input)])
        4) Solenie:    (R7: [puste, "Początek", "Koniec"],
                        R8: ["Solenie", QLineEdit (solenie_start_input), QLineEdit (solenie_end_input)])
        """

        groupC = QGroupBox("Etapy produkcji (Twarog)")
        gridC = QGridLayout()
        gridC.setHorizontalSpacing(20)

        label_width = 195
        field_width = 80

        # -------------------------------------------------------------
        # 1) KROJENIE: 2 wiersze
        # -------------------------------------------------------------
        # Wiersz 1 (etykiety): [puste, "Godzina", "Temperatura"]
        row = 0
        lbl_empty1 = QLabel("")
        lbl_empty1.setFixedWidth(label_width)
        lbl_kroj_time = QLabel("Godzina")
        lbl_kroj_temp = QLabel("Temperatura")
        gridC.addWidget(lbl_empty1, row, 0)
        gridC.addWidget(lbl_kroj_time, row, 1)
        gridC.addWidget(lbl_kroj_temp, row, 2)

        # Wiersz 2: ["Krojenie", QLineEdit => krojenie_start_input, QLineEdit => krojenie_end_input]
        row += 1
        lbl_krojenie = QLabel("Krojenie")
        lbl_krojenie.setFixedWidth(label_width)

        # Zachowujemy dotychczasowe nazwy pól, jeśli tak masz w load/save
        self.krojenie_start_input = QLineEdit()
        self.krojenie_start_input.setFixedWidth(field_width)
        self.krojenie_end_input = QLineEdit()
        self.krojenie_end_input.setFixedWidth(field_width)

        gridC.addWidget(lbl_krojenie, row, 0)
        gridC.addWidget(self.krojenie_start_input, row, 1)
        gridC.addWidget(self.krojenie_end_input, row, 2)

        # -------------------------------------------------------------
        # 2) DOGRZEWANIE: 2 wiersze
        # -------------------------------------------------------------
        # Wiersz 1 (etykiety): [puste, "Początek", "Koniec"]
        row += 1
        lbl_empty2 = QLabel("")
        lbl_empty2.setFixedWidth(label_width)
        lbl_dogr_start = QLabel("Początek")
        lbl_dogr_end = QLabel("Koniec")
        gridC.addWidget(lbl_empty2, row, 0)
        gridC.addWidget(lbl_dogr_start, row, 1)
        gridC.addWidget(lbl_dogr_end, row, 2)

        # Wiersz 2: ["Dogrzewanie", QLineEdit => dogrzewanie_start_input, QLineEdit => dogrzewanie_end_input]
        row += 1
        lbl_dogrzewanie = QLabel("Dogrzewanie")
        lbl_dogrzewanie.setFixedWidth(label_width)
        self.dogrzewanie_start_input = QLineEdit()
        self.dogrzewanie_start_input.setFixedWidth(field_width)
        self.dogrzewanie_end_input = QLineEdit()
        self.dogrzewanie_end_input.setFixedWidth(field_width)

        gridC.addWidget(lbl_dogrzewanie, row, 0)
        gridC.addWidget(self.dogrzewanie_start_input, row, 1)
        gridC.addWidget(self.dogrzewanie_end_input, row, 2)

        # -------------------------------------------------------------
        # 3) FORMY: 2 wiersze
        # -------------------------------------------------------------
        # Wiersz 1 (etykiety): [puste, "Ilość", "Wielkość"]
        row += 1
        lbl_empty3 = QLabel("")
        lbl_empty3.setFixedWidth(label_width)
        lbl_formy_ilosc = QLabel("Ilość")
        lbl_formy_wiel = QLabel("Wielkość")
        gridC.addWidget(lbl_empty3, row, 0)
        gridC.addWidget(lbl_formy_ilosc, row, 1)
        gridC.addWidget(lbl_formy_wiel, row, 2)

        # Wiersz 2: ["Formy", QLineEdit => formy_ilosc_input, QLineEdit => formy_wielkosc_input]
        row += 1
        lbl_formy = QLabel("Formy")
        lbl_formy.setFixedWidth(label_width)
        self.formy_ilosc_input = QLineEdit()
        self.formy_ilosc_input.setFixedWidth(field_width)
        self.formy_wielkosc_input = QLineEdit()
        self.formy_wielkosc_input.setFixedWidth(field_width)

        gridC.addWidget(lbl_formy, row, 0)
        gridC.addWidget(self.formy_ilosc_input, row, 1)
        gridC.addWidget(self.formy_wielkosc_input, row, 2)

        # -------------------------------------------------------------
        # 4) SOLENIE: 2 wiersze
        # -------------------------------------------------------------
        # Wiersz 1 (etykiety): [puste, "Początek", "Koniec"]
        row += 1
        lbl_empty4 = QLabel("")
        lbl_empty4.setFixedWidth(label_width)
        lbl_sol_start = QLabel("Początek")
        lbl_sol_end = QLabel("Koniec")
        gridC.addWidget(lbl_empty4, row, 0)
        gridC.addWidget(lbl_sol_start, row, 1)
        gridC.addWidget(lbl_sol_end, row, 2)

        # Wiersz 2: ["Solenie", QLineEdit => solenie_start_input, QLineEdit => solenie_end_input]
        row += 1
        lbl_solenie = QLabel("Solenie")
        lbl_solenie.setFixedWidth(label_width)
        self.solenie_start_input = QLineEdit()
        self.solenie_start_input.setFixedWidth(field_width)
        self.solenie_end_input = QLineEdit()
        self.solenie_end_input.setFixedWidth(field_width)

        gridC.addWidget(lbl_solenie, row, 0)
        gridC.addWidget(self.solenie_start_input, row, 1)
        gridC.addWidget(self.solenie_end_input, row, 2)

        # -------------------------------------------------------------
        # Przypisujemy layout do groupC i dodajemy do głównego layoutu
        # -------------------------------------------------------------
        groupC.setLayout(gridC)
        self.main_layout.addWidget(groupC)

    # ----------------------------------------------------------------
    # D. Ewidencja partii (15 wierszy)
    # ----------------------------------------------------------------
    def create_section_d_parties(self):
        groupD = QGroupBox("Ewidencja partii (Ser Twarogowy)")
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
    # Dolne przyciski (Powrót / Zapisz)
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
    # LOGIKA
    # ----------------------------------------------------------------
    def load_from_record(self, record_data: Optional[dict]) -> None:
        """
        Wczytuje protokół z bazy (production_records + twarog_production_details).
        Jeśli record_data=None => nowy, pusty protokół (bez ID w bazie).
        """
        if record_data is None:
            # ----------------------------------
            # NOWY protokół (bez ID)
            # ----------------------------------
            self.current_protocol_id = None

            today_str = date.today().strftime("%Y-%m-%d")
            self.date_input.setText(today_str)

            # Numer serii (generowany automatycznie)
            new_series = self.generate_series_number()
            self.series_input.setText(new_series)

            # Sekcja A (mleko, pH, pasteryzacja, itd.)
            self.milkAmount_input.clear()
            self.ph_input.clear()
            if self.pasteur_combo.count() > 0:
                self.pasteur_combo.setCurrentIndex(0)
            if self.milkType_combo.count() > 0:
                self.milkType_combo.setCurrentIndex(0)

            # Sekcja C (krojenie, dogrzewanie, formy, solenie)
            self.krojenie_start_input.clear()
            self.krojenie_end_input.clear()
            self.dogrzewanie_start_input.clear()
            self.dogrzewanie_end_input.clear()
            self.formy_wielkosc_input.clear()
            self.formy_ilosc_input.clear()
            self.solenie_start_input.clear()
            self.solenie_end_input.clear()

            # Sekcja D (partie)
            for part_edit, weight_edit, comment_edit in self.parties_lines:
                part_edit.clear()
                weight_edit.clear()
                comment_edit.clear()

            # Combo 'Wybierz...' w product_combo
            if self.product_combo.count() > 0:
                # -- (A) Wybieramy domyślnie "Ser twarogowy" (jeśli istnieje w comboboxie)
                default_prod_name = "Ser twarogowy"
                idx_twarog = self.product_combo.findText(default_prod_name)
                if idx_twarog < 0:
                    # Jeśli nie znaleziono, weź pierwszy
                    idx_twarog = 0
                self.product_combo.setCurrentIndex(idx_twarog)

                # -- (B) Pobieramy ID wybranego produktu i wypełniamy dodatki
                default_pid = self.product_combo.itemData(idx_twarog)
                if default_pid and default_pid != -1:
                    self.fill_additives_from_db(default_pid)
                else:
                    # Jeśli "Wybierz..." lub brak ID – wyczyść
                    self.clear_additives_fields()
            else:
                # Jeżeli brak elementów w comboboxie, to i tak
                # nie możemy nic wypełnić.
                self.clear_additives_fields()

            print(
                ">>> Nowy protokół (Twarog) => wyczyszczono pola, wypełniono domyślnie dodatki (o ile były)."
            )
            return

        # -------------------------------------------------------
        # ISTNIEJĄCY protokół (record_data != None)
        # -------------------------------------------------------
        self.current_protocol_id = record_data.get("id", None)
        date_str = record_data.get("date", "")
        series_str = record_data.get("series", "")
        product_id = record_data.get("product_id", None)

        # Sekcja A – data, numer serii
        self.date_input.setText(date_str)
        self.series_input.setText(series_str)

        # Ustaw produkt w combo (wg product_id)
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
                    f"Produkt o ID={product_id} nie istnieje w bazie. Ustawiam pierwszy z listy.",
                )
            if self.product_combo.count() > 0:
                self.product_combo.setCurrentIndex(0)

        # -------------------------------------------------------
        # Wczytujemy szczegóły z tabeli twarog_production_details
        # -------------------------------------------------------
        if self.db_manager and self.current_protocol_id is not None:
            details = self.db_manager.get_twarog_production_details(
                self.current_protocol_id
            )
            if details:
                amt_str = details.get("milk_amount", "")
                self.milkAmount_input.setText(amt_str)

                ph_str = details.get("ph", "")
                self.ph_input.setText(ph_str)

                pasteur_str = details.get("pasteryzacja", "Brak")
                idx_past = self.pasteur_combo.findText(pasteur_str)
                if idx_past < 0:
                    idx_past = 0
                self.pasteur_combo.setCurrentIndex(idx_past)

                milk_type_str = details.get("milk_type", "Krowie")
                idx_milk = self.milkType_combo.findText(milk_type_str)
                if idx_milk < 0:
                    idx_milk = 0
                self.milkType_combo.setCurrentIndex(idx_milk)

                # Sekcja C
                self.krojenie_start_input.setText(details.get("krojenie_start", ""))
                self.krojenie_end_input.setText(details.get("krojenie_end", ""))
                self.dogrzewanie_start_input.setText(
                    details.get("dogrzewanie_start", "")
                )
                self.dogrzewanie_end_input.setText(details.get("dogrzewanie_end", ""))
                self.formy_wielkosc_input.setText(details.get("formy_wielkosc", ""))
                self.formy_ilosc_input.setText(details.get("formy_ilosc", ""))
                self.solenie_start_input.setText(details.get("solenie_start", ""))
                self.solenie_end_input.setText(details.get("solenie_end", ""))
            else:
                # Brak wiersza w twarog_production_details => czyścimy
                self.milkAmount_input.clear()
                self.ph_input.clear()
                if self.pasteur_combo.count() > 0:
                    self.pasteur_combo.setCurrentIndex(0)
                if self.milkType_combo.count() > 0:
                    self.milkType_combo.setCurrentIndex(0)

                self.krojenie_start_input.clear()
                self.krojenie_end_input.clear()
                self.dogrzewanie_start_input.clear()
                self.dogrzewanie_end_input.clear()
                self.formy_wielkosc_input.clear()
                self.formy_ilosc_input.clear()
                self.solenie_start_input.clear()
                self.solenie_end_input.clear()

        # ------------------------------------------------------------
        # Wczytujemy ZAPISANE w bazie dodatki (sekcja B)
        # ------------------------------------------------------------
        if product_id and self.db_manager:
            try:
                lines = self.db_manager.get_ser_production_additives_for_record(
                    self.current_protocol_id
                )
            except AttributeError:
                # Metoda nie istnieje => brak możliwości wczytania
                lines = []
                print(
                    "UWAGA: Brak metody get_ser_production_additives_for_record w DBManager."
                )

            # Czyścimy pola
            self.clear_additives_fields()

            # Przepisz dane z bazy do GUI
            for i, row in enumerate(lines):
                if i >= len(self.additive_lines):
                    break
                cat_str = row.get("additive_category", "")
                add_str = row.get("additive_name", "")
                dose_str = row.get("dose_calculated", "")

                base_val, unit = parse_dosage(dose_str)
                self.additives_info[i] = (base_val, unit)

                (cat_edit, add_edit, dose_edit) = self.additive_lines[i]
                cat_edit.setText(cat_str)
                add_edit.setText(add_str)
                dose_edit.setText(dose_str)

        print(
            f">>> Twarog load_from_record: ID={self.current_protocol_id}, "
            f"date={date_str}, series={series_str}, product_id={product_id}"
        )

    def save_protocol(self) -> None:
        """
        Zapis / aktualizacja protokołu w:
         - production_records,
         - twarog_production_details,
         - ser_production_additives (jeśli używamy tej wspólnej tabeli na dodatki).
        """
        if not self.db_manager:
            QMessageBox.warning(self, "Błąd", "Brak db_manager – nie można zapisać.")
            return

        product_id = self.product_combo.currentData()
        date_str = self.date_input.text().strip()
        series_str = self.series_input.text().strip()

        milk_type_str = self.milkType_combo.currentText().strip()
        amt_str = self.milkAmount_input.text().strip()
        ph_str = self.ph_input.text().strip()
        pasteur_str = self.pasteur_combo.currentText().strip()

        if not date_str or not series_str or not amt_str:
            QMessageBox.warning(
                self, "Błąd", "Uzupełnij datę, numer serii i ilość mleka."
            )
            return
        if product_id is None or product_id == -1:
            QMessageBox.warning(
                self, "Błąd", "Nie wybrano poprawnego produktu (Ser Twarogowy)."
            )
            return
        try:
            float(amt_str)
        except ValueError:
            QMessageBox.warning(self, "Błąd", "Ilość mleka musi być liczbą.")
            return

        # Sekcja C
        kroj_start_str = self.krojenie_start_input.text().strip()
        kroj_end_str = self.krojenie_end_input.text().strip()
        dogr_start_str = self.dogrzewanie_start_input.text().strip()
        dogr_end_str = self.dogrzewanie_end_input.text().strip()
        formy_w_str = self.formy_wielkosc_input.text().strip()
        formy_i_str = self.formy_ilosc_input.text().strip()
        sol_start_str = self.solenie_start_input.text().strip()
        sol_end_str = self.solenie_end_input.text().strip()

        try:
            if self.current_protocol_id is None:
                # NOWY
                new_id = self.db_manager.add_production_record_returning_id(
                    date_str, series_str, product_id
                )
                # Dodaj w twarog_production_details
                self.db_manager.add_twarog_production_details(
                    production_record_id=new_id,
                    milk_type=milk_type_str,
                    milk_amount=amt_str,
                    ph=ph_str,
                    pasteryzacja=pasteur_str,
                    krojenie_start=kroj_start_str,
                    krojenie_end=kroj_end_str,
                    dogrzewanie_start=dogr_start_str,
                    dogrzewanie_end=dogr_end_str,
                    formy_wielkosc=formy_w_str,
                    formy_ilosc=formy_i_str,
                    solenie_start=sol_start_str,
                    solenie_end=sol_end_str,
                )
                self.current_protocol_id = new_id
                QMessageBox.information(
                    self,
                    "Sukces",
                    f"Protokół (Ser Twarogowy) '{series_str}' zapisany (NOWY).",
                )
            else:
                # EDYCJA
                self.db_manager.update_production_record(
                    self.current_protocol_id, date_str, series_str, product_id
                )
                self.db_manager.update_twarog_production_details(
                    production_record_id=self.current_protocol_id,
                    milk_type=milk_type_str,
                    milk_amount=amt_str,
                    ph=ph_str,
                    pasteryzacja=pasteur_str,
                    krojenie_start=kroj_start_str,
                    krojenie_end=kroj_end_str,
                    dogrzewanie_start=dogr_start_str,
                    dogrzewanie_end=dogr_end_str,
                    formy_wielkosc=formy_w_str,
                    formy_ilosc=formy_i_str,
                    solenie_start=sol_start_str,
                    solenie_end=sol_end_str,
                )
                QMessageBox.information(
                    self,
                    "Sukces",
                    f"Zaktualizowano protokół (Ser Twarogowy) '{series_str}' (ID={self.current_protocol_id}).",
                )

            # Dodatki
            record_id = self.current_protocol_id
            self.db_manager.clear_ser_production_additives_for_record(record_id)
            for cat_edit, add_edit, dose_edit in self.additive_lines:
                cat_str = cat_edit.text().strip()
                add_str = add_edit.text().strip()
                dose_val = dose_edit.text().strip()
                if not cat_str and not add_str and not dose_val:
                    continue
                self.db_manager.add_ser_production_additive_3col(
                    record_id, cat_str, add_str, dose_val
                )

        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się zapisać protokołu: {e}")

    def update_doses(self):
        """
        Przelicza wartości dawek w sekcji B, na podstawie self.additives_info[i].
        factor = (ilość mleka w litrach) / 100.
        """
        try:
            amt_str = self.milkAmount_input.text().strip()
            if not amt_str:
                self.clear_doses()
                return
            amt_liters = float(amt_str)
        except ValueError:
            self.clear_doses()
            return

        factor = amt_liters / 100.0
        for i, (cat_edit, add_edit, dose_edit) in enumerate(self.additive_lines):
            base_val, unit = self.additives_info[i]
            if base_val > 0:
                final_val = base_val * factor
                dose_edit.setText(f"{final_val:.1f} {unit}")
            else:
                dose_edit.clear()

    def clear_doses(self):
        """
        Czyści wartości w kolumnie 'Dawka'.
        """
        for cat_edit, add_edit, dose_edit in self.additive_lines:
            dose_edit.clear()

    def generate_series_number(self) -> str:
        """
        Generuje numer serii w formacie xxxyy_zz na bazie db_manager.
        """
        if not self.db_manager:
            return "00000_00"
        today = date.today()
        mm = today.month
        yyyy = today.year
        current_count = self.db_manager.get_next_series_number_for_month(mm, yyyy)
        return f"{current_count:03d}{mm:02d}_{yyyy}"
