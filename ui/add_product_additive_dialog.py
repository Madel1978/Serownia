from typing import Optional, Any
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt

class AddProductAdditiveDialog(QDialog):
    """
    Dialog do dodania nowego składnika w product_additives:
      - Wybór dodatku (QComboBox)
      - Wpisanie dawki (QLineEdit)
    """

    def __init__(self, parent: Optional[Any] = None, db_manager: Optional[Any] = None, product_id: Optional[int] = None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.product_id = product_id

        self.setWindowTitle("Dodaj nowy składnik (additive) do produktu")
        self.setGeometry(400, 300, 300, 200)

        layout = QVBoxLayout(self)

        # Etykieta i combo z listą dodatków
        layout.addWidget(QLabel("Wybierz dodatek:"))
        self.additive_combo = QComboBox()
        layout.addWidget(self.additive_combo)

        # wypełnij combo z bazy (np. db_manager.get_all_additives())
        self.fill_additives_combo()

        # Etykieta i pole dawka/100L
        layout.addWidget(QLabel("Dawka/100L:"))
        self.dosage_input = QLineEdit()
        self.dosage_input.setPlaceholderText("np. 3 g")
        layout.addWidget(self.dosage_input)

        # Przycisk Zapisz
        save_button = QPushButton("Zapisz")
        save_button.clicked.connect(self.save_data)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def fill_additives_combo(self):
        """Wypełnia QComboBox listą wszystkich dodatków."""
        if not self.db_manager:
            return
        all_additives = self.db_manager.get_all_additives()
        for ad in all_additives:
            self.additive_combo.addItem(ad["name"], ad["id"])

    def save_data(self):
        """Po kliknięciu 'Zapisz' dodaj nowy wiersz w product_additives."""
        if not self.db_manager or not self.product_id:
            QMessageBox.warning(self, "Błąd", "Brak db_manager lub product_id!")
            return

        additive_id = self.additive_combo.itemData(self.additive_combo.currentIndex())
        dosage_per_100 = self.dosage_input.text().strip()
        if not dosage_per_100:
            QMessageBox.warning(self, "Błąd", "Wpisz dawkę (np. '3 g').")
            return

        try:
            self.db_manager.add_product_additive(self.product_id, additive_id, dosage_per_100)
            QMessageBox.information(self, "Sukces", f"Dodano nowy składnik o dawce {dosage_per_100}.")
            self.accept()  # Zamknij dialog z kodem QDialog.Accepted
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się dodać składnika: {e}")
