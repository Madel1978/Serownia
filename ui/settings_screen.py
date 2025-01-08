# c:\serownia\ui\settings_screen.py

from typing import Optional, Any

from PyQt5.QtWidgets import (
    QGridLayout, QPushButton
)
from PyQt5.QtCore import Qt

# Zależnie od Twojej struktury
from database.db_manager import DBManager
from ui.background_screen import BackgroundScreen

class SettingsScreen(BackgroundScreen):
    """
    Ekran ustawień, zawierający przyciski do zarządzania:
      - kontem użytkownika,
      - kategoriami produktów (CRUD),
      - kategoriami dodatków (CRUD),
      - kategoriami opakowań (CRUD),
      - (opcjonalnie) „Produkty”,
      - przycisk "Użytkownicy",
      - przycisk "Powrót" (do ekranu startowego).
    """

    def __init__(
        self,
        parent: Optional[Any] = None,
        db_manager: Optional[DBManager] = None
    ) -> None:
        """
        Inicjalizuje ekran ustawień, tworzy układ siatki (QGridLayout) z przyciskami
        do poszczególnych podkategorii.

        :param parent: Najczęściej MainWindow (zawiera show_screen).
        :param db_manager: Obiekt DBManager do zarządzania bazą danych.
        """
        super().__init__(
            parent=parent,
            bg_image_path=r"c:\serownia\images\cheese.jpg",
            panel_width=800
        )

        self.db_manager = db_manager
        self.setWindowTitle("Ustawienia")

        # Tworzymy layout siatki
        grid_layout = QGridLayout()

        # Definicje przycisków dla podkategorii
        buttons = [
            {"name": "Moje konto",          "screen": "account_screen"},
            {"name": "Kategorie produktów", "screen": "product_categories_crud_screen"},
            {"name": "Kategorie dodatków",  "screen": "additive_categories_crud_screen"},
            {"name": "Kategorie opakowań",  "screen": "packaging_categories_crud_screen"},
            # {"name": "Produkty",          "screen": "products_list_screen"},  # odkomentuj, jeśli potrzebne
        ]

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
            # Tworzymy lambda, która wywoła metodę _navigate_to_screen
            button.clicked.connect(lambda _, s=btn_info["screen"]: self._navigate_to_screen(s))

            grid_layout.addWidget(button, i // 2, i % 2)

        # Przycisk "Użytkownicy"
        users_button = QPushButton("Użytkownicy")
        users_button.setStyleSheet("""
            background-color: #ADD8E6;
            color: #000080;
            font-size: 24px;
            font-weight: bold;
            border-radius: 10px;
            padding: 20px;
        """)
        users_button.clicked.connect(self.manage_users)
        row_for_users = (len(buttons) // 2) + 1
        grid_layout.addWidget(users_button, row_for_users, 0)

        # Przycisk "Powrót"
        back_button = QPushButton("Powrót")
        back_button.setStyleSheet("""
            background-color: #FFCCCC;
            color: #800000;
            font-size: 24px;
            font-weight: bold;
            border-radius: 10px;
            padding: 15px;
        """)
        back_button.clicked.connect(lambda: self._navigate_to_screen("start_screen"))
        grid_layout.addWidget(back_button, row_for_users + 1, 0, 1, 2)

        # Zamiast self.setLayout(grid_layout), dodajemy do form_layout
        self.form_layout.addLayout(grid_layout)

    def _navigate_to_screen(self, screen_attr_name: str) -> None:
        """
        Pomocnicza metoda, która wyszukuje w obiekcie MainWindow (self.window())
        atrybut o nazwie screen_attr_name i przełącza na ten ekran
        korzystając z window().show_screen().
        """
        mw = self.window()
        if not mw or not hasattr(mw, "show_screen"):
            print("Brak głównego okna lub metody show_screen.")
            return

        screen = getattr(mw, screen_attr_name, None)
        if screen is not None:
            mw.show_screen(screen)
        else:
            print(f"Nie znaleziono ekranu '{screen_attr_name}' w MainWindow.")

    def manage_users(self) -> None:
        """
        Metoda wywoływana po kliknięciu przycisku 'Użytkownicy'.
        Na razie tylko print, w przyszłości można przejść do ekranu zarządzania użytkownikami.
        """
        print("Zarządzanie użytkownikami (w fazie planowania).")
