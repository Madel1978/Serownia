# background_screen.py

import os
from typing import Optional
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QFrame,
    QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QResizeEvent


class BackgroundScreen(QMainWindow):
    """
    Bazowa klasa ekranu z automatycznym tłem i półprzezroczystym panelem.
    Dziedzicz po niej w innych ekranach (RegistrationScreen, etc.),
    aby uniknąć duplikowania kodu z tłem.
    """

    def __init__(
        self,
        parent: Optional[QMainWindow] = None,
        bg_image_path: str = r"c:\serownia\images\cheese.jpg",
        panel_width: int = 500
    ) -> None:
        super().__init__(parent)

        # 1. Zapamiętujemy ścieżkę do obrazu
        self.bg_image_path = bg_image_path

        # 2. Główny widget (central)
        self.central_w = QWidget()
        self.setCentralWidget(self.central_w)

        # 3. Layout główny
        self.main_layout = QVBoxLayout(self.central_w)
        self.central_w.setLayout(self.main_layout)

        # 4. QLabel na tło (z QPixmap)
        self.bg_label = QLabel(self.central_w)
        self.bg_label.setScaledContents(True)  # pozwala rozciągać obraz
        self.bg_label.lower()  # tło ma być pod spodem

        abs_path = os.path.abspath(self.bg_image_path)
        self.bg_pixmap = QPixmap(abs_path)

        # 5. Tworzymy półprzezroczysty kontener (QFrame)
        self.form_container = QFrame(self.central_w)
        self.form_container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.85);
                border-radius: 15px;
            }
            QLabel {
                background: transparent;
                border: none;
                color: #333;
            }
        """)
        self.form_container.setFixedWidth(panel_width)

        # Layout w form_container
        self.form_layout = QVBoxLayout(self.form_container)
        self.form_container.setLayout(self.form_layout)

        # 6. Wyśrodkowanie
        self.main_layout.addStretch(1)
        center_hbox = QHBoxLayout()
        center_hbox.addStretch(1)
        center_hbox.addWidget(self.form_container, 0, Qt.AlignCenter)
        center_hbox.addStretch(1)
        self.main_layout.addLayout(center_hbox)
        self.main_layout.addStretch(1)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Automatyczne skalowanie obrazu tła przy zmianie rozmiaru okna.
        """
        super().resizeEvent(event)
        if not self.bg_pixmap.isNull():
            target_size = self.centralWidget().size()
            scaled = self.bg_pixmap.scaled(
                target_size,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            self.bg_label.setPixmap(scaled)
            self.bg_label.resize(target_size)
