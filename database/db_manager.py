import sqlite3
import os
from typing import Optional, List, Dict, Any

class DBManager:
    """
    Klasa odpowiedzialna za zarządzanie bazą danych (SQLite).
    Utrzymuje ścieżkę do pliku bazy, tworzy połączenia i udostępnia metody
    CRUD dla różnych tabel (users, additives, products, packaging, etc.).
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            self.db_path = r"c:\serownia\serownia.db"
        else:
            self.db_path = db_path

        abs_path = os.path.abspath(self.db_path)
        print(f"=== DBManager używa pliku: {self.db_path}")
        print(f"=== Absolutna ścieżka   : {abs_path}")

        # Inicjalizacja bazy (tworzenie tabel, wstawianie danych początkowych)
        self.setup_database()

    def create_connection(self) -> sqlite3.Connection:
        """
        Tworzy i zwraca połączenie do bazy SQLite,
        z włączonym wsparciem kluczy obcych (PRAGMA foreign_keys=ON).
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as e:
            print(f"Błąd podczas włączania kluczy obcych: {e}")
        return conn

    def setup_database(self) -> None:
        self.create_tables()

    def create_tables(self) -> None:
        """
        Tworzy (jeśli nie istnieją) wymagane tabele w bazie danych,
        a także wstawia dane początkowe (np. kategorie).
        Uwaga: IF NOT EXISTS nie modyfikuje istniejącej tabeli.
        """
        with self.create_connection() as conn:
            cursor = conn.cursor()
            try:
                # -------------------- Użytkownicy --------------------
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL
                    )
                """)

                # -------------------- Kategorie Dodatków (do additives) --------------------
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE
                    )
                """)

                # -------------------- Kategorie Produktów (do products) --------------------
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS product_categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE
                    )
                """)

                # -------------------- Dodatki --------------------
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS additives (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        weight TEXT,
                        dosage TEXT,
                        category_id INTEGER,
                        FOREIGN KEY (category_id) REFERENCES categories(id)
                    )
                """)

                # -------------------- Produkty --------------------
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        category_id INTEGER,
                        price TEXT,
                        stock TEXT,
                        FOREIGN KEY (category_id) REFERENCES product_categories(id)
                    )
                """)

                # -------------------- Tabela product_additives (relacja produkt - dodatek) --------------------
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS product_additives (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER NOT NULL,
                        additive_id INTEGER NOT NULL,
                        dosage_per_100 TEXT,
                        FOREIGN KEY (product_id) REFERENCES products(id),
                        FOREIGN KEY (additive_id) REFERENCES additives(id)
                    )
                """)

                # -------------------- Kategorie Opakowań --------------------
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS packaging_categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE
                    )
                """)

                # -------------------- Opakowania --------------------
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS packaging (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        quantity TEXT,
                        date TEXT,
                        packaging_category_id INTEGER,
                        FOREIGN KEY (packaging_category_id) REFERENCES packaging_categories(id)
                    )
                """)

                # -------------------- Rejestr Dodatków --------------------
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS additives_register (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT,
                        quantity TEXT,
                        additive_id INTEGER,
                        FOREIGN KEY (additive_id) REFERENCES additives(id)
                    )
                """)

                # -------------------- Rejestr Opakowań --------------------
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS packaging_register (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT,
                        quantity TEXT,
                        packaging_id INTEGER,
                        FOREIGN KEY (packaging_id) REFERENCES packaging(id)
                    )
                """)

                # -------------------- Tabela production_records --------------------
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS production_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        series TEXT NOT NULL,
                        product_id INTEGER,
                        FOREIGN KEY (product_id) REFERENCES products(id)
                    )
                """)

                # -------------------- ser_production_details --------------------
                #
                # Uwaga: w bazie muszą istnieć kolumny dopasowane do 9 (czy nawet 6-8)
                # czynności, np.:
                #   dodanie_kultur_godzina, dodanie_kultur_czas, ...
                #   => tego tu nie widzimy – więc dodałem tylko kolumny, które
                #   były do tej pory, plus nowo wstawione (serwatka_plus, woda_minus,
                #   temp_poczatkowa, temp_koncowa).
                #
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ser_production_details (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        production_record_id INTEGER NOT NULL,
                        milk_amount TEXT,
                        ph TEXT,
                        krojenie_start TEXT,
                        krojenie_end TEXT,
                        plukanie_start TEXT,
                        plukanie_end TEXT,
                        dogrzewanie_start TEXT,
                        dogrzewanie_end TEXT,
                        serwatka_plus TEXT,
                        woda_minus TEXT,
                        temp_poczatkowa TEXT,
                        temp_koncowa TEXT,
                        FOREIGN KEY (production_record_id) REFERENCES production_records(id)
                    )
                """)

                # -------------------- ser_production_additives --------------------
                #
                # Tablica, w której trzymamy KONKRETNE dodatki użyte w protokole
                # (powiązane z production_record_id), 3 kolumny: kategoria, nazwa, dawka
                # – i usunięta kolumna time_added (nie chcemy jej).
                #
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ser_production_additives (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        production_record_id INTEGER NOT NULL,
                        additive_category TEXT,
                        additive_name TEXT,
                        dose_calculated TEXT,
                        FOREIGN KEY (production_record_id) REFERENCES production_records(id)
                    )
                """)

                # --- Dane startowe: kategorie dodatków (tabela categories) ---
                initial_categories = [
                    "Kultury starterowe",
                    "Podpuszczka",
                    "Lizozym",
                    "Chlorek wapnia",
                    "Przyprawy",
                    "Proszki"
                ]
                for category in initial_categories:
                    cursor.execute(
                        "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                        (category,)
                    )

                # --- Dane startowe: kategorie produktów (tabela product_categories) ---
                initial_product_categories = [
                    "Ser",
                    "Napoje fermentowane",
                    "Ser twarogowy",
                    "Ser zwarowy",
                    "Mleko",
                    "Serwatka",
                    "Lody",
                    "Inne"
                ]
                for cat_name in initial_product_categories:
                    cursor.execute(
                        "INSERT OR IGNORE INTO product_categories (name) VALUES (?)",
                        (cat_name,)
                    )

                # --- Dane startowe: kategorie opakowań (tabela packaging_categories) ---
                initial_packaging_categories = [
                    "Słoiki",
                    "Worki",
                    "Pudełka",
                    "Papier",
                    "Inne"
                ]
                for pcat_name in initial_packaging_categories:
                    cursor.execute(
                        "INSERT OR IGNORE INTO packaging_categories (name) VALUES (?)",
                        (pcat_name,)
                    )

                conn.commit()

            except sqlite3.Error as e:
                print(f"Błąd przy tworzeniu tabel: {e}")
                conn.rollback()

    # ----------------------------------------------------------------
    # -------------------- UŻYTKOWNICY (CRUD) ------------------------
    # ----------------------------------------------------------------
    def add_user(self, username: str, password: str) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, password)
                    VALUES (?, ?)
                """, (username, password))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy dodawaniu użytkownika: {e}")

    def verify_user(self, username: str, password: str) -> bool:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id FROM users
                    WHERE username=? AND password=?
                """, (username, password))
                row = cursor.fetchone()
                return row is not None
        except sqlite3.Error as e:
            print(f"Błąd przy weryfikacji użytkownika: {e}")
            return False

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, password
                    FROM users
                    WHERE username=?
                """, (username,))
                row = cursor.fetchone()
                if row:
                    return {"id": row[0], "username": row[1], "password": row[2]}
                return None
        except sqlite3.Error as e:
            print(f"Błąd przy pobieraniu użytkownika: {e}")
            return None

    def update_user_password(self, username: str, new_password: str) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users
                    SET password=?
                    WHERE username=?
                """, (new_password, username))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy aktualizacji hasła użytkownika: {e}")

    # ----------------------------------------------------------------
    # ----------------- KATEGORIE DODATKÓW (CRUD) --------------------
    # ----------------------------------------------------------------
    def get_categories(self) -> List[Dict[str, Any]]:
        """
        Zwraca listę *wszystkich* kategorii z tabeli 'categories'
        (czyli kategorii dla dodatków).
        """
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM categories")
                rows = cursor.fetchall()
                return [{"id": row[0], "name": row[1]} for row in rows]
        except sqlite3.Error as e:
            print(f"Błąd przy pobieraniu kategorii: {e}")
            return []

    def get_additive_categories(self) -> List[Dict[str, Any]]:
        """
        Alias dla get_categories, jeśli potrzebujemy nazwy get_additive_categories().
        """
        return self.get_categories()

    def add_category(self, name: str) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO categories (name) VALUES (?)
                """, (name,))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy dodawaniu kategorii: {e}")

    def update_category(self, category_id: int, new_name: str) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE categories
                    SET name=?
                    WHERE id=?
                """, (new_name, category_id))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy aktualizacji kategorii: {e}")

    def delete_category(self, category_id: int) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM categories WHERE id=?", (category_id,))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy usuwaniu kategorii: {e}")

    # ----------------------------------------------------------------
    # ---------------------- DODATKI (CRUD) --------------------------
    # ----------------------------------------------------------------
    def get_all_additives(self) -> List[Dict[str, Any]]:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, weight, dosage, category_id
                    FROM additives
                """)
                rows = cursor.fetchall()
                result: List[Dict[str, Any]] = []
                for row in rows:
                    result.append({
                        "id": row[0],
                        "name": row[1],
                        "weight": row[2],
                        "dosage": row[3],
                        "category_id": row[4],
                    })
                return result
        except sqlite3.Error as e:
            print(f"Błąd przy pobieraniu dodatków: {e}")
            return []

    def add_additive(self, name: str, weight: str, dosage: str, category_id: int) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO additives (name, weight, dosage, category_id)
                    VALUES (?, ?, ?, ?)
                """, (name, weight, dosage, category_id))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy dodawaniu dodatku: {e}")

    def delete_additive(self, additive_id: int) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM additives WHERE id=?", (additive_id,))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy usuwaniu dodatku: {e}")

    def update_additive(self, additive_id: int, name: str, weight: str, dosage: str, category_id: int) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE additives
                    SET name=?, weight=?, dosage=?, category_id=?
                    WHERE id=?
                """, (name, weight, dosage, category_id, additive_id))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy aktualizacji dodatku: {e}")

    # ----------------------------------------------------------------
    # ------------------ KATEGORIE PRODUKTÓW (CRUD) ------------------
    # ----------------------------------------------------------------
    def get_product_categories(self) -> List[Dict[str, Any]]:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM product_categories")
                rows = cursor.fetchall()
                return [{"id": row[0], "name": row[1]} for row in rows]
        except sqlite3.Error as e:
            print(f"Błąd przy pobieraniu kategorii produktów: {e}")
            return []

    def add_product_category(self, name: str) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO product_categories (name) VALUES (?)
                """, (name,))
                conn.commit()
        except sqlite3.IntegrityError:
            print(f"[WARN] Próba dodania zduplikowanej kategorii produktu: '{name}'")
            raise
        except sqlite3.Error as e:
            print(f"Błąd przy dodawaniu kategorii produktu: {e}")

    def update_product_category(self, category_id: int, new_name: str) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE product_categories
                    SET name=?
                    WHERE id=?
                """, (new_name, category_id))
                conn.commit()
        except sqlite3.IntegrityError:
            print(f"[WARN] Próba zmiany nazwy kategorii na zduplikowaną: '{new_name}'")
            raise
        except sqlite3.Error as e:
            print(f"Błąd przy aktualizacji kategorii produktu: {e}")

    def delete_product_category(self, category_id: int) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM product_categories WHERE id=?", (category_id,))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy usuwaniu kategorii produktu: {e}")

    # ----------------------------------------------------------------
    # ----------------------- PRODUKTY (CRUD) ------------------------
    # ----------------------------------------------------------------
    def get_all_products(self) -> List[Dict[str, Any]]:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, category_id, price, stock
                    FROM products
                """)
                rows = cursor.fetchall()
                result: List[Dict[str, Any]] = []
                for row in rows:
                    result.append({
                        "id": row[0],
                        "name": row[1],
                        "category_id": row[2],
                        "price": row[3],
                        "stock": row[4]
                    })
                return result
        except sqlite3.Error as e:
            print(f"Błąd przy pobieraniu produktów: {e}")
            return []

    def add_product(
        self,
        name: str,
        category_id: int,
        price: Optional[str] = None,
        stock: Optional[str] = None
    ) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO products (name, category_id, price, stock)
                    VALUES (?, ?, ?, ?)
                """, (name, category_id, price if price else None, stock if stock else None))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy dodawaniu produktu: {e}")

    def update_product(
        self,
        product_id: int,
        new_name: str,
        new_category_id: int,
        new_price: Optional[str] = None,
        new_stock: Optional[str] = None
    ) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE products
                    SET name = ?, category_id = ?, price = ?, stock = ?
                    WHERE id = ?
                """, (
                    new_name,
                    new_category_id,
                    new_price if new_price else None,
                    new_stock if new_stock else None,
                    product_id
                ))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy aktualizacji produktu: {e}")

    def delete_product(self, product_id: int) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy usuwaniu produktu: {e}")

    # ----------------------------------------------------------------
    # --------------- product_additives (RELACJA PRODUKT-DODATEK) ----
    # ----------------------------------------------------------------
    def get_product_additives(self, product_id: int) -> List[Dict[str, Any]]:
        """
        Pobiera listę wierszy z tabeli 'product_additives' dla danego product_id.
        Następnie w kodzie możesz osobno wywołać get_additive_by_id(additive_id)
        dla szczegółów o dodatku.
        """
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, product_id, additive_id, dosage_per_100
                    FROM product_additives
                    WHERE product_id = ?
                """, (product_id,))
                rows = cursor.fetchall()
                result: List[Dict[str, Any]] = []
                for row in rows:
                    result.append({
                        "id": row[0],
                        "product_id": row[1],
                        "additive_id": row[2],
                        "dosage_per_100": row[3]
                    })
                return result
        except sqlite3.Error as e:
            print(f"Błąd przy pobieraniu relacji product_additives: {e}")
            return []

    def get_product_additives_join(self, product_id: int) -> List[Dict[str, Any]]:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT pa.id,
                           pa.product_id,
                           pa.dosage_per_100,
                           a.id AS additive_id,
                           a.name AS additive_name,
                           a.category_id
                      FROM product_additives pa
                      JOIN additives a ON pa.additive_id = a.id
                     WHERE pa.product_id = ?
                """, (product_id,))
                rows = cursor.fetchall()
                result: List[Dict[str, Any]] = []
                for row in rows:
                    result.append({
                        "id": row[0],
                        "product_id": row[1],
                        "dosage_per_100": row[2],
                        "additive_id": row[3],
                        "additive_name": row[4],
                        "category_id": row[5]
                    })
                return result
        except sqlite3.Error as e:
            print(f"Błąd przy pobieraniu relacji product_additives (JOIN): {e}")
            return []

    def add_product_additive(self, product_id: int, additive_id: int, dosage_per_100: str) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO product_additives (product_id, additive_id, dosage_per_100)
                    VALUES (?, ?, ?)
                """, (product_id, additive_id, dosage_per_100))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy dodawaniu wpisu w product_additives: {e}")

    def update_product_additive(self, pa_id: int, new_dosage: str) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE product_additives
                    SET dosage_per_100 = ?
                    WHERE id = ?
                """, (new_dosage, pa_id))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy aktualizacji wpisu w product_additives: {e}")

    def delete_product_additive(self, pa_id: int) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM product_additives WHERE id=?", (pa_id,))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy usuwaniu wpisu w product_additives: {e}")

    def update_product_additive_full(self, pa_id: int, new_additive_id: int, new_dosage: str) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE product_additives
                    SET additive_id = ?, dosage_per_100 = ?
                    WHERE id = ?
                """, (new_additive_id, new_dosage, pa_id))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy aktualizacji product_additives (pa_id={pa_id}): {e}")

    # ----------------------------------------------------------------
    # ------------------ KATEGORIE OPAKOWAŃ (CRUD) -------------------
    # ----------------------------------------------------------------
    def get_packaging_categories(self) -> List[Dict[str, Any]]:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM packaging_categories")
                rows = cursor.fetchall()
                return [{"id": row[0], "name": row[1]} for row in rows]
        except sqlite3.Error as e:
            print(f"Błąd przy pobieraniu kategorii opakowań: {e}")
            return []

    def add_packaging_category(self, name: str) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO packaging_categories (name) VALUES (?)
                """, (name,))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy dodawaniu kategorii opakowania: {e}")

    def update_packaging_category(self, category_id: int, new_name: str) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE packaging_categories
                    SET name=?
                    WHERE id=?
                """, (new_name, category_id))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy aktualizacji kategorii opakowania: {e}")

    def delete_packaging_category(self, category_id: int) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM packaging_categories WHERE id=?", (category_id,))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy usuwaniu kategorii opakowania: {e}")

    # ----------------------------------------------------------------
    # ---------------------- OPAKOWANIA (CRUD) -----------------------
    # ----------------------------------------------------------------
    def get_all_packaging(self) -> List[Dict[str, Any]]:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, quantity, date, packaging_category_id
                    FROM packaging
                """)
                rows = cursor.fetchall()
                result: List[Dict[str, Any]] = []
                for row in rows:
                    result.append({
                        "id": row[0],
                        "name": row[1],
                        "quantity": row[2],
                        "date": row[3],
                        "packaging_category_id": row[4]
                    })
                return result
        except sqlite3.Error as e:
            print(f"Błąd przy pobieraniu opakowań: {e}")
            return []

    def add_packaging(self, name: str, quantity: str, date: str, packaging_category_id: int) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO packaging (name, quantity, date, packaging_category_id)
                    VALUES (?, ?, ?, ?)
                """, (name, quantity, date, packaging_category_id))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy dodawaniu opakowania: {e}")

    def update_packaging(self, packaging_id: int, name: str, quantity: str, date: str, category_id: int) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE packaging
                    SET name=?, quantity=?, date=?, packaging_category_id=?
                    WHERE id=?
                """, (name, quantity, date, category_id, packaging_id))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy aktualizacji opakowania: {e}")

    def delete_packaging(self, packaging_id: int) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM packaging WHERE id=?", (packaging_id,))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy usuwaniu opakowania: {e}")

    # ----------------------------------------------------------------
    # -------------------- REJESTR OPAKOWAŃ --------------------------
    # ----------------------------------------------------------------
    def add_packaging_register(self, date: str, quantity: str, packaging_id: int) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO packaging_register (date, quantity, packaging_id)
                    VALUES (?, ?, ?)
                """, (date, quantity, packaging_id))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy dodawaniu do rejestru opakowań: {e}")

    def get_all_packaging_register(self) -> List[Dict[str, Any]]:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT pr.id, pr.date, pr.quantity, pr.packaging_id, p.name
                    FROM packaging_register pr
                    LEFT JOIN packaging p ON pr.packaging_id = p.id
                """)
                rows = cursor.fetchall()
                result: List[Dict[str, Any]] = []
                for row in rows:
                    result.append({
                        "id": row[0],
                        "date": row[1],
                        "quantity": row[2],
                        "packaging_id": row[3],
                        "packaging_name": row[4]
                    })
                return result
        except sqlite3.Error as e:
            print(f"Błąd przy pobieraniu rejestru opakowań: {e}")
            return []

    def update_packaging_register(self, register_id: int, date_str: str, quantity_str: str, packaging_id: int) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE packaging_register
                    SET date=?, quantity=?, packaging_id=?
                    WHERE id=?
                """, (date_str, quantity_str, packaging_id, register_id))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy aktualizacji rejestru opakowań: {e}")

    def delete_packaging_register(self, register_id: int) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM packaging_register WHERE id=?", (register_id,))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy usuwaniu z rejestru opakowań: {e}")

    # ----------------------------------------------------------------
    # -------------------- REJESTR DODATKÓW --------------------------
    # ----------------------------------------------------------------
    def add_additive_register(self, date_str: str, quantity_str: str, additive_id: int) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO additives_register (date, quantity, additive_id)
                    VALUES (?, ?, ?)
                """, (date_str, quantity_str, additive_id))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy dodawaniu do rejestru dodatków: {e}")

    def get_all_additives_register(self) -> List[Dict[str, Any]]:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ar.id, ar.date, ar.quantity, ar.additive_id, a.name
                    FROM additives_register ar
                    LEFT JOIN additives a ON ar.additive_id = a.id
                """)
                rows = cursor.fetchall()
                result: List[Dict[str, Any]] = []
                for row in rows:
                    result.append({
                        "id": row[0],
                        "date": row[1],
                        "quantity": row[2],
                        "additive_id": row[3],
                        "additive_name": row[4]
                    })
                return result
        except sqlite3.Error as e:
            print(f"Błąd przy pobieraniu rejestru dodatków: {e}")
            return []

    def update_additive_register(self, register_id: int, new_date: str, new_quantity: str, additive_id: int) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE additives_register
                    SET date=?, quantity=?, additive_id=?
                    WHERE id=?
                """, (new_date, new_quantity, additive_id, register_id))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy aktualizacji rejestru dodatków: {e}")

    def delete_additive_register(self, register_id: int) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM additives_register WHERE id=?", (register_id,))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy usuwaniu z rejestru dodatków: {e}")

    # ----------------------------------------------------------------
    # --------------- NOWA METODA: GET_ADDITIVE_BY_ID ---------------
    # ----------------------------------------------------------------
    def get_additive_by_id(self, additive_id: int) -> Optional[Dict[str, Any]]:
        """
        Zwraca słownik z informacjami o danym dodatku (id, name, weight, dosage, category_id)
        na podstawie jego ID, albo None, jeśli nie znaleziono wpisu w bazie.
        """
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, weight, dosage, category_id
                    FROM additives
                    WHERE id = ?
                """, (additive_id,))
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "name": row[1],
                        "weight": row[2],
                        "dosage": row[3],
                        "category_id": row[4],
                    }
                return None
        except sqlite3.Error as e:
            print(f"Błąd przy pobieraniu dodatku (id={additive_id}): {e}")
            return None

    # ----------------------------------------------------------------
    # ----------- Metody do obsługi PRODUCTION_RECORDS --------------
    # ----------------------------------------------------------------
    def add_production_record(self, date_str: str, series_str: str, product_id: int) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO production_records (date, series, product_id)
                    VALUES (?, ?, ?)
                """, (date_str, series_str, product_id))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy dodawaniu rekordu w production_records: {e}")
            raise

    def add_production_record_returning_id(self, date_str: str, series_str: str, product_id: int) -> int:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO production_records (date, series, product_id)
                    VALUES (?, ?, ?)
                """, (date_str, series_str, product_id))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Błąd przy dodawaniu rekordu w production_records (returning id): {e}")
            raise

    def get_production_count_for_month(self, month: int, full_year: int) -> int:
        """
        Zwraca liczbę protokołów w danym (miesiącu, roku) w production_records.
        np. do generowania numeru serii.
        """
        month_str = f"{month:02d}"
        year_str = str(full_year)

        sql = """
            SELECT COUNT(*)
            FROM production_records
            WHERE strftime('%m', date) = ?
              AND strftime('%Y', date) = ?
        """

        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (month_str, year_str))
                row = cursor.fetchone()
                return row[0] if row else 0
        except sqlite3.Error as e:
            print(f"[DBManager] Błąd przy liczeniu protokołów: {e}")
            return 0

    def update_production_record(
        self,
        record_id: int,
        new_date: str,
        new_series: str,
        new_product_id: int
    ) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE production_records
                    SET date = ?,
                        series = ?,
                        product_id = ?
                    WHERE id = ?
                """, (new_date, new_series, new_product_id, record_id))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy aktualizacji production_records (id={record_id}): {e}")
            raise

    # ----------------------------------------------------------------
    # ------------------ ser_production_details (CRUD) --------------
    # ----------------------------------------------------------------
    def add_ser_production_details(
        self,
        production_record_id: int,
        milk_amount: str,
        ph: str,
        pasteryzacja_str: int,
        krojenie_start: str,
        krojenie_end: str,
        plukanie_start: str,
        plukanie_end: str,
        dogrzewanie_start: str,
        dogrzewanie_end: str,
        serwatka_plus: str,
        woda_minus: str,
        temp_poczatkowa: str,
        temp_koncowa: str
    ) -> None:
        """
        Dodaje nowy wiersz do tabeli ser_production_details.
        """
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO ser_production_details (
                    production_record_id,
                    milk_amount,
                    ph,
                    dodanie_kultur_start,
                    dodanie_kultur_end,
                    podpuszczka_start,
                    podpuszczka_end,
                    krojenie_start,
                    krojenie_end,
                    serwatka_start,
                    serwatka_end,
                    dogrzewanie_start,
                    dogrzewanie_end,
                    dosuszanie_start,
                    dosuszanie_end,
                    wstepne_prasowanie_start,
                    wstepne_prasowanie_end,
                    formy_wielkosc,
                    formy_ilosc,
                    solenie_start,
                    solenie_end,
                    pasteryzacja
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    production_record_id,
                    milk_amount,
                    ph,
                    dodanie_kultur_start,
                    dodanie_kultur_end,
                    podpuszczka_start,
                    podpuszczka_end,
                    krojenie_start,
                    krojenie_end,
                    serwatka_start,
                    serwatka_end,
                    dogrzewanie_start,
                    dogrzewanie_end,
                    dosuszanie_start,
                    dosuszanie_end,
                    wstepne_prasowanie_start,
                    wstepne_prasowanie_end,
                    formy_wielkosc,
                    formy_ilosc,
                    solenie_start,
                    solenie_end,
                    pasteryzacja
                )
            )
            conn.commit()

    def get_ser_production_details(self, production_record_id: int) -> Dict[str, Any]:
        """
        Pobiera szczegółowe dane protokołu 'Ser' z tabeli ser_production_details
        dla danego production_record_id. Zwraca słownik z polami (kolumnami).
        Jeśli brak wiersza – zwraca pusty słownik.
        """
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                # Upewnij się, że SELECT uwzględnia *wszystkie* kolumny w tabeli
                # (poza 'id', jeśli chcesz) w tej samej kolejności, co w DB:
                cursor.execute("""
                    SELECT
                        id,
                        production_record_id,
                        milk_amount,
                        ph,
                        dodanie_kultur_start,
                        dodanie_kultur_end,
                        podpuszczka_start,
                        podpuszczka_end,
                        krojenie_start,
                        krojenie_end,
                        serwatka_start,
                        serwatka_end,
                        dogrzewanie_start,
                        dogrzewanie_end,
                        dosuszanie_start,
                        dosuszanie_end,
                        wstepne_prasowanie_start,
                        wstepne_prasowanie_end,
                        formy_wielkosc,
                        formy_ilosc,
                        solenie_start,
                        solenie_end,
                        pasteryzacja
                    FROM ser_production_details
                    WHERE production_record_id = ?
                """, (production_record_id,))

                row = cursor.fetchone()
                if row:
                    return {
                        "id":                         row[0],
                        "production_record_id":       row[1],
                        "milk_amount":                row[2],
                        "ph":                         row[3],
                        "dodanie_kultur_start":       row[4],
                        "dodanie_kultur_end":         row[5],
                        "podpuszczka_start":          row[6],
                        "podpuszczka_end":            row[7],
                        "krojenie_start":             row[8],
                        "krojenie_end":               row[9],
                        "serwatka_start":             row[10],
                        "serwatka_end":               row[11],
                        "dogrzewanie_start":          row[12],
                        "dogrzewanie_end":            row[13],
                        "dosuszanie_start":           row[14],
                        "dosuszanie_end":             row[15],
                        "wstepne_prasowanie_start":   row[16],
                        "wstepne_prasowanie_end":     row[17],
                        "formy_wielkosc":             row[18],
                        "formy_ilosc":                row[19],
                        "solenie_start":              row[20],
                        "solenie_end":                row[21],
                        "pasteryzacja":               row[22],
                    }
                else:
                    return {}
        except sqlite3.Error as e:
            print(f"Błąd przy pobieraniu ser_production_details: {e}")
            return {}


    def delete_ser_production_details(self, production_record_id: int) -> None:
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM ser_production_details
                    WHERE production_record_id = ?
                """, (production_record_id,))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Błąd przy usuwaniu ser_production_details: {e}")
            raise

    def get_next_series_number_for_month(self, month: int, full_year: int) -> int:
        """
        Zwraca KOLEJNY numer (integer) na podstawie tego,
        jaki najwyższy numer serii jest w danym (miesiącu, roku) w production_records.
        Format np. '00712_2024' -> bierzemy pierwsze 3 cyfry jako numer kolejny.
        """
        month_str = f"{month:02d}"
        year_str = str(full_year)

        sql = """
            SELECT series
            FROM production_records
            WHERE
                strftime('%m', date) = ?
                AND strftime('%Y', date) = ?
            ORDER BY series DESC
            LIMIT 1
        """

        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (month_str, year_str))
                row = cursor.fetchone()
                if row:
                    last_series = row[0]  # np. "00712_2024"
                    last_num_str = last_series[:3]  # "007"
                    last_num = int(last_num_str)
                    return last_num + 1
                else:
                    return 1
        except Exception as e:
            print(f"[DBManager] Błąd w get_next_series_number_for_month: {e}")
            return 1

    def get_product_by_id(self, product_id: int) -> Optional[dict]:
        """
        Zwraca słownik z informacjami o produkcie (id, name, category_id),
        albo None, jeśli nie znaleziono wiersza w bazie.
        """
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, category_id FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "name": row[1], "category_id": row[2]}
            return None

    # ----------------------------------------------------------------
    # -------------- ser_production_additives (CRUD) ----------------
    # (bez kolumny "time_added", bo usuwamy "Godz. dodania")
    # ----------------------------------------------------------------

    def clear_ser_production_additives_for_record(self, record_id: int) -> None:
        """
        Usuwa wszystkie dodatki (ser_production_additives) powiązane z danym protokołem
        (production_record_id).
        """
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM ser_production_additives
                WHERE production_record_id = ?
            """, (record_id,))
            conn.commit()

    def add_ser_production_additive(
        self,
        production_record_id: int,
        cat_name: str,
        add_name: str,
        dose_str: str
        # usunięto time_str
    ) -> None:
        """
        Dodaje jeden wiersz do 'ser_production_additives' – kategoria dodatku, nazwa, dawka.
        Kolumny: production_record_id, additive_category, additive_name, dose_calculated.
        """
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ser_production_additives (
                    production_record_id,
                    additive_category,
                    additive_name,
                    dose_calculated
                )
                VALUES (?, ?, ?, ?)
            """, (production_record_id, cat_name, add_name, dose_str))
            conn.commit()
    def add_ser_production_details_extended(
        self,
        production_record_id: int,
        milk_amount: str,
        ph: str,
        pasteryzacja: str,
        dodanie_kultur_start: str,
        dodanie_kultur_end: str,
        podpuszczka_start: str,
        podpuszczka_end: str,
        krojenie_start: str,
        krojenie_end: str,
        serwatka_start: str,
        serwatka_end: str,
        dogrzewanie_start: str,
        dogrzewanie_end: str,
        dosuszanie_start: str,
        dosuszanie_end: str,
        wstepne_prasowanie_start: str,
        wstepne_prasowanie_end: str,
        formy_wielkosc: str,
        formy_ilosc: str,
        solenie_start: str,
        solenie_end: str
    ) -> None:
        """
        Wstawia nowy wiersz do ser_production_details z pełnym zestawem pól,
        w tym polem 'pasteryzacja' i 9 czynności (start/end).
        """
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO ser_production_details (
                    production_record_id,
                    milk_amount,
                    ph,
                    dodanie_kultur_start,
                    dodanie_kultur_end,
                    podpuszczka_start,
                    podpuszczka_end,
                    krojenie_start,
                    krojenie_end,
                    serwatka_start,
                    serwatka_end,
                    dogrzewanie_start,
                    dogrzewanie_end,
                    dosuszanie_start,
                    dosuszanie_end,
                    wstepne_prasowanie_start,
                    wstepne_prasowanie_end,
                    formy_wielkosc,
                    formy_ilosc,
                    solenie_start,
                    solenie_end,
                    pasteryzacja
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    production_record_id,
                    milk_amount,
                    ph,
                    dodanie_kultur_start,
                    dodanie_kultur_end,
                    podpuszczka_start,
                    podpuszczka_end,
                    krojenie_start,
                    krojenie_end,
                    serwatka_start,
                    serwatka_end,
                    dogrzewanie_start,
                    dogrzewanie_end,
                    dosuszanie_start,
                    dosuszanie_end,
                    wstepne_prasowanie_start,
                    wstepne_prasowanie_end,
                    formy_wielkosc,
                    formy_ilosc,
                    solenie_start,
                    solenie_end,
                    pasteryzacja
                )
            )
            conn.commit()

    def add_ser_production_additive_3col(
        self,
        production_record_id: int,
        cat_name: str,
        add_name: str,
        dose_str: str
    ) -> None:
        """
        Wstawia nowy wiersz do ser_production_additives z 3 kolumnami:
        - additive_category (cat_name),
        - additive_name     (add_name),
        - dose_calculated   (dose_str).
        Nie zapisujemy godziny/czasu.
        """
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ser_production_additives (
                    production_record_id,
                    additive_category,
                    additive_name,
                    dose_calculated
                )
                VALUES (?, ?, ?, ?)
            """, (production_record_id, cat_name, add_name, dose_str))
            conn.commit()

    def update_ser_production_details_extended(
        self,
        production_record_id: int,
        milk_amount: str,
        ph: str,
        pasteryzacja: str,
        dodanie_kultur_start: str,
        dodanie_kultur_end: str,
        podpuszczka_start: str,
        podpuszczka_end: str,
        krojenie_start: str,
        krojenie_end: str,
        serwatka_start: str,
        serwatka_end: str,
        dogrzewanie_start: str,
        dogrzewanie_end: str,
        dosuszanie_start: str,
        dosuszanie_end: str,
        wstepne_prasowanie_start: str,
        wstepne_prasowanie_end: str,
        formy_wielkosc: str,
        formy_ilosc: str,
        solenie_start: str,
        solenie_end: str
    ) -> None:
        """
        Aktualizuje istniejący wiersz w ser_production_details (zidentyfikowany
        przez production_record_id), uwzględniając pole 'pasteryzacja' i 9 czynności.
        """
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE ser_production_details
                SET
                    milk_amount               = ?,
                    ph                       = ?,
                    pasteryzacja            = ?,
                    dodanie_kultur_start    = ?,
                    dodanie_kultur_end      = ?,
                    podpuszczka_start       = ?,
                    podpuszczka_end         = ?,
                    krojenie_start          = ?,
                    krojenie_end            = ?,
                    serwatka_start          = ?,
                    serwatka_end            = ?,
                    dogrzewanie_start       = ?,
                    dogrzewanie_end         = ?,
                    dosuszanie_start        = ?,
                    dosuszanie_end          = ?,
                    wstepne_prasowanie_start= ?,
                    wstepne_prasowanie_end  = ?,
                    formy_wielkosc          = ?,
                    formy_ilosc             = ?,
                    solenie_start           = ?,
                    solenie_end             = ?
                WHERE production_record_id = ?
                """,
                (
                    milk_amount,
                    ph,
                    pasteryzacja,
                    dodanie_kultur_start,
                    dodanie_kultur_end,
                    podpuszczka_start,
                    podpuszczka_end,
                    krojenie_start,
                    krojenie_end,
                    serwatka_start,
                    serwatka_end,
                    dogrzewanie_start,
                    dogrzewanie_end,
                    dosuszanie_start,
                    dosuszanie_end,
                    wstepne_prasowanie_start,
                    wstepne_prasowanie_end,
                    formy_wielkosc,
                    formy_ilosc,
                    solenie_start,
                    solenie_end,
                    production_record_id  # warunek w WHERE
                )
            )
            conn.commit()


    def add_fermented_production_details(
        self,
        production_record_id: int,
        milk_type: str,
        amt: str,
        ph: str,
        pasteryzacja: str,
        dod_kultur_godz: str,
        dod_kultur_czas: str,
        rozl_start: str,
        rozl_end: str,
        ink_temp: str,
        ink_czas: str,
        chl_godz: str,
        chl_temp_end: str
    ) -> None:
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO fermented_production_details (
                    production_record_id,
                    milk_type,
                    amt,
                    ph,
                    pasteryzacja,
                    dod_kultur_godz,
                    dod_kultur_czas,
                    rozl_start,
                    rozl_end,
                    ink_temp,
                    ink_czas,
                    chl_godz,
                    chl_temp_end
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                production_record_id,
                milk_type,
                amt,
                ph,
                pasteryzacja,
                dod_kultur_godz,
                dod_kultur_czas,
                rozl_start,
                rozl_end,
                ink_temp,
                ink_czas,
                chl_godz,
                chl_temp_end
            ))
            conn.commit()

    def update_fermented_production_details(
        self,
        production_record_id: int,
        milk_type: str,
        amt: str,
        ph: str,
        pasteryzacja: str,
        dod_kultur_godz: str,
        dod_kultur_czas: str,
        rozl_start: str,
        rozl_end: str,
        ink_temp: str,
        ink_czas: str,
        chl_godz: str,
        chl_temp_end: str
    ) -> None:
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE fermented_production_details
                SET
                    milk_type = ?,
                    amt = ?,
                    ph = ?,
                    pasteryzacja = ?,
                    dod_kultur_godz = ?,
                    dod_kultur_czas = ?,
                    rozl_start = ?,
                    rozl_end = ?,
                    ink_temp = ?,
                    ink_czas = ?,
                    chl_godz = ?,
                    chl_temp_end = ?
                WHERE production_record_id = ?
            """, (
                milk_type,
                amt,
                ph,
                pasteryzacja,
                dod_kultur_godz,
                dod_kultur_czas,
                rozl_start,
                rozl_end,
                ink_temp,
                ink_czas,
                chl_godz,
                chl_temp_end,
                production_record_id
            ))
            conn.commit()

    def get_fermented_production_details(self, production_record_id: int) -> Dict[str, Any]:
        """
        Pobiera szczegóły z tabeli fermented_production_details
        dla danego production_record_id.
        """
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id,
                    production_record_id,
                    milk_type,
                    amt,
                    ph,
                    pasteryzacja,
                    dod_kultur_godz,
                    dod_kultur_czas,
                    rozl_start,
                    rozl_end,
                    ink_temp,
                    ink_czas,
                    chl_godz,
                    chl_temp_end
                FROM fermented_production_details
                WHERE production_record_id = ?
            """, (production_record_id,))

            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "production_record_id": row[1],
                    "milk_type": row[2],
                    "amt": row[3],
                    "ph": row[4],
                    "pasteryzacja": row[5],
                    "dod_kultur_godz": row[6],
                    "dod_kultur_czas": row[7],
                    "rozl_start": row[8],
                    "rozl_end": row[9],
                    "ink_temp": row[10],
                    "ink_czas": row[11],
                    "chl_godz": row[12],
                    "chl_temp_end": row[13]
                }
            else:
                return {}
    # -------------- TWAROG (CRUD) --------------
    def add_twarog_production_details(
        self,
        production_record_id: int,
        milk_type: str,
        milk_amount: str,
        ph: str,
        pasteryzacja: str,
        krojenie_start: str,
        krojenie_end: str,
        dogrzewanie_start: str,
        dogrzewanie_end: str,
        formy_wielkosc: str,
        formy_ilosc: str,
        solenie_start: str,
        solenie_end: str
    ) -> None:
        """
        Dodaje nowy wiersz do tabeli twarog_production_details.
        """
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO twarog_production_details (
                    production_record_id,
                    milk_type,       
                    milk_amount,
                    ph,
                    pasteryzacja,
                    krojenie_start,
                    krojenie_end,
                    dogrzewanie_start,
                    dogrzewanie_end,
                    formy_wielkosc,
                    formy_ilosc,
                    solenie_start,
                    solenie_end
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                production_record_id,
                milk_type,
                milk_amount,
                ph,
                pasteryzacja,
                krojenie_start,
                krojenie_end,
                dogrzewanie_start,
                dogrzewanie_end,
                formy_wielkosc,
                formy_ilosc,
                solenie_start,
                solenie_end
            ))
            conn.commit()


    def get_twarog_production_details(self, production_record_id: int) -> dict:
        """
        Pobiera wiersz z twarog_production_details dla danego production_record_id.
        Zwraca słownik z kluczami odpowiadającymi kolumnom w tabeli.
        Jeśli brak — zwraca pusty słownik {}.
        """
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        id,
                        production_record_id,
                        milk_type,
                        milk_amount,
                        ph,
                        pasteryzacja,
                        krojenie_start,
                        krojenie_end,
                        dogrzewanie_start,
                        dogrzewanie_end,
                        formy_wielkosc,
                        formy_ilosc,
                        solenie_start,
                        solenie_end
                    FROM twarog_production_details
                    WHERE production_record_id = ?
                """, (production_record_id,))
                row = cursor.fetchone()
                if row:
                    return {
                        "id":                  row[0],
                        "production_record_id": row[1],
                        "milk_type":            row[2],
                        "milk_amount":         row[3],
                        "ph":                  row[4],
                        "pasteryzacja":        row[5],
                        "krojenie_start":      row[6],
                        "krojenie_end":        row[7],
                        "dogrzewanie_start":   row[8],
                        "dogrzewanie_end":     row[9],
                        "formy_wielkosc":      row[10],
                        "formy_ilosc":         row[11],
                        "solenie_start":       row[12],
                        "solenie_end":         row[13],
                    }
                else:
                    return {}
        except Exception as e:
            print(f"[DBManager] Błąd w get_twarog_production_details: {e}")
            return {}


    def update_twarog_production_details(
        self,
        production_record_id: int,
        milk_type: str,
        milk_amount: str,
        ph: str,
        pasteryzacja: str,
        krojenie_start: str,
        krojenie_end: str,
        dogrzewanie_start: str,
        dogrzewanie_end: str,
        formy_wielkosc: str,
        formy_ilosc: str,
        solenie_start: str,
        solenie_end: str
    ) -> None:
        """
        Aktualizuje istniejący wiersz w twarog_production_details
        (identyfikowany przez production_record_id).
        """
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE twarog_production_details
                SET
                    milk_type        = ?,  
                    milk_amount       = ?,
                    ph               = ?,
                    pasteryzacja     = ?,
                    krojenie_start   = ?,
                    krojenie_end     = ?,
                    dogrzewanie_start= ?,
                    dogrzewanie_end  = ?,
                    formy_wielkosc   = ?,
                    formy_ilosc      = ?,
                    solenie_start    = ?,
                    solenie_end      = ?
                WHERE production_record_id = ?
            """, (
                milk_type,
                milk_amount,
                ph,
                pasteryzacja,
                krojenie_start,
                krojenie_end,
                dogrzewanie_start,
                dogrzewanie_end,
                formy_wielkosc,
                formy_ilosc,
                solenie_start,
                solenie_end,
                production_record_id
            ))
            conn.commit()
    def fill_additives_from_record(self, record_id: int) -> None:
        self.clear_additives_fields()

        if not self.db_manager:
            return

        # załóżmy, że w DBManager mamy:
        #    get_ser_production_additives_for_record(record_id) 
        # zwracające listę słowników: [ 
        #   { "additive_category":..., "additive_name":..., "dose_calculated":... }, … 
        # ]
        lines = self.db_manager.get_ser_production_additives_for_record(record_id)
        for i, row in enumerate(lines):
            if i >= len(self.additive_lines):
                break
            cat_str = row.get("additive_category", "")
            add_str = row.get("additive_name", "")
            dose_str = row.get("dose_calculated", "")

            # parse dosage:
            base_val, unit = parse_dosage(dose_str)
            self.additives_info[i] = (base_val, unit)

            # wypełniamy pola wiersza
            cat_edit, add_edit, dose_edit = self.additive_lines[i]
            cat_edit.setText(cat_str)
            add_edit.setText(add_str)
            # Możemy wstawić:
            dose_edit.setText(dose_str)  # np. "30.0 g"
        # ewentualnie na końcu update_doses() – ale to znów przeliczy
        # i może nadpisać. Więc jeśli chcemy to ZACHOWAĆ, możemy pominąć 
        # update_doses() 
    def get_ser_production_additives_for_record(self, record_id: int) -> List[dict]:
        result = []
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                id,
                additive_category,
                additive_name,
                dose_calculated
                FROM ser_production_additives
                WHERE production_record_id = ?
            """, (record_id,))
            rows = cursor.fetchall()
            for row in rows:
                result.append({
                    "id":               row[0],
                    "additive_category": row[1],
                    "additive_name":     row[2],
                    "dose_calculated":   row[3],
                })
        return result
