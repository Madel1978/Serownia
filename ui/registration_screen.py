from typing import Optional

from PyQt5.QtWidgets import (
    QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from database.db_manager import DBManager
from ui.background_screen import BackgroundScreen

class RegistrationScreen(BackgroundScreen):
    def __init__(self, parent=None, db_manager: Optional[DBManager] = None):
        super().__init__(parent, bg_image_path=r"c:\serownia\images\cheese.jpg", panel_width=500)
        
        self.db_manager = db_manager
        self.setWindowTitle("Rejestracja")
        self.setGeometry(100, 100, 800, 600)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Wprowadź nazwę użytkownika")
        self.form_layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Wprowadź hasło")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.form_layout.addWidget(self.password_input)

        register_button = QPushButton("Zarejestruj")
        register_button.clicked.connect(self.handle_register)
        self.form_layout.addWidget(register_button)

        back_button = QPushButton("Powrót")
        back_button.clicked.connect(lambda: self._navigate_to_screen("login_screen"))
        self.form_layout.addWidget(back_button)

    def handle_register(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Błąd", "Wszystkie pola muszą być wypełnione.")
            return

        if not self.db_manager:
            QMessageBox.critical(self, "Błąd", "Brak obiektu db_manager – rejestracja niemożliwa.")
            return

        try:
            self.db_manager.add_user(username, password)
            QMessageBox.information(self, "Sukces", f"Konto '{username}' utworzone.")
            self.username_input.clear()
            self.password_input.clear()
            self._navigate_to_screen("login_screen")
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się zarejestrować: {e}")

    def _navigate_to_screen(self, screen_name: str) -> None:
        mw = self.window()
        if hasattr(mw, 'show_screen'):
            screen = getattr(mw, screen_name, None)
            if screen:
                mw.show_screen(screen)
