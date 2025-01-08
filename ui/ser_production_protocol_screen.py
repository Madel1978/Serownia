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
from datetime import date  # Do ustawiania dzisiejszej daty

from database.db_manager import DBManager


def parse_dosage(dosage_str: str) -> Tuple[float, str]:
    """
    Rozdziela tekst w stylu "30 g", "17 ml", "10" itp. na (wartość float, jednostka).
    """
    parts = dosage_str.split()
    if len(parts) == 1:
        try:
            val = float(parts[0].replace(",", "."))
        except ValueError:
            val = 0.0
        return val, ""
    elif len(parts) >= 2:
        try:
            val = float(parts[0].replace(",", "."))
        except ValueError:
            val = 0.0
        unit = parts[1]
        return val, unit
    else:
        return 0.0, ""


class SerProductionProtocolScreen(QWidget):
    """
    Formularz protokołu produkcji 'Ser' z obsługą:
      - load_from_record(record_data): wczytywanie danych z bazowych tablic (production_records, ser_production_details),
      - generowania numeru serii (xxxyy_zz),
      - wypełniania dodatków (do 10 wierszy) z bazy product_additives,
      - przeliczania dawek wg ilości mleka (update_doses),
      - zapisywania danych do production_records + ser_production_details.
    """

    def __init__(
        self, parent: Optional[Any] = None, db_manager: Optional[DBManager] = None
    ):
        super().__init__(parent)
        print(
            "SerProductionProtocolScreen - constructor called!",
            "isVisible=",
            self.isVisible(),
        )
        self.parent = parent
        self.db_manager = db_manager

        self.setWindowTitle("Protokół Produkcji (Ser)")
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

        print(">>> SerProductionProtocolScreen constructor START")

        # Id protokołu (None => nowy)
        self.current_protocol_id: Optional[int] = None

        # Przechowujemy info o dodatkach (wartości bazowe i jednostka) dla max. 10 wierszy
        self.additives_info: List[Tuple[float, str]] = [(0.0, "") for _ in range(10)]

        # ScrollArea + główny layout
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)

        # Sekcje A, B, C, D
        self.create_section_a_params()  # A: Parametry
        self.create_section_b_additives()  # B: Dodatki (3 kolumny)
        self.create_section_c_stages()  # C: 9 czynności
        self.create_section_d_parties()  # D: Ewidencja partii
        self.create_bottom_buttons()  # Dolny pasek (Powrót / Zapisz)

        self.scroll_area.setWidget(self.main_widget)
        outer_layout = QVBoxLayout()
        outer_layout.addWidget(self.scroll_area)
        self.setLayout(outer_layout)

        print(">>> SerProductionProtocolScreen constructor END")

    # ----------------------------------------------------------------
    # A. PARAMETRY (QGridLayout)
    # ----------------------------------------------------------------
    def create_section_a_params(self):
        group = QGroupBox("Parametry wstępne")
        grid = QGridLayout()
        grid.setHorizontalSpacing(40)

        label_width = 195
        field_width = 195

        # 1) Nazwa produktu (Ser)
        lbl_prod = QLabel("Nazwa produktu (Ser):")
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

        # 4) Rodzaj mleka
        lbl_milk_type = QLabel("Rodzaj mleka:")
        lbl_milk_type.setFixedWidth(label_width)
        self.milkType_combo = QComboBox()
        self.milkType_combo.addItems(["Krowie", "Owcze", "Kozie"])
        self.milkType_combo.setFixedWidth(field_width)
        grid.addWidget(lbl_milk_type, 3, 0)
        grid.addWidget(self.milkType_combo, 3, 1)

        # 5) Ilość mleka
        lbl_milk_amt = QLabel("Ilość mleka (litry):")
        lbl_milk_amt.setFixedWidth(label_width)
        self.milkAmount_input = QLineEdit()
        self.milkAmount_input.setFixedWidth(field_width)
        self.milkAmount_input.setPlaceholderText("np. 100.0")
        self.milkAmount_input.textChanged.connect(self.update_doses)
        grid.addWidget(lbl_milk_amt, 4, 0)
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

        # Wypełnienie listy produktów (tylko kategoria "Ser")
        self.fill_ser_products()

    # ----------------------------------------------------------------
    # B. DODATKI – 10 wierszy, 3 kolumny (Kategoria, Dodatek, Dawka)
    # ----------------------------------------------------------------
    def create_section_b_additives(self):
        group = QGroupBox("Dodatki (maks. 10) – [Kategoria | Dodatek | Dawka]")
        vbox = QVBoxLayout()

        # Nagłówki (3 kolumny)
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
        for i in range(10):
            row = QHBoxLayout()

            cat_edit = QLineEdit()
            cat_edit.setFixedWidth(190)

            add_edit = QLineEdit()
            add_edit.setFixedWidth(140)

            dose_edit = QLineEdit()
            dose_edit.setFixedWidth(80)
            dose_edit.setReadOnly(True)  # bo dawka wyliczana dynamicznie

            row.addWidget(cat_edit)
            row.addSpacing(30)
            row.addWidget(add_edit)
            row.addSpacing(30)
            row.addWidget(dose_edit)

            # Teraz mamy tylko 3 pola w każdym wierszu
            self.additive_lines.append((cat_edit, add_edit, dose_edit))
            vbox.addLayout(row)

        group.setLayout(vbox)
        self.main_layout.addWidget(group)

    # ----------------------------------------------------------------
    # C. ETAPY – 9 czynności
    # ----------------------------------------------------------------
    def create_section_c_stages(self):
        """
        Sekcja C: 9 czynności, każda to 2 wiersze w gridzie:
          (1) Dodanie kultur        (Godzina, Czas trwania)
          (2) Podpuszczka           (Godzina, Czas trwania)
          (3) Krojenie              (Godzina, Czas trwania)
          (4) Płukanie ziarna       (Serwatka-, Woda+)
          (5) Dogrzewanie ziarna    (Godzina, Czas trwania)
          (6) Dosuszanie ziarna     (Godzina, Czas trwania)
          (7) Wstępne prasowanie    (Początek, Koniec)
          (8) Formy                 (Wielkość, Ilość)
          (9) Solenie               (Godzina, Czas trwania)
        """

        groupC = QGroupBox("Etapy produkcji (9 czynności)")
        gridC = QGridLayout()
        gridC.setHorizontalSpacing(20)

        label_width = 195
        field_width = 80

        def add_two_rows(
            grid,
            base_row: int,
            nazwa_czynnosci: str,
            opis1: str,
            opis2: str,
            attr1: str,
            attr2: str,
        ):
            """
            Tworzy w gridzie 2 wiersze:
              R1: [puste] | opis1    | opis2
              R2: nazwa   | QLineEdit1 | QLineEdit2

            atrybuty (attr1, attr2) to nazwy pol w 'self' (np. 'dodanie_kultur_start_input').
            """
            # Wiersz 1 (opisy)
            lbl_empty = QLabel("")
            lbl_empty.setFixedWidth(label_width)
            lbl_opis1 = QLabel(opis1)
            lbl_opis2 = QLabel(opis2)

            grid.addWidget(lbl_empty, base_row, 0)
            grid.addWidget(lbl_opis1, base_row, 1)
            grid.addWidget(lbl_opis2, base_row, 2)

            # Wiersz 2 (nazwa czynności, QLineEdit, QLineEdit)
            lbl_czyn = QLabel(nazwa_czynnosci)
            lbl_czyn.setFixedWidth(label_width)

            edit_1 = QLineEdit()
            edit_1.setFixedWidth(field_width)
            edit_2 = QLineEdit()
            edit_2.setFixedWidth(field_width)

            setattr(self, attr1, edit_1)
            setattr(self, attr2, edit_2)

            grid.addWidget(lbl_czyn, base_row + 1, 0)
            grid.addWidget(edit_1, base_row + 1, 1)
            grid.addWidget(edit_2, base_row + 1, 2)

        # 1) Dodanie kultur (Godzina, Czas trwania)
        add_two_rows(
            gridC,
            1,
            "Dodanie kultur",
            "Godzina",
            "Czas trwania",
            "dodanie_kultur_start_input",
            "dodanie_kultur_end_input",
        )

        # 2) Podpuszczka (Godzina, Czas trwania)
        add_two_rows(
            gridC,
            3,
            "Podpuszczka",
            "Godzina",
            "Czas trwania",
            "podpuszczka_start_input",
            "podpuszczka_end_input",
        )

        # 3) Krojenie (Godzina, Czas trwania)
        add_two_rows(
            gridC,
            5,
            "Krojenie",
            "Godzina",
            "Czas trwania",
            "krojenie_start_input",
            "krojenie_end_input",
        )

        # 4) Płukanie ziarna (Serwatka-, Woda+)
        add_two_rows(
            gridC,
            7,
            "Płukanie ziarna",
            "Serwatka-",
            "Woda+",
            "serwatka_start_input",
            "serwatka_end_input",
        )

        # 5) Dogrzewanie ziarna (Godzina, Czas trwania)
        add_two_rows(
            gridC,
            9,
            "Dogrzewanie ziarna",
            "Godzina",
            "Czas trwania",
            "dogrzewanie_start_input",
            "dogrzewanie_end_input",
        )

        # 6) Dosuszanie ziarna (Godzina, Czas trwania)
        add_two_rows(
            gridC,
            11,
            "Dosuszanie ziarna",
            "Godzina",
            "Czas trwania",
            "dosuszanie_start_input",
            "dosuszanie_end_input",
        )

        # 7) Wstępne prasowanie (Początek, Koniec)
        add_two_rows(
            gridC,
            13,
            "Wstępne prasowanie",
            "Początek",
            "Koniec",
            "wstepne_prasowanie_start_input",
            "wstepne_prasowanie_end_input",
        )

        # 8) Formy (Wielkość, Ilość)
        add_two_rows(
            gridC,
            15,
            "Formy",
            "Wielkość",
            "Ilość",
            "formy_wielkosc_input",
            "formy_ilosc_input",
        )

        # 9) Solenie (Godzina, Czas trwania)
        add_two_rows(
            gridC,
            17,
            "Solenie",
            "Godzina",
            "Czas trwania",
            "solenie_start_input",
            "solenie_end_input",
        )

        groupC.setLayout(gridC)
        self.main_layout.addWidget(groupC)

    # ----------------------------------------------------------------
    # D. Ewidencja partii (QGroupBox, 15 wierszy)
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

    # ----------------------------------------------------------------
    # LOGIKA (load_from_record, save_protocol, itp.)
    # ----------------------------------------------------------------
    def go_back(self):
        if hasattr(self.parent, "show_previous_screen"):
            self.parent.show_previous_screen()
        else:
            self.hide()

    def load_from_record(self, record_data: Optional[dict]) -> None:
        """
        Wypełnia formularz danymi z 'record_data' (z production_records).
        Jeśli record_data=None => nowy, pusty protokół (bez ID w production_records).
        """
        if record_data is None:
            # NOWY protokół (brak ID)
            self.current_protocol_id = None

            # [A] – Inicjalizacja sekcji parametrów
            today_str = date.today().strftime("%Y-%m-%d")
            self.date_input.setText(today_str)

            new_series = self.generate_series_number()  # generujemy np. "00105_2024"
            self.series_input.setText(new_series)

            self.milkAmount_input.clear()
            self.ph_input.clear()

            # ComboBox pasteryzacji => domyślnie "Brak"
            idx_pasteur = self.pasteur_combo.findText("Brak")
            if idx_pasteur < 0:
                idx_pasteur = 0
            self.pasteur_combo.setCurrentIndex(idx_pasteur)

            # [C] – 9 czynności => czyścimy wszystkie
            self.dodanie_kultur_start_input.clear()
            self.dodanie_kultur_end_input.clear()
            self.podpuszczka_start_input.clear()
            self.podpuszczka_end_input.clear()
            self.krojenie_start_input.clear()
            self.krojenie_end_input.clear()
            self.serwatka_start_input.clear()
            self.serwatka_end_input.clear()
            self.dogrzewanie_start_input.clear()
            self.dogrzewanie_end_input.clear()
            self.dosuszanie_start_input.clear()
            self.dosuszanie_end_input.clear()
            self.wstepne_prasowanie_start_input.clear()
            self.wstepne_prasowanie_end_input.clear()
            self.formy_wielkosc_input.clear()
            self.formy_ilosc_input.clear()
            self.solenie_start_input.clear()
            self.solenie_end_input.clear()

            # Ustaw combo "Wybierz..." dla produktu (jeśli istnieje)
            if self.product_combo.count() > 0:
                self.product_combo.setCurrentIndex(0)

            # Czyścimy dodatki (sekcja B)
            self.clear_additives_fields()

            print(">>> load_from_record: NOWY / pusty protokół.")
            return

        # -----------------------------------------------------------
        # ISTNIEJĄCY protokół
        # -----------------------------------------------------------
        self.current_protocol_id = record_data.get("id", None)
        date_str = record_data.get("date", "")
        series_str = record_data.get("series", "")
        product_id = record_data.get("product_id", None)

        # [A] – Sekcja parametrów
        self.date_input.setText(date_str)
        self.series_input.setText(series_str)

        # Ustaw produkt w combo
        found_index = -1
        if product_id is not None:
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

        # -----------------------------------------------------------
        # Pobierz szczegóły z ser_production_details
        # -----------------------------------------------------------
        if self.db_manager and self.current_protocol_id is not None:
            details = self.db_manager.get_ser_production_details(
                self.current_protocol_id
            )
            if details:
                # A) Mleko, pH + pasteryzacja
                self.milkAmount_input.setText(details.get("milk_amount", ""))
                self.ph_input.setText(details.get("ph", ""))

                pasteryzacja_str = details.get("pasteryzacja", "Brak")
                idx_pasteur = self.pasteur_combo.findText(pasteryzacja_str)
                if idx_pasteur < 0:
                    idx_pasteur = 0
                self.pasteur_combo.setCurrentIndex(idx_pasteur)

                # B) 9 czynności
                self.dodanie_kultur_start_input.setText(
                    details.get("dodanie_kultur_start", "")
                )
                self.dodanie_kultur_end_input.setText(
                    details.get("dodanie_kultur_end", "")
                )

                self.podpuszczka_start_input.setText(
                    details.get("podpuszczka_start", "")
                )
                self.podpuszczka_end_input.setText(details.get("podpuszczka_end", ""))

                self.krojenie_start_input.setText(details.get("krojenie_start", ""))
                self.krojenie_end_input.setText(details.get("krojenie_end", ""))

                self.serwatka_start_input.setText(details.get("serwatka_start", ""))
                self.serwatka_end_input.setText(details.get("serwatka_end", ""))

                self.dogrzewanie_start_input.setText(
                    details.get("dogrzewanie_start", "")
                )
                self.dogrzewanie_end_input.setText(details.get("dogrzewanie_end", ""))

                self.dosuszanie_start_input.setText(details.get("dosuszanie_start", ""))
                self.dosuszanie_end_input.setText(details.get("dosuszanie_end", ""))

                self.wstepne_prasowanie_start_input.setText(
                    details.get("wstepne_prasowanie_start", "")
                )
                self.wstepne_prasowanie_end_input.setText(
                    details.get("wstepne_prasowanie_end", "")
                )

                self.formy_wielkosc_input.setText(details.get("formy_wielkosc", ""))
                self.formy_ilosc_input.setText(details.get("formy_ilosc", ""))

                self.solenie_start_input.setText(details.get("solenie_start", ""))
                self.solenie_end_input.setText(details.get("solenie_end", ""))
            else:
                # Brak wiersza => czyścimy
                self.milkAmount_input.clear()
                self.ph_input.clear()

                idx_pasteur = self.pasteur_combo.findText("Brak")
                if idx_pasteur < 0:
                    idx_pasteur = 0
                self.pasteur_combo.setCurrentIndex(idx_pasteur)

                self.dodanie_kultur_start_input.clear()
                self.dodanie_kultur_end_input.clear()
                self.podpuszczka_start_input.clear()
                self.podpuszczka_end_input.clear()
                self.krojenie_start_input.clear()
                self.krojenie_end_input.clear()
                self.serwatka_start_input.clear()
                self.serwatka_end_input.clear()
                self.dogrzewanie_start_input.clear()
                self.dogrzewanie_end_input.clear()
                self.dosuszanie_start_input.clear()
                self.dosuszanie_end_input.clear()
                self.wstepne_prasowanie_start_input.clear()
                self.wstepne_prasowanie_end_input.clear()
                self.formy_wielkosc_input.clear()
                self.formy_ilosc_input.clear()
                self.solenie_start_input.clear()
                self.solenie_end_input.clear()

        # -----------------------------------------------------------
        # Wczytujemy dodatki (sekcja B)
        # -----------------------------------------------------------
        if product_id:
            self.fill_additives_from_db(product_id)

        print(
            f">>> load_from_record: protokół ID={self.current_protocol_id}, "
            f"date={date_str}, series={series_str}, product_id={product_id}."
        )

        # Na końcu przelicz dawki:
        self.update_doses()

    def save_protocol(self) -> None:
        """
        Zapisuje / aktualizuje protokół w bazie:
        - production_records (date, series, product_id),
        - ser_production_details_extended (milk_amount, ph, pasteryzacja, 9 czynności),
        - dodatki (3 kolumny: Kategoria, Dodatek, Dawka) w ser_production_additives (bez kolumny 'time').
        """
        if not self.db_manager:
            QMessageBox.warning(self, "Błąd", "Brak db_manager - nie można zapisać.")
            return

        # ----------------------------------------------------------------
        # 1) Odczyt pól sekcji A
        # ----------------------------------------------------------------
        product_id = self.product_combo.currentData()
        date_str = self.date_input.text().strip()
        series_str = self.series_input.text().strip()
        milk_str = self.milkAmount_input.text().strip()
        ph_str = self.ph_input.text().strip()

        # Odczyt z combo pasteryzacji (np. "Brak", "65°C/30min", "85°C/10min")
        pasteryzacja_str = self.pasteur_combo.currentText().strip()

        # Minimalna walidacja
        if not date_str or not series_str or not milk_str:
            QMessageBox.warning(
                self, "Błąd", "Uzupełnij datę, numer serii i ilość mleka."
            )
            return
        if product_id is None or product_id == -1:
            QMessageBox.warning(self, "Błąd", "Nie wybrano poprawnego produktu (Ser).")
            return
        try:
            float(milk_str)
        except ValueError:
            QMessageBox.warning(self, "Błąd", "Ilość mleka musi być liczbą.")
            return

        # ----------------------------------------------------------------
        # 2) Odczyt pól sekcji C – 9 czynności (każda 2 parametry: start/end)
        # ----------------------------------------------------------------
        dodanie_kultur_start_str = self.dodanie_kultur_start_input.text().strip()
        dodanie_kultur_end_str = self.dodanie_kultur_end_input.text().strip()

        podpuszczka_start_str = self.podpuszczka_start_input.text().strip()
        podpuszczka_end_str = self.podpuszczka_end_input.text().strip()

        krojenie_start_str = self.krojenie_start_input.text().strip()
        krojenie_end_str = self.krojenie_end_input.text().strip()

        serwatka_start_str = self.serwatka_start_input.text().strip()
        serwatka_end_str = self.serwatka_end_input.text().strip()

        dogrzewanie_start_str = self.dogrzewanie_start_input.text().strip()
        dogrzewanie_end_str = self.dogrzewanie_end_input.text().strip()

        dosuszanie_start_str = self.dosuszanie_start_input.text().strip()
        dosuszanie_end_str = self.dosuszanie_end_input.text().strip()

        wstepne_prasowanie_start_str = (
            self.wstepne_prasowanie_start_input.text().strip()
        )
        wstepne_prasowanie_end_str = self.wstepne_prasowanie_end_input.text().strip()

        formy_wielkosc_str = self.formy_wielkosc_input.text().strip()
        formy_ilosc_str = self.formy_ilosc_input.text().strip()

        solenie_start_str = self.solenie_start_input.text().strip()
        solenie_end_str = self.solenie_end_input.text().strip()

        # ----------------------------------------------------------------
        # 3) Zapis / aktualizacja w bazie (production_records + ser_production_details_extended)
        # ----------------------------------------------------------------
        try:
            if self.current_protocol_id is None:
                # NOWY rekord
                new_id = self.db_manager.add_production_record_returning_id(
                    date_str, series_str, product_id
                )
                # Dodaj w ser_production_details_extended
                self.db_manager.add_ser_production_details_extended(
                    production_record_id=new_id,
                    milk_amount=milk_str,
                    ph=ph_str,
                    pasteryzacja=pasteryzacja_str,  # nowy argument
                    dodanie_kultur_start=dodanie_kultur_start_str,
                    dodanie_kultur_end=dodanie_kultur_end_str,
                    podpuszczka_start=podpuszczka_start_str,
                    podpuszczka_end=podpuszczka_end_str,
                    krojenie_start=krojenie_start_str,
                    krojenie_end=krojenie_end_str,
                    serwatka_start=serwatka_start_str,
                    serwatka_end=serwatka_end_str,
                    dogrzewanie_start=dogrzewanie_start_str,
                    dogrzewanie_end=dogrzewanie_end_str,
                    dosuszanie_start=dosuszanie_start_str,
                    dosuszanie_end=dosuszanie_end_str,
                    wstepne_prasowanie_start=wstepne_prasowanie_start_str,
                    wstepne_prasowanie_end=wstepne_prasowanie_end_str,
                    formy_wielkosc=formy_wielkosc_str,
                    formy_ilosc=formy_ilosc_str,
                    solenie_start=solenie_start_str,
                    solenie_end=solenie_end_str,
                )
                self.current_protocol_id = new_id
                QMessageBox.information(
                    self, "Sukces", f"Protokół '{series_str}' zapisany (NOWY)."
                )
            else:
                # EDYCJA istniejącego
                self.db_manager.update_production_record(
                    self.current_protocol_id, date_str, series_str, product_id
                )
                self.db_manager.update_ser_production_details_extended(
                    production_record_id=self.current_protocol_id,
                    milk_amount=milk_str,
                    ph=ph_str,
                    pasteryzacja=pasteryzacja_str,
                    dodanie_kultur_start=dodanie_kultur_start_str,
                    dodanie_kultur_end=dodanie_kultur_end_str,
                    podpuszczka_start=podpuszczka_start_str,
                    podpuszczka_end=podpuszczka_end_str,
                    krojenie_start=krojenie_start_str,
                    krojenie_end=krojenie_end_str,
                    serwatka_start=serwatka_start_str,
                    serwatka_end=serwatka_end_str,
                    dogrzewanie_start=dogrzewanie_start_str,
                    dogrzewanie_end=dogrzewanie_end_str,
                    dosuszanie_start=dosuszanie_start_str,
                    dosuszanie_end=dosuszanie_end_str,
                    wstepne_prasowanie_start=wstepne_prasowanie_start_str,
                    wstepne_prasowanie_end=wstepne_prasowanie_end_str,
                    formy_wielkosc=formy_wielkosc_str,
                    formy_ilosc=formy_ilosc_str,
                    solenie_start=solenie_start_str,
                    solenie_end=solenie_end_str,
                )

                QMessageBox.information(
                    self,
                    "Sukces",
                    f"Zaktualizowano protokół '{series_str}' (ID={self.current_protocol_id}).",
                )

            # ----------------------------------------------------------------
            # 4) Zapis dodatków (sekcja B) – 3 kolumny (cat, add, dose)
            # ----------------------------------------------------------------
            record_id = self.current_protocol_id
            self.db_manager.clear_ser_production_additives_for_record(record_id)

            # Zwróć uwagę, że usunęliśmy pole time_edit,
            # więc self.additive_lines = [(cat_edit, add_edit, dose_edit), ...]
            for cat_edit, add_edit, dose_edit in self.additive_lines:
                cat_str = cat_edit.text().strip()
                add_str = add_edit.text().strip()
                dose_val = dose_edit.text().strip()
                if not cat_str and not add_str and not dose_val:
                    continue  # pomijamy wiersz pusty

                # Wstaw do ser_production_additives (3 kolumny: cat, add, dose)
                self.db_manager.add_ser_production_additive_3col(
                    record_id, cat_str, add_str, dose_val
                )

        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się zapisać protokołu: {e}")

    def generate_series_number(self) -> str:
        """Generuje numer serii w formacie xxxyy_zz."""
        if not self.db_manager:
            return "00000_00"
        today = date.today()
        mm = today.month
        yyyy = today.year
        current_count = self.db_manager.get_next_series_number_for_month(mm, yyyy)
        return f"{current_count:03d}{mm:02d}_{yyyy}"

    def fill_ser_products(self):
        """Ładuje listę produktów (kategoria 'Ser') do self.product_combo."""
        if not self.db_manager:
            return
        try:
            self.product_combo.currentIndexChanged.disconnect(self.on_product_changed)
        except TypeError:
            pass

        self.product_combo.clear()
        self.product_combo.addItem("Wybierz...", -1)

        all_products = self.db_manager.get_all_products()
        for p in all_products:
            cat_id = p.get("category_id")
            cat_name = self.get_category_name_by_id(cat_id).lower()
            if cat_name == "ser":
                self.product_combo.addItem(p["name"], p["id"])

        self.product_combo.setCurrentIndex(0)
        self.product_combo.setEnabled(True)

        self.product_combo.currentIndexChanged.connect(self.on_product_changed)

    def clear_additives_fields(self):
        """Czyści 10 wierszy (3 pola)."""
        for i in range(10):
            (cat_edit, add_edit, dose_edit) = self.additive_lines[i]
            cat_edit.clear()
            add_edit.clear()
            dose_edit.clear()
            self.additives_info[i] = (0.0, "")

    def update_doses(self):
        """Przelicza dawki w sekcji B."""
        milk_str = self.milkAmount_input.text().strip()
        if not milk_str:
            self.clear_doses()
            return
        try:
            milk_liters = float(milk_str)
        except ValueError:
            self.clear_doses()
            return

        factor = milk_liters / 100.0
        for i, (cat_edit, add_edit, dose_edit) in enumerate(self.additive_lines):
            base_val, unit = self.additives_info[i]
            if base_val > 0:
                dose_edit.setText(f"{base_val * factor:.1f} {unit}")
            else:
                dose_edit.clear()

    def clear_doses(self):
        """Czyści kolumnę 'Dawka' (sekcja B)."""
        for cat_edit, add_edit, dose_edit in self.additive_lines:
            dose_edit.clear()

    def get_category_name_by_id(self, cat_id: int) -> str:
        """Zwraca nazwę kategorii PRODUKTU (z table product_categories)."""
        if not self.db_manager:
            return ""
        prod_cats = self.db_manager.get_product_categories()
        for c in prod_cats:
            if c["id"] == cat_id:
                return c["name"]
        return ""

    def fill_additives_from_db(self, product_id: int):
        """Wypełnia sekcję B na podstawie product_additives, 3 pola: cat, name, dawka."""
        self.clear_additives_fields()
        if not self.db_manager:
            return
        product_adds = self.db_manager.get_product_additives(product_id)
        for i, pa in enumerate(product_adds):
            if i >= 10:
                break
            add_id = pa["additive_id"]
            dosage_str = pa.get("dosage_per_100", "")
            base_val, unit = parse_dosage(dosage_str)

            add_info = self.db_manager.get_additive_by_id(add_id)
            if not add_info:
                continue
            cat_id = add_info.get("category_id", None)

            # Kategoria = categories
            cat_name = self.get_additive_category_name_by_id(cat_id)
            add_name = add_info.get("name", "")

            (cat_edit, add_edit, dose_edit) = self.additive_lines[i]
            cat_edit.setText(cat_name)
            add_edit.setText(add_name)
            dose_edit.clear()

            self.additives_info[i] = (base_val, unit)

    def get_additive_category_name_by_id(self, cat_id: int) -> str:
        """Zwraca nazwę kategorii dodatku (z table 'categories')."""
        if not self.db_manager:
            return ""
        cats = self.db_manager.get_categories()
        for c in cats:
            if c["id"] == cat_id:
                return c["name"]
        return ""

    def on_product_changed(self, index: int):
        """Gdy user wybierze inny produkt w combo, wypełniamy dodatki i przeliczamy dawki."""
        pid = self.product_combo.currentData()
        if pid and pid != -1:
            self.fill_additives_from_db(pid)
            self.update_doses()
        else:
            self.clear_additives_fields()

    def showEvent(self, event):
        super().showEvent(event)
        print("SerProductionProtocolScreen.showEvent() - I'm being shown!")
