import sys
from typing import Optional, List

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QLabel,
    QPushButton, QToolBar
)
from PyQt5.QtCore import Qt

# Baza danych
from database.db_manager import DBManager

# Klasy bazowe i ekrany
from ui.base_list_screen import BaseListScreen  # Zawiera apply_filter
from ui.start_screen import StartScreen
from ui.production_screen import ProductionScreen
from ui.magazyn_screen import MagazynScreen
from ui.settings_screen import SettingsScreen
from ui.login_screen import LoginScreen
from ui.registration_screen import RegistrationScreen
from ui.account_screen import AccountScreen
from ui.raporty_screen import RaportyScreen

from ui.packaging_list_screen import PackagingListScreen
from ui.packaging_register_screen import PackagingRegisterScreen
from ui.additives_register_screen import AdditivesRegisterScreen
from ui.additives_list_screen import AdditivesListScreen
from ui.products_list_screen import ProductsListScreen

from ui.packaging_categories_crud_screen import PackagingCategoriesCrudScreen
from ui.product_categories_crud_screen import ProductCategoriesCrudScreen
from ui.product_composition_screen import ProductCompositionScreen
from ui.additive_categories_crud_screen import AdditiveCategoriesCrudScreen

from ui.new_production_screen import NewProductionScreen

from ui.ser_production_protocol_screen import SerProductionProtocolScreen
from ui.fermented_production_protocol_screen import FermentedProductionProtocolScreen
from ui.twarog_production_protocol_screen import TwarogProductionProtocolScreen

from ui.production_list_screen import ProductionListScreen


