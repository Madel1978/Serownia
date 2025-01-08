# c:\serownia\ui\start_screen.py

from PyQt5.QtWidgets import QPushButton, QGridLayout
from ui.background_screen import BackgroundScreen

class StartScreen(BackgroundScreen):
    """
    Ekran startowy aplikacji, zawiera główne przyciski nawigacyjne
    (Produkcja, Magazyn, Raporty, Ustawienia).
    """

    def __init__(self, parent=None):
        """
        Inicjalizuje ekran startowy i ustawia layout z przyciskami.
        :param parent: Okno nadrzędne, zazwyczaj instancja MainWindow.
        """
        super().__init__(
            parent=parent,
            bg_image_path=r"c:\serownia\images\cheese.jpg",
            panel_width=800  # Możesz dostosować szerokość panelu
        )
        self.setWindowTitle("Ekran startowy")

        # Zamiast QVBoxLayout czy QHBoxLayout używamy QGridLayout
        layout = QGridLayout()

        # Definicje przycisków z powiązaną akcją
        buttons = [
            {
                "name": "Produkcja",
                "action": lambda: self._navigate_to_screen("production_screen")
            },
            {
                "name": "Magazyn",
                "action": lambda: self._navigate_to_screen("magazyn_screen")
            },
            {
                "name": "Raporty",
                "action": lambda: self._navigate_to_screen("raporty_screen")
            },
            {
                "name": "Ustawienia",
                "action": lambda: self._navigate_to_screen("settings_screen")
            },
        ]

        # Dodaj przyciski do siatki (2 wiersze x 2 kolumny)
        for i, btn_info in enumerate(buttons):
            button = QPushButton(btn_info["name"])
            button.setStyleSheet("""
                background-color: #ADD8E6;  /* Kolor błękitny */
                color: #000080;            /* Granatowy tekst */
                font-size: 24px;
                font-weight: bold;
                border-radius: 15px;       /* Zaokrąglone rogi */
                padding: 30px;
                border: 2px solid #87CEEB; /* Jasnoniebieska obwódka */
            """)
            button.clicked.connect(btn_info["action"])

            # Wstawienie do siatki: wiersz i kolumnę liczymy z i // 2, i % 2
            row = i // 2
            col = i % 2
            layout.addWidget(button, row, col)

        # Dodaj layout do panelu form_layout z klasy bazowej
        self.form_layout.addLayout(layout)

    def _navigate_to_screen(self, screen_attribute_name: str) -> None:
        """
        Pomocnicza metoda nawigująca do określonego ekranu w MainWindow.

        :param screen_attribute_name: np. "production_screen", "magazyn_screen" itp.
        """
        # Najbezpieczniej użyć self.window(), bo parent() bywa QStackedWidget
        main_window = self.window()
        if not main_window or not hasattr(main_window, 'show_screen'):
            return  # Albo wyświetl QMessageBox z błędem

        screen = getattr(main_window, screen_attribute_name, None)
        if screen:
            main_window.show_screen(screen)
        else:
            # Tu można ewentualnie obsłużyć brak ekranu
            pass
