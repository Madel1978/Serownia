# c:\serownia\ui\raporty_screen.py

from typing import Optional
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt

from ui.background_screen import BackgroundScreen


class RaportyScreen(BackgroundScreen):
    """
    Ekran 'Raporty', zawierający placeholder „Tutaj będą raporty”
    oraz przycisk „Powrót” do ekranu startowego.
    """

    def __init__(self, parent: Optional[BackgroundScreen] = None) -> None:
        super().__init__(
            parent=parent,
            bg_image_path=r"c:\serownia\images\cheese.jpg",  # Tło
            panel_width=800,
        )
        self.setWindowTitle("Raporty")

        # Tworzymy layout pionowy na zawartość
        layout = QVBoxLayout()

        # Placeholder
        label = QLabel("Tutaj będą raporty.")
        label.setStyleSheet("font-size: 16px; padding: 20px;")
        layout.addWidget(label)

        # Przycisk „Powrót”
        back_button = QPushButton("Powrót")
        back_button.setStyleSheet(
            """
            background-color: #FFCCCC;
            color: #800000;
            font-size: 24px;
            font-weight: bold;
            border-radius: 10px;
            padding: 15px;
        """
        )
        back_button.clicked.connect(self.go_back_to_start)
        layout.addWidget(back_button)

        # Zamiast setCentralWidget(...) – dodajemy layout do form_layout
        self.form_layout.addLayout(layout)

    def go_back_to_start(self) -> None:
        """
        Przycisk „Powrót” – wraca do ekranu startowego (start_screen) z MainWindow.
        """
        mw = self.window()  # Najpewniej MainWindow
        if hasattr(mw, "start_screen"):
            mw.show_screen(mw.start_screen)
        else:
            # Fallback: chowamy to okno (lub cokolwiek innego)
            self.hide()
