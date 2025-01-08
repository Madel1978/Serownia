from typing import Optional, Any

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QComboBox,
)
from PyQt5.QtCore import Qt


class AddPackagingDialog(QDialog):
    """
    Dialog umożliwiający dodanie nowego opakowania, bez pól „Ilość” i „Data”.
    Zostaje jedynie nazwa i kategoria opakowania.
    """

    def __init__(
        self,
        parent: Optional[Any] = None,  # Najczęściej QMainWindow lub inny widok
        db_manager: Optional[Any] = None,  # Docelowo: Optional[DBManager]
    ) -> None:
        """
        Inicjalizuje dialog 'Dodaj nowe opakowanie', zawierający
        tylko nazwę opakowania i kategorię.

        :param parent: Okno-rodzic (np. PackagingListScreen).
        :param db_manager: Obiekt bazy danych (DBManager).
        """
        super().__init__(parent)
        self.db_manager = db_manager

        self.setWindowTitle("Dodaj nowe opakowanie")
        self.setGeometry(400, 300, 300, 150)

        layout = QVBoxLayout(self)

        # Pole: nazwa opakowania
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nazwa opakowania (wymagane)")
        layout.addWidget(QLabel("Nazwa opakowania:"))
        layout.addWidget(self.name_input)

        # Pole: Kategoria (QComboBox)
        self.category_combo = QComboBox()
        layout.addWidget(QLabel("Kategoria opakowania:"))
        layout.addWidget(self.category_combo)
        self.fill_categories()

        # Przycisk "Zapisz"
        save_button = QPushButton("Zapisz")
        save_button.clicked.connect(self.save_data)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def fill_categories(self) -> None:
        """
        Wypełnia QComboBox listą kategorii z bazy danych,
        np. db_manager.get_packaging_categories().
        """
        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można wczytać kategorii."
            )
            return

        categories = (
            self.db_manager.get_packaging_categories()
        )  # np. [{"id":1, "name":"Słoiki"}, ...]
        for cat in categories:
            self.category_combo.addItem(cat["name"], cat["id"])

    def save_data(self) -> None:
        """
        Zapisanie danych do bazy (wywołuje db_manager.add_packaging)
        z pustymi wartościami dla ilości i daty, skoro usunięto te pola.
        W przypadku sukcesu zamyka dialog (QDialog.Accepted),
        w przeciwnym razie wyświetla komunikat o błędzie.
        """
        if not self.db_manager:
            QMessageBox.critical(
                self, "Błąd", "Brak db_manager – nie można dodać opakowania."
            )
            return

        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Błąd", "Nazwa opakowania jest wymagana.")
            return

        # Odczytujemy aktualnie wybraną kategorię
        category_id = self.category_combo.itemData(self.category_combo.currentIndex())

        # Skoro kolumny „Ilość” i „Data” usunięto z UI, możemy przekazać puste łańcuchy znaków:
        quantity_placeholder = ""
        date_placeholder = ""

        try:
            self.db_manager.add_packaging(
                name, quantity_placeholder, date_placeholder, category_id
            )
            QMessageBox.information(
                self, "Sukces", f"Opakowanie '{name}' zostało dodane."
            )
            self.accept()  # zamyka dialog (QDialog.Accepted)
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się dodać opakowania: {e}")
