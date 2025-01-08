# c:\serownia\ui\login_screen.py

from typing import Optional, Any
import os

from PyQt5.QtWidgets import (
    QLineEdit,
    QLabel,
    QPushButton,
    QWidget,
    QMessageBox,
    QCheckBox,
    QHBoxLayout,
    QVBoxLayout,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from ui.background_screen import BackgroundScreen


class LoginScreen(BackgroundScreen):
    """
    Ekran logowania, w którym zamiast etykiet „Nazwa użytkownika” i „Hasło”
    używamy ikon (np. człowieczka i klucza) obok pól wprowadzania.
    """

    def __init__(
        self, parent: Optional[QWidget] = None, db_manager: Optional[Any] = None
    ):
        super().__init__(
            parent=parent,
            bg_image_path=r"c:\serownia\images\cheese.jpg",  # Tło
            panel_width=800,  # szerokość panelu
        )

        self.db_manager = db_manager
        self.setWindowTitle("LOGOWANIE")

        # ------------------ Nagłówek „LOGOWANIE” ------------------
        self.header_label = QLabel("LOGOWANIE")
        self.header_label.setStyleSheet(
            """
            font-size: 24px;
            font-weight: bold;
            background: transparent;
            border: none;
        """
        )
        self.header_label.setAlignment(Qt.AlignCenter)
        self.form_layout.addWidget(self.header_label)

        # ------------------ Wiersz: ikona + pole "Nazwa użytkownika" ------------------
        user_layout = QHBoxLayout()

        # Ikonka człowieczka:
        self.user_icon_label = QLabel()
        user_icon_path = (
            r"c:\serownia\images\user_icon.png"  # <-- Dostaw faktyczną ścieżkę do pliku
        )
        if os.path.exists(user_icon_path):
            self.user_icon_label.setPixmap(
                QPixmap(user_icon_path).scaled(
                    32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
        else:
            self.user_icon_label.setText("👤")  # fallback emoji
        self.user_icon_label.setStyleSheet("background: transparent;")

        # Pole nazwy użytkownika:
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Wpisz swoją nazwę użytkownika")
        self.username_input.setStyleSheet(
            """
            font-size: 24px;
            border-radius: 10px;
            padding: 8px;
        """
        )

        user_layout.addWidget(self.user_icon_label)
        user_layout.addWidget(self.username_input)
        self.form_layout.addLayout(user_layout)

        # ------------------ Wiersz: ikona + pole "Hasło" ------------------
        pass_layout = QHBoxLayout()

        # Ikonka klucza:
        self.key_icon_label = QLabel()
        key_icon_path = r"c:\serownia\images\key_icon.png"
        if os.path.exists(key_icon_path):
            self.key_icon_label.setPixmap(
                QPixmap(key_icon_path).scaled(
                    32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
        else:
            self.key_icon_label.setText("🔑")  # fallback emoji
        self.key_icon_label.setStyleSheet("background: transparent;")

        # Pole hasła:
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Wpisz swoje hasło")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(
            """
            font-size: 24px;
            border-radius: 10px;
            padding: 8px;
        """
        )

        pass_layout.addWidget(self.key_icon_label)
        pass_layout.addWidget(self.password_input)
        self.form_layout.addLayout(pass_layout)

        # ------------------ CheckBox „Pokaż hasło” ------------------
        self.show_password_checkbox = QCheckBox("Pokaż hasło")
        self.show_password_checkbox.setStyleSheet("font-size: 16px;")  # ewentualnie
        self.show_password_checkbox.stateChanged.connect(
            self._toggle_password_visibility
        )
        self.form_layout.addWidget(self.show_password_checkbox)

        # ------------------ Przycisk „Zaloguj się” ------------------
        self.login_button = QPushButton("Zaloguj się")
        self.login_button.setStyleSheet(
            """
            background-color: #00BFFF;
            color: white;
            font-weight: bold;
            border-radius: 5px;
            padding: 10px 20px;
            font-size: 24px;
        """
        )
        self.login_button.clicked.connect(self.attempt_login)
        self.form_layout.addWidget(self.login_button)

        # ------------------ Link „Zapomniałem hasła” ------------------
        self.forgot_button = QPushButton("Zapomniałem hasła")
        self.forgot_button.setStyleSheet(
            """
            background-color: transparent;
            color: #333;
            text-decoration: underline;
            border: none;
            margin-top: 5px;
        """
        )
        # self.forgot_button.clicked.connect(...)
        self.form_layout.addWidget(self.forgot_button)

        # ------------------ Przycisk „Zarejestruj się” ------------------
        self.register_button = QPushButton("Zarejestruj się")
        self.register_button.setStyleSheet(
            """
            background-color: #FFC0CB;
            color: #800000;
            font-weight: bold;
            border-radius: 5px;
            padding: 10px 20px;
            margin-top: 5px;
            font-size: 24px;
        """
        )
        self.register_button.clicked.connect(self.go_to_registration)
        self.form_layout.addWidget(self.register_button)

    # -------------------- Metody obsługi logowania --------------------

    def _toggle_password_visibility(self, state: int) -> None:
        """
        Pokazuje/ukrywa hasło w zależności od stanu CheckBoxa.
        """
        if state == Qt.Checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def attempt_login(self) -> None:
        """
        Sprawdza dane logowania i wywołuje self.window().login_user(username),
        jeśli parent to MainWindow i ma taką metodę.
        """
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(
                self, "Błąd", "Nazwa użytkownika i hasło nie mogą być puste."
            )
            return

        if self.db_manager and self.db_manager.verify_user(username, password):
            # Jeśli parent to MainWindow, i ma metodę login_user
            mw = self.window()
            if hasattr(mw, "login_user"):
                mw.login_user(username)
            else:
                QMessageBox.warning(
                    self,
                    "Błąd",
                    "Brak metody window().login_user – nie można kontynuować.",
                )
        else:
            QMessageBox.warning(
                self, "Błąd", "Niepoprawna nazwa użytkownika lub hasło."
            )

    def go_to_registration(self) -> None:
        """
        Przełącza widok na ekran rejestracji (registration_screen).
        """
        mw = self.window()
        if hasattr(mw, "show_screen") and hasattr(mw, "registration_screen"):
            mw.show_screen(mw.registration_screen)
        else:
            QMessageBox.warning(
                self,
                "Błąd",
                "Brak ekranu rejestracji lub metody show_screen w oknie głównym.",
            )
