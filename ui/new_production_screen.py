# c:\serownia\ui\new_production_screen.py

from typing import Optional, Any

from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QGridLayout, QPushButton, QMessageBox
from PyQt5.QtCore import Qt

from ui.background_screen import BackgroundScreen


class NewProductionScreen(BackgroundScreen):
    """
    Główny ekran 'Nowa Produkcja' – dziedziczący po BackgroundScreen,
    dzięki czemu ma to samo tło (cheese.jpg) i półprzezroczysty panel.
    """

    def __init__(self, parent: Optional[Any] = None) -> None:
        super().__init__(
            parent=parent,
            bg_image_path=r"c:\serownia\images\cheese.jpg",
            panel_width=800,  # Możesz dostosować szerokość panelu
        )

        self.setWindowTitle("Nowa Produkcja")

        # Główny layout siatkowy, do którego dodamy przyciski kategorii i "Powrót"
        self.grid_layout = QGridLayout()
        self.form_layout.addLayout(self.grid_layout)

        # Flaga, by uniknąć wielokrotnego ładowania kategorii
        self.categories_loaded = False

    def showEvent(self, event: QShowEvent) -> None:
        """
        Wywoływane, gdy widget jest WYŚWIETLANY w QStackedWidget.
        Tutaj ładujemy kategorie z db_manager – bo tu self.window() jest MainWindow.
        """
        super().showEvent(event)

        if not self.categories_loaded:
            self.load_categories_and_create_buttons()
            self.categories_loaded = True

    def load_categories_and_create_buttons(self) -> None:
        """
        Pobiera kategorie produktów z bazy (mw.db_manager) i tworzy przyciski (2 kolumny).
        Po dodaniu kafelków w siatce, wstawiamy przycisk „Powrót” z rozpiętością.
        """
        mw = self.window()
        if not mw or not hasattr(mw, "db_manager") or not mw.db_manager:
            QMessageBox.warning(self, "Błąd", "Brak db_manager w MainWindow.")
            return

        db_manager = mw.db_manager
        categories = db_manager.get_product_categories()
        if not categories:
            QMessageBox.information(self, "Info", "Brak kategorii produktów w bazie.")
            return

        # Tworzymy przyciski dla każdej kategorii w siatce (2 kolumny)
        for i, cat in enumerate(categories):
            cat_name = cat["name"]
            btn = QPushButton(cat_name)
            btn.setStyleSheet(
                """
                background-color: #ADD8E6;
                color: #000080;
                font-size: 24px;
                font-weight: bold;
                border-radius: 10px;
                padding: 20px;
            """
            )
            # Kliknięcie przycisku – obsługa danej kategorii
            btn.clicked.connect(
                lambda _, cname=cat_name: self.on_category_clicked_by_name(cname)
            )

            row = i // 2
            col = i % 2
            self.grid_layout.addWidget(btn, row, col)

        # Teraz dodajemy przycisk „Powrót” w nowym wierszu, rozciągnięty na 2 kolumny
        row_for_back = (len(categories) // 2) + 1  # wiersz poniżej ostatniego przycisku
        back_button = QPushButton("Powrót")
        back_button.setStyleSheet(
            """
            background-color: #FFCCCC;
            color: #800000;
            font-size: 24px;
            font-weight: bold;
            border-radius: 10px;
            padding: 10px 20px;
        """
        )
        back_button.clicked.connect(self.go_back)

        # Dodajemy w wierszu row_for_back, kolumna 0, obejmując 1 wiersz, 2 kolumny
        self.grid_layout.addWidget(back_button, row_for_back, 0, 1, 2)

    def go_back(self) -> None:
        """
        Obsługuje powrót do poprzedniego ekranu, jeśli MainWindow oferuje show_previous_screen().
        """
        mw = self.window()
        if hasattr(mw, "show_previous_screen"):
            mw.show_previous_screen()
        else:
            self.hide()

    def on_category_clicked_by_name(self, category_name: str) -> None:
        """
        Obsługa kliknięcia kategorii. Sprawdza w MainWindow słownik
        protocol_screens_by_name i przełącza na odpowiedni protokół.
        """
        print(f"[NewProductionScreen] Kliknięto kategorię='{category_name}'.")

        mw = self.window()
        if not mw or not hasattr(mw, "protocol_screens_by_name"):
            QMessageBox.information(
                self,
                "Info",
                f"Brak słownika 'protocol_screens_by_name' w MainWindow.\n"
                f"Nie obsługuję protokołu dla '{category_name}'.",
            )
            return

        proto_dict = mw.protocol_screens_by_name
        if category_name in proto_dict:
            screen = proto_dict[category_name]
            # Załóżmy, że protokół ma metodę load_from_record(None)
            if hasattr(screen, "load_from_record"):
                screen.load_from_record(None)
            else:
                QMessageBox.warning(
                    self,
                    "Błąd",
                    f"Ekran protokołu '{category_name}' nie ma metody 'load_from_record'.",
                )
                return
            mw.show_screen(screen)
        else:
            QMessageBox.information(
                self,
                "Brak ekranu",
                f"Nie zaimplementowano protokołu dla kategorii '{category_name}'.",
            )
