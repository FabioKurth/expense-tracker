"""
SQLite Datenbank-Schicht.

Verwaltet die lokale Datenbank fuer Ausgaben und Budgets.
Erstellt Tabellen automatisch beim ersten Aufruf.
Die .db-Datei liegt lokal und wird nicht ins Git committed.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

DB_PATH = Path(__file__).parent.parent / "expenses.db"


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context Manager fuer Datenbankverbindungen.

    Sorgt dafuer, dass Verbindungen immer sauber geschlossen
    und Transaktionen bei Fehlern zurueckgerollt werden.
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database() -> None:
    """
    Erstellt die Datenbanktabellen falls sie noch nicht existieren.

    Tabellen:
    - expenses: Alle Ausgaben mit Betrag, Kategorie, Datum, Notiz
    - budgets: Monatliche Budget-Limits pro Kategorie
    """
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL UNIQUE,
                monthly_limit REAL NOT NULL
            )
        """)


# Vordefinierte Kategorien
CATEGORIES = [
    "Lebensmittel",
    "Wohnen",
    "Transport",
    "Unterhaltung",
    "Gesundheit",
    "Kleidung",
    "Bildung",
    "Restaurant",
    "Abonnements",
    "Sonstiges",
]
