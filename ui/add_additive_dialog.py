from typing import Optional, Any

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt


class AddAdditiveDialog(QDialog):
    """
    Dialog umożliwiający dodanie nowego dodatku. 
    W tej zmodyfikowanej wersji usunięto pola „Waga” i „Dawkowanie”,
    tak aby zapisywać tylko nazwę dodatku oraz kategorię.
    """

    def __init__(
        self,
        parent: Optional[Any] = None,  # Najczęściej QMainWindow lub inny widok-rodzic
        db_manager: Optional[Any] = None  # Docelowo: Optional[DBManager]
    ) -> None:
        """
        Inicjalizuje dialog do dodania nowego dodatku (bez wagi i dawkowania).

        :param parent: Okno-rodzic (np. AdditivesListScreen).
        :param db_manager: Obiekt bazy danych (DBManager).
        """
        super().__init__(parent)
        self.db_manager = db_manager

        self.setWindowTitle("Dodaj nowy dodatek")
        self.setGeometry(400, 300, 300, 180)

        layout = QVBoxLayout(self)

        # Pole: Nazwa dodatku
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nazwa dodatku (wymagane)")
        layout.addWidget(QLabel("Nazwa dodatku:"))
        layout.addWidget(self.name_input)

        # Wybór kategorii (QComboBox)
        self.category_combo = QComboBox()
        layout.addWidget(QLabel("Kategoria dodatku:"))
        layout.addWidget(self.category_combo)

        # Wypełnij combo listą kategorii z bazy
        self.fill_categories()

        # Przycisk "Zapisz"
        save_button = QPushButton("Zapisz")
        save_button.clicked.connect(self.save_data)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def fill_categories(self) -> None:
        """
        Pobiera listę kategorii z bazy i wypełnia QComboBox parą (nazwa, id).
        Zakładamy, że db_manager.get_categories() zwraca listę słowników:
            [{"id": 1, "name": "Kultury starterowe"}, ...].
        """
        if not self.db_manager:
            QMessageBox.critical(
                self,
                "Błąd",
                "Brak db_manager – nie można wczytać kategorii."
            )
            return

        categories = self.db_manager.get_categories()
        for cat in categories:
            self.category_combo.addItem(cat["name"], cat["id"])

    def save_data(self) -> None:
        """
        Zapisuje dane (nazwa, kategoria_id) w bazie,
        wywołując db_manager.add_additive(...) z pustymi wartościami
        dla 'weight' i 'dosage', skoro nie są już potrzebne.
        
        Przy sukcesie wyświetla komunikat i zamyka dialog z QDialog.Accepted;
        w razie błędu pokazuje QMessageBox.
        """
        if not self.db_manager:
            QMessageBox.critical(
                self,
                "Błąd",
                "Brak db_manager – nie można dodać dodatku."
            )
            return

        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Błąd", "Nazwa dodatku jest wymagana.")
            return

        # Pobranie id wybranej kategorii
        selected_index = self.category_combo.currentIndex()
        category_id = self.category_combo.itemData(selected_index) if selected_index >= 0 else None

        # Ponieważ usunęliśmy pola 'Waga' i 'Dawkowanie', przekazujemy puste ciągi.
        weight_placeholder = ""
        dosage_placeholder = ""

        try:
            self.db_manager.add_additive(name, weight_placeholder, dosage_placeholder, category_id)
            QMessageBox.information(
                self,
                "Sukces",
                f"Dodatek '{name}' został dodany."
            )
            self.accept()  # zamyka dialog z kodem QDialog.Accepted
        except Exception as e:
            QMessageBox.warning(
                self,
                "Błąd",
                f"Nie udało się dodać dodatku: {e}"
            )
