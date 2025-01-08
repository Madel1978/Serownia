from typing import Optional

from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QPushButton, QWidget


class BaseScreen(QMainWindow):
    """
    Bazowy ekran (QMainWindow), z którego mogą dziedziczyć inne ekrany w aplikacji.
    Zawiera przykładowy przycisk 'Powrót', który domyślnie przełącza widok
    na inny ekran w obiekcie rodzica (np. start_screen).
    """

    def __init__(self, parent: Optional[QMainWindow] = None) -> None:
        """
        Inicjalizuje bazowy ekran, ustawia główne wymiary okna
        oraz tworzy główny layout (QVBoxLayout).

        :param parent: Okno-rodzic, najczęściej MainWindow (lub None).
        """
        super().__init__(parent)
        self.parent = parent  # Zapamiętujemy obiekt rodzica (np. MainWindow)
        self.setGeometry(100, 100, 800, 600)

        # Główny widget i layout
        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        # Dodanie przycisku "Powrót" (jeśli mamy rodzica)
        if self.parent is not None:
            self.add_back_button()

    def add_back_button(self) -> None:
        """
        Dodaje przycisk 'Powrót' na końcu layoutu.
        Styl i logikę obsługi możesz dostosować do własnych potrzeb.
        """
        back_button = QPushButton("Powrót")
        back_button.setStyleSheet("""
            padding: 15px;
            font-size: 14px;
            background-color: #FFCCCC;
            color: #800000;
            border-radius: 10px;
        """)

        # Zamiast self.close() przełączamy się na inny ekran w QStackedWidget (o ile istnieje rodzic)
        back_button.clicked.connect(self.handle_back)
        self.layout.addWidget(back_button)

    def handle_back(self) -> None:
        """
        Obsługa przycisku 'Powrót'. Domyślnie wraca do ekranu startowego w rodzicu,
        jednak możesz zmienić to zachowanie według własnych potrzeb.
        """
        if self.parent is not None:
            # Przykład: powrót na ekran główny (start_screen)
            if hasattr(self.parent, 'show_screen') and hasattr(self.parent, 'start_screen'):
                self.parent.show_screen(self.parent.start_screen)
            else:
                # Jeśli nie istnieją atrybuty show_screen / start_screen, to zamknij okno
                self.close()
        else:
            # Jeśli nie ma rodzica, zamykamy okno
            self.close()
