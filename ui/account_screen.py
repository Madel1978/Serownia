import hashlib
import logging
from typing import Optional, Dict

from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QWidget, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt

from database.db_manager import DBManager  # Zależnie od Twojej struktury projektu

# Ustawienia loggera – w większych projektach można to zrobić w osobnym module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def hash_password(password: str) -> str:
    """
    Przykładowe (bardzo uproszczone) hashowanie hasła.
    W praktyce lepiej używać bibliotek typu bcrypt/argon2 (passlib),
    aby bezpiecznie zarządzać solą i kosztami obliczeń.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class AccountScreen(QMainWindow):
    """
    Ekran konta użytkownika, pozwalający:
      - wyświetlić nazwę użytkownika,
      - zmienić jego hasło (z użyciem hashowania),
      - wrócić do poprzedniego ekranu.
    """

    def __init__(
        self,
        parent: Optional[QMainWindow] = None,
        db_manager: Optional[DBManager] = None
    ) -> None:
        """
        Inicjalizuje ekran 'Moje Konto'.

        :param parent: Okno-rodzic (zazwyczaj instancja MainWindow).
        :param db_manager: Obiekt DBManager do komunikacji z bazą danych.
        """
        super().__init__(parent)

        self.parent = parent
        self.db_manager = db_manager
        self.user_data: Optional[Dict] = None  # Dane aktualnie zalogowanego użytkownika

        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        Tworzy i konfiguruje wszystkie elementy interfejsu (layout, pola, przyciski).
        """
        self.setWindowTitle("Moje Konto")
        self.setGeometry(100, 100, 800, 600)

        # Główny widget i layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # 1. Etykieta z nazwą użytkownika
        self.username_label = QLabel("Nazwa użytkownika:")
        layout.addWidget(self.username_label)

        # 2. Pole do zmiany hasła
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Wprowadź nowe hasło")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        # 3. CheckBox "Pokaż hasło"
        self.show_password_checkbox = QCheckBox("Pokaż hasło")
        self.show_password_checkbox.stateChanged.connect(self._toggle_password_visibility)
        layout.addWidget(self.show_password_checkbox)

        # 4. Przycisk do zapisania zmian
        save_button = QPushButton("Zapisz zmiany")
        save_button.setStyleSheet("""
            background-color: #ADD8E6;
            color: #000080;
            font-size: 14px;
            font-weight: bold;
            border-radius: 10px;
            padding: 15px;
        """)
        save_button.clicked.connect(self.save_changes)
        layout.addWidget(save_button)

        # 5. Przycisk powrotu
        back_button = QPushButton("Powrót")
        back_button.setStyleSheet("""
            background-color: #FFCCCC;
            color: #800000;
            font-size: 14px;
            font-weight: bold;
            border-radius: 10px;
            padding: 10px;
        """)
        back_button.clicked.connect(self._go_back)
        layout.addWidget(back_button)

    # ----------------------------------------------------------------
    # ---------------------- ŁADOWANIE DANYCH ------------------------
    # ----------------------------------------------------------------

    def load_user_data(self, username: str) -> None:
        """
        Ładuje dane zalogowanego użytkownika z bazy danych i wyświetla jego nazwę.
        Wywołaj tę metodę po zalogowaniu użytkownika.
        """
        if not self.db_manager:
            QMessageBox.warning(self, "Błąd", "Brak db_manager – nie można pobrać danych użytkownika.")
            return

        self.user_data = self.db_manager.get_user_by_username(username)

        if self.user_data:
            logger.info(f"Załadowano dane użytkownika: {self.user_data}")
            self.username_label.setText(f"Nazwa użytkownika: {self.user_data['username']}")
        else:
            QMessageBox.warning(self, "Błąd", "Nie znaleziono danych użytkownika w bazie.")

    # ----------------------------------------------------------------
    # --------------------- ZAPIS HASŁA (SAVE) -----------------------
    # ----------------------------------------------------------------

    def save_changes(self) -> None:
        """
        Zapisuje zmiany w danych użytkownika (obecnie tylko nowe hasło).
        Hasło jest walidowane i hashowane przed zapisem do bazy.
        """
        if not self.user_data:
            QMessageBox.warning(self, "Błąd", "Brak danych użytkownika – nie można zmienić hasła.")
            return

        new_password = self.password_input.text().strip()
        if not new_password:
            QMessageBox.warning(self, "Błąd", "Hasło nie może być puste.")
            return

        # Walidacja hasła (przykładowa, minimalna długość)
        if not self.validate_password(new_password):
            QMessageBox.warning(self, "Błąd", "Hasło musi mieć co najmniej 8 znaków!")
            return

        # Hashowanie hasła (przykład)
        hashed_pw = hash_password(new_password)

        if not self.db_manager:
            QMessageBox.warning(self, "Błąd", "Brak db_manager – nie można zaktualizować hasła.")
            return

        # Próba zapisu w DB
        try:
            self.db_manager.update_user_password(self.user_data['username'], hashed_pw)
            QMessageBox.information(self, "Sukces", "Hasło zostało zmienione.")
            self.password_input.clear()
        except Exception as e:
            logger.error(f"Błąd przy aktualizacji hasła: {e}")
            QMessageBox.critical(self, "Błąd", f"Nie udało się zaktualizować hasła. {str(e)}")

    def validate_password(self, password: str) -> bool:
        """
        Przykładowa prosta walidacja nowego hasła:
         - Sprawdza minimalną długość (8).
         - W razie potrzeby można dodać warunki (cyfry, duże litery, znaki specjalne).
        """
        return len(password) >= 8

    # ----------------------------------------------------------------
    # --------------- POKAŻ / UKRYJ HASŁO (CHECKBOX) -----------------
    # ----------------------------------------------------------------

    def _toggle_password_visibility(self, state: int) -> None:
        """
        Pokazuje/ukrywa hasło w zależności od stanu CheckBoxa.
        """
        if state == Qt.Checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    # ----------------------------------------------------------------
    # --------------------------- POWRÓT -----------------------------
    # ----------------------------------------------------------------

    def _go_back(self) -> None:
        """
        Obsługuje powrót do ekranu ustawień (settings_screen).
        Jeśli się nie powiedzie, zamyka obecne okno (fallback).
        """
        if self.parent and hasattr(self.parent, 'show_screen'):
            self.parent.show_screen(self.parent.settings_screen)
        else:
            QMessageBox.warning(
                self,
                "Uwaga",
                "Nie można wrócić do poprzedniego ekranu – zamykam okno."
            )
            self.close()
