# c:\serownia\ui\magazyn_screen.py

from typing import Optional
from PyQt5.QtWidgets import QGridLayout, QPushButton
from ui.background_screen import BackgroundScreen

class MagazynScreen(BackgroundScreen):
    """
    Ekran 'Magazyn', zawierający przyciski do nawigacji między różnymi
    widokami związanymi z magazynowaniem (Dodatki, Opakowania, Rejestry).
    """

    def __init__(self, parent: Optional[BackgroundScreen] = None) -> None:
        """
        Inicjalizuje ekran 'Magazyn' i tworzy układ (QGridLayout) z przyciskami:
          - Dodatki
          - Opakowania
          - Rejestr Dodatków
          - Rejestr Opakowań
          - Powrót (do ekranu startowego)

        :param parent: Najczęściej MainWindow (zawiera show_screen i atrybuty).
        """
        super().__init__(
            parent=parent,
            bg_image_path=r"c:\serownia\images\cheese.jpg",
            panel_width=800
        )

        self.setWindowTitle("Magazyn – Ekran główny")

        # Tworzymy layout siatki
        grid_layout = QGridLayout()

        # Przyciski dla podkategorii
        buttons = [
            {"name": "Dodatki",           "action": self.show_additives},
            {"name": "Opakowania",        "action": self.show_packaging},
            {"name": "Rejestr Dodatków",  "action": self.show_additives_register},
            {"name": "Rejestr Opakowań",  "action": self.show_packaging_register},
        ]

        for i, btn_info in enumerate(buttons):
            button = QPushButton(btn_info["name"])
            button.setStyleSheet("""
                background-color: #87CEEB; /* jasnoniebieski */
                color: #000080;
                font-size: 24px;
                font-weight: bold;
                border-radius: 10px;
                padding: 30px;
            """)
            button.clicked.connect(btn_info["action"])
            grid_layout.addWidget(button, i // 2, i % 2)

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
        grid_layout.addWidget(
            back_button,
            (len(buttons) // 2) + 1, 0,
            1, 2
        )

        # Zamiast self.setLayout(grid_layout), dodajemy do form_layout
        self.form_layout.addLayout(grid_layout)

    # -----------
    # Metody akcji
    # -----------

    def show_additives(self) -> None:
        """
        Przejście do widoku 'Lista Dodatków' (self.window().additives_list_screen).
        """
        print("Wywołano show_additives()")
        mw = self.window()
        if hasattr(mw, 'show_screen') and hasattr(mw, 'additives_list_screen'):
            mw.show_screen(mw.additives_list_screen)

    def show_packaging(self) -> None:
        """
        Przejście do widoku 'Lista Opakowań' (self.window().packaging_list_screen).
        """
        print("Wywołano show_packaging()")
        mw = self.window()
        if hasattr(mw, 'show_screen') and hasattr(mw, 'packaging_list_screen'):
            mw.show_screen(mw.packaging_list_screen)

    def show_additives_register(self) -> None:
        """
        Przejście do widoku 'Rejestr Dodatków' (self.window().additives_register_screen).
        """
        print("Wywołano show_additives_register()")
        mw = self.window()
        if hasattr(mw, 'show_screen') and hasattr(mw, 'additives_register_screen'):
            mw.show_screen(mw.additives_register_screen)

    def show_packaging_register(self) -> None:
        """
        Przejście do widoku 'Rejestr Opakowań' (self.window().packaging_register_screen).
        """
        print("Wywołano show_packaging_register()")
        mw = self.window()
        if hasattr(mw, 'show_screen') and hasattr(mw, 'packaging_register_screen'):
            mw.show_screen(mw.packaging_register_screen)

    def go_back_to_start(self) -> None:
        """
        Przycisk 'Powrót' – przejście do ekranu startowego.
        """
        print("Powrót do ekranu startowego.")
        mw = self.window()
        if hasattr(mw, 'show_screen') and hasattr(mw, 'start_screen'):
            mw.show_screen(mw.start_screen)
