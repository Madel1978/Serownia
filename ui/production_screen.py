# c:\serownia\ui\production_screen.py

from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton
from ui.background_screen import BackgroundScreen

class ProductionScreen(BackgroundScreen):
    def __init__(self, parent=None):
        super().__init__(
            parent=parent,
            bg_image_path=r"c:\serownia\images\cheese.jpg",
            panel_width=800  # Lub inna szerokość
        )

        # Ustawiamy tytuł okna (opcjonalnie):
        self.setWindowTitle("Ekran Produkcji")

        # Tworzymy layout siatki (QGridLayout) na przyciski:
        grid_layout = QGridLayout()

        # Definicje przycisków
        buttons = [
            {"name": "Nowa Produkcja", "action": self.new_production},
            {"name": "Baza Produkcji", "action": self.production_base},
            {"name": "Produkty",       "action": self.products},
            {"name": "Receptury",      "action": self.recipes},
            {"name": "Pakowanie",      "action": self.packaging},
        ]

        # Dodaj przyciski do grid_layout
        for i, btn_info in enumerate(buttons):
            button = QPushButton(btn_info["name"])
            button.setStyleSheet("""
                background-color: #ADD8E6;
                color: #000080;
                font-size: 24px;
                font-weight: bold;
                border-radius: 10px;
                padding: 20px;
            """)
            button.clicked.connect(btn_info["action"])

            # Umieszczamy w siatce: wiersz = i // 2, kol = i % 2
            row = i // 2
            col = i % 2
            grid_layout.addWidget(button, row, col)

        # Przycisk Powrót
        back_button = QPushButton("Powrót")
        back_button.setStyleSheet("""
            background-color: #FFCCCC;
            color: #800000;
            font-size: 24px;
            font-weight: bold;
            border-radius: 10px;
            padding: 15px;
        """)
        back_button.clicked.connect(self.go_back_to_start)
        grid_layout.addWidget(back_button, (len(buttons) // 2) + 1, 0, 1, 2)

        # Zamiast self.setLayout(grid_layout), dodajemy do form_layout
        self.form_layout.addLayout(grid_layout)

    # -----------------------
    # Metody dla podkategorii
    # -----------------------

    def new_production(self):
        """Kliknięcie 'Nowa Produkcja'."""
        print("Nowa Produkcja - wywołanie funkcji")
        main_window = self.window()  # Najpewniej <MainWindow ...>
        if hasattr(main_window, "new_production_screen"):
            main_window.show_screen(main_window.new_production_screen)
        else:
            print("Brak atrybutu 'new_production_screen' w MainWindow.")

    def production_base(self):
        """Baza Produkcji - np. show_production_list_screen w MainWindow."""
        print("Baza Produkcji - wywołanie funkcji")
        main_window = self.window()
        if hasattr(main_window, "show_production_list_screen"):
            main_window.show_production_list_screen()
        else:
            print("Brak metody 'show_production_list_screen' w MainWindow.")

    def products(self):
        """Kliknięcie 'Produkty'."""
        print("Produkty - wywołanie funkcji")
        mw = self.window()
        if hasattr(mw, "products_list_screen"):
            mw.show_screen(mw.products_list_screen)
        else:
            print("Brak 'products_list_screen' w MainWindow.")

    def recipes(self):
        """Kliknięcie 'Receptury'."""
        print("Receptury - wywołanie funkcji")
        # Jeżeli chcesz przejść do np. mw.recipes_screen, odkomentuj:
        # mw = self.window()
        # if hasattr(mw, "recipes_screen"):
        #     mw.show_screen(mw.recipes_screen)
        # else:
        #     print("Brak 'recipes_screen' w MainWindow.")

    def packaging(self):
        """Kliknięcie 'Pakowanie'."""
        print("Pakowanie - wywołanie funkcji")
        # Podobnie, do packaging_screen:
        # mw = self.window()
        # if hasattr(mw, "packaging_screen"):
        #     mw.show_screen(mw.packaging_screen)
        # else:
        #     print("Brak 'packaging_screen' w MainWindow.")

    def go_back_to_start(self):
        """Przycisk 'Powrót' - wróć do ekranu startowego."""
        print("Powrót do ekranu startowego.")
        mw = self.window()
        if hasattr(mw, "start_screen"):
            mw.show_screen(mw.start_screen)
        else:
            print("Brak atrybutu 'start_screen' w MainWindow.")