class MainWindow(QMainWindow):
    """
    Główne okno aplikacji Serownia Manager.
    Zarządza wszystkimi ekranami (QStackedWidget), obsługuje logowanie/wylogowanie,
    oraz przechowuje obiekt db_manager do komunikacji z bazą danych.
    """

    def __init__(self, db_manager: DBManager) -> None:
        super().__init__()
        print("=== Inicjalizacja MainWindow ===")

        self.setWindowTitle("Serownia Manager")
        self.setGeometry(100, 100, 600, 800)

        # Przechowujemy db_manager w MainWindow,
        # aby ekrany mogły go pobrać przez self.window().db_manager
        self.db_manager = db_manager

        self.logged_in_user: Optional[str] = None
        self.screen_history: List[QMainWindow] = []

        # Stos ekranów
        self.stacked_widget: QStackedWidget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Pasek narzędzi
        self.toolbar: QToolBar = QToolBar("Użytkownik")
        self.user_label: QLabel = QLabel("")
        self.logout_button: QPushButton = QPushButton("Wyloguj")

        # Inicjalizacja UI
        self.setup_ui()
        self.setup_connections()

        print("=== MainWindow zainicjalizowane. ===")

    def setup_ui(self) -> None:
        """
        Tworzy ekrany i dodaje je do QStackedWidget, konfiguruje toolbar itp.
        """
        print("=== Tworzenie i dodawanie ekranów do QStackedWidget ===")

        # ----------------------------------------------------------
        # 1) Tworzymy instancje ekranów (koniecznie w poprawnej kolejności)
        # ----------------------------------------------------------

        # Ekrany logowania / rejestracji / start
        self.login_screen = LoginScreen(parent=self, db_manager=self.db_manager)
        self.registration_screen = RegistrationScreen(parent=self, db_manager=self.db_manager)
        self.start_screen = StartScreen(parent=self)

        # Ekrany funkcyjne
        self.production_screen = ProductionScreen(parent=self)
        self.magazyn_screen = MagazynScreen(parent=self)
        self.settings_screen = SettingsScreen(parent=self, db_manager=self.db_manager)
        self.account_screen = AccountScreen(parent=self, db_manager=self.db_manager)
        self.raporty_screen = RaportyScreen(parent=self)

        # Najpierw ekrany list, z których jeden będzie używany przez base_list_screen:
        self.packaging_list_screen = PackagingListScreen(parent=self, db_manager=self.db_manager)
        print(f"[DEBUG] packaging_list_screen = {self.packaging_list_screen}, id={id(self.packaging_list_screen)}")
        self.packaging_register_screen = PackagingRegisterScreen(parent=self, db_manager=self.db_manager)
        self.additives_register_screen = AdditivesRegisterScreen(parent=self, db_manager=self.db_manager)
        self.additives_list_screen = AdditivesListScreen(parent=self, db_manager=self.db_manager)
        self.products_list_screen = ProductsListScreen(parent=self, db_manager=self.db_manager)
        print(f"[DEBUG] products_list_screen  = {self.products_list_screen}, id={id(self.products_list_screen)}")

        # Następnie klasa bazowa, jeśli chcemy z niej korzystać w interfejsie
        self.base_list_screen = BaseListScreen(
            parent=self,
            title="BaseListScreen (Uniwersalny)",
            columns=["Kol1", "Kol2", "Kol3"]
        )
        # Kluczowe: 
        # Metoda apply_filter() w base_list_screen pozwala wyszukiwać w products_list_screen
        self.base_list_screen.products_list_screen = self.products_list_screen

        # CRUD kategorie
        self.packaging_categories_crud_screen = PackagingCategoriesCrudScreen(parent=self, db_manager=self.db_manager)
        self.product_categories_crud_screen = ProductCategoriesCrudScreen(parent=self, db_manager=self.db_manager)
        self.product_composition_screen = ProductCompositionScreen(parent=self, db_manager=self.db_manager)
        self.additive_categories_crud_screen = AdditiveCategoriesCrudScreen(parent=self, db_manager=self.db_manager)

        # Nowa Produkcja (kafelki)
        self.new_production_screen = NewProductionScreen(parent=self)

        # Protokoły
        self.ser_production_protocol_screen = SerProductionProtocolScreen(parent=self, db_manager=self.db_manager)
        self.fermented_production_protocol_screen = FermentedProductionProtocolScreen(parent=self, db_manager=self.db_manager)
        self.twarog_production_protocol_screen = TwarogProductionProtocolScreen(parent=self, db_manager=self.db_manager)

        # Baza Produkcji (lista protokołów)
        self.production_list_screen = ProductionListScreen(parent=self, db_manager=self.db_manager)

        # ----------------------------------------------------------
        # 2) Dodajemy ekrany do QStackedWidget
        # ----------------------------------------------------------
        self.stacked_widget.addWidget(self.login_screen)
        self.stacked_widget.addWidget(self.registration_screen)
        self.stacked_widget.addWidget(self.start_screen)
        self.stacked_widget.addWidget(self.production_screen)
        self.stacked_widget.addWidget(self.magazyn_screen)
        self.stacked_widget.addWidget(self.settings_screen)
        self.stacked_widget.addWidget(self.account_screen)
        self.stacked_widget.addWidget(self.raporty_screen)

        self.stacked_widget.addWidget(self.packaging_list_screen)
        self.stacked_widget.addWidget(self.packaging_register_screen)
        self.stacked_widget.addWidget(self.additives_register_screen)
        self.stacked_widget.addWidget(self.additives_list_screen)
        self.stacked_widget.addWidget(self.products_list_screen)

        # Dodajemy base_list_screen
        self.stacked_widget.addWidget(self.base_list_screen)

        self.stacked_widget.addWidget(self.product_composition_screen)
        self.stacked_widget.addWidget(self.packaging_categories_crud_screen)
        self.stacked_widget.addWidget(self.product_categories_crud_screen)
        self.stacked_widget.addWidget(self.additive_categories_crud_screen)

        self.stacked_widget.addWidget(self.new_production_screen)

        self.stacked_widget.addWidget(self.ser_production_protocol_screen)
        self.stacked_widget.addWidget(self.fermented_production_protocol_screen)
        self.stacked_widget.addWidget(self.twarog_production_protocol_screen)
        self.stacked_widget.addWidget(self.production_list_screen)

        # Na koniec ustawiamy ekran startowy (login)
        self.stacked_widget.setCurrentWidget(self.login_screen)
        print("Aktualny ekran =", self.stacked_widget.currentWidget())

        # ----------------------------------------------------------
        # 3) Konfiguracja toolbaru
        # ----------------------------------------------------------
        print("=== Konfiguracja paska narzędzi (toolbar) ===")
        self.toolbar.setStyleSheet("background-color: #F0F0F0;")
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)
        self.toolbar.addWidget(self.user_label)

        self.logout_button.setStyleSheet("""
            background-color: #FFCCCC;
            color: #800000;
            font-size: 12px;
            border-radius: 10px;
            padding: 5px 10px;
        """)
        self.toolbar.addWidget(self.logout_button)
        self.toolbar.hide()

        # Mapa protokołów
        self.protocol_screens_by_name = {
            "Ser": self.ser_production_protocol_screen,
            "Napoje fermentowane": self.fermented_production_protocol_screen,
            "Ser twarogowy": self.twarog_production_protocol_screen,
        }

    def setup_connections(self) -> None:
        """
        Podpinamy sygnały/sloty (np. wylogowanie).
        """
        print("=== Łączenie sygnałów/slotów ===")
        self.logout_button.clicked.connect(self.logout)

    # ----------------------------------------------------------
    # Nawigacja
    # ----------------------------------------------------------
    def show_screen(self, screen: QMainWindow) -> None:
        current_widget = self.stacked_widget.currentWidget()
        if current_widget is not None and current_widget != screen:
            self.screen_history.append(current_widget)
        self.stacked_widget.setCurrentWidget(screen)

    def show_previous_screen(self) -> None:
        if self.screen_history:
            prev_screen = self.screen_history.pop()
            self.stacked_widget.setCurrentWidget(prev_screen)

    # ----------------------------------------------------------
    # Logowanie / wylogowanie
    # ----------------------------------------------------------
    def login_user(self, username: str) -> None:
        self.logged_in_user = username
        self.account_screen.load_user_data(username)
        self.user_label.setText(f"Zalogowany jako: {username}")
        self.toolbar.show()
        self.show_screen(self.start_screen)

    def logout(self) -> None:
        print("=== Wylogowywanie użytkownika ===")
        self.logged_in_user = None
        self.user_label.setText("")
        self.toolbar.hide()
        self.screen_history.clear()
        self.show_screen(self.login_screen)

    def show_production_list_screen(self) -> None:
        print(">>> show_production_list_screen()")
        self.show_screen(self.production_list_screen)


if __name__ == "__main__":
    print("=== Start pliku main.py ===")
    app = QApplication(sys.argv)
    print("=== QApplication stworzona ===")

    db_manager = DBManager()
    print("=== DBManager zainicjalizowany ===")

    window = MainWindow(db_manager)
    print("=== MainWindow stworzone, wywołuję show() ===")
    window.show()

    print("=== Wchodzę w pętlę zdarzeń (app.exec_()) ===")
    sys.exit(app.exec_())
