# base_list_screen.py
from typing import Optional, List

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox
)
from PyQt5.QtCore import Qt


class BaseListScreen(QMainWindow):
    """
    Bazowy ekran wyświetlający listę danych w tabeli. Zawiera:
    - Tytuł (nagłówek),
    - Przyciski: 'Importuj', 'Nowy',
    - Pole wyszukiwania i przyciski 'Szukaj' oraz 'Wyczyść filtr',
    - Tabelę z możliwością sortowania kolumn.

    Klasy dziedziczące mogą nadpisywać metody:
    - load_data()     (ładowanie danych do tabeli),
    - import_data()   (logika przycisku 'Importuj'),
    - add_new_item()  (logika przycisku 'Nowy'),
    - apply_filter()  (logika przycisku 'Szukaj'),
    - clear_filter()  (czyszczenie i ponowne wczytanie danych).
    """

    def __init__(
        self,
        parent: Optional[QMainWindow] = None,
        title: str = "Lista",
        columns: Optional[List[str]] = None
    ) -> None:
        """
        Inicjalizuje bazowy ekran listy.
        """
        super().__init__(parent)
        self.parent = parent
        self.title_text: str = title
        self.columns: List[str] = columns if columns else []

        self.setWindowTitle(self.title_text)
        self.setGeometry(100, 100, 1000, 600)

        # Główny widget
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # 1. Nagłówek (tytuł)
        self.header_label = QLabel(self.title_text)
        self.header_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px 0;")
        main_layout.addWidget(self.header_label)

        # 2. Pasek akcji (Import, Nowy)
        action_layout = QHBoxLayout()

        self.import_button = QPushButton("Importuj")
        self.import_button.setStyleSheet("""
            background-color: #17a2b8; /* turkus */
            color: #FFFFFF;
            font-size: 14px;
            font-weight: bold;
            border-radius: 8px;
            padding: 10px 20px;
        """)
        self.import_button.clicked.connect(self.import_data)
        action_layout.addWidget(self.import_button)

        self.new_button = QPushButton("Nowy")
        self.new_button.setStyleSheet("""
            background-color: #007bff; /* niebieski */
            color: #FFFFFF;
            font-size: 14px;
            font-weight: bold;
            border-radius: 8px;
            padding: 10px 20px;
        """)
        self.new_button.clicked.connect(self.add_new_item)
        action_layout.addWidget(self.new_button)

        action_layout.addStretch()
        main_layout.addLayout(action_layout)

        # 3. Pasek filtra
        filter_layout = QHBoxLayout()

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Wpisz tekst do wyszukania...")
        filter_layout.addWidget(self.filter_input)

        self.search_button = QPushButton("Szukaj")
        self.search_button.setStyleSheet("""
            background-color: #5a6268;
            color: #FFFFFF;
            font-size: 14px;
            border-radius: 6px;
            padding: 8px 16px;
        """)
        self.search_button.clicked.connect(self.apply_filter)
        filter_layout.addWidget(self.search_button)

        self.clear_button = QPushButton("Wyczyść filtr")
        self.clear_button.setStyleSheet("""
            background-color: #6c757d;
            color: #FFFFFF;
            font-size: 14px;
            border-radius: 6px;
            padding: 8px 16px;
        """)
        self.clear_button.clicked.connect(self.clear_filter)
        filter_layout.addWidget(self.clear_button)

        main_layout.addLayout(filter_layout)

        # 4. Tabela
        self.table = QTableWidget()
        self.table.setSortingEnabled(True)
        main_layout.addWidget(self.table)

        self.setCentralWidget(central_widget)

        # Ustaw kolumny
        self.setup_table()

        # Automatyczne wczytanie danych
        self.load_data()

    def setup_table(self) -> None:
        """Ustawia nagłówki kolumn w tabeli."""
        if not self.columns:
            self.columns = ["Nazwa", "Kod", "Opis", "Data utworzenia"]

        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.resizeColumnsToContents()

    def load_data(self) -> None:
        """Do nadpisania w klasie potomnej."""
        self.table.setRowCount(0)
        # Przykład (można usunąć):
        data = []
        for row_index, row_data in enumerate(data):
            self.table.insertRow(row_index)
            for col_index, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                self.table.setItem(row_index, col_index, item)

        self.table.resizeColumnsToContents()

    def import_data(self) -> None:
        QMessageBox.information(self, "Import", "Nie zaimplementowano jeszcze importu.")

    def add_new_item(self) -> None:
        QMessageBox.information(self, "Nowy", "Nie zaimplementowano jeszcze dodawania.")

# base_list_screen.py

    def apply_filter(self):
        text = self.filter_input.text().strip()
        print(f"[DEBUG] base_list_screen.apply_filter: filter_text = {text}")
        
        # Zamiast self.products_list_screen, użyjemy "self", bo to SAM ekran:
        self.load_data(filter_text=text)


    def clear_filter(self) -> None:
        self.filter_input.clear()
        self.load_data()
        
    def hide_import_and_new_buttons(self) -> None:
        """
        Metoda, która chowa (lub usuwa) przyciski „Importuj” i „Nowy”,
        o ile zostały utworzone w klasie bazowej.
        """
        if hasattr(self, "import_button"):
            self.import_button.hide()

        if hasattr(self, "new_button"):
            self.new_button.hide()
   