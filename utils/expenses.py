"""
Geschaeftslogik fuer Ausgaben und Budgets.

CRUD-Operationen und Aggregationen fuer die Ausgaben-Datenbank.
Alle Datenbankzugriffe laufen ueber den Context Manager aus database.py.
"""

from datetime import datetime

import pandas as pd

from utils.database import get_connection


def add_expense(
    amount: float,
    category: str,
    date: str,
    description: str = "",
) -> int:
    """
    Speichert eine neue Ausgabe in der Datenbank.

    Args:
        amount: Betrag in Euro
        category: Kategorie (z.B. "Lebensmittel")
        date: Datum im Format "YYYY-MM-DD"
        description: Optionale Beschreibung

    Returns:
        ID der neuen Ausgabe
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO expenses (amount, category, date, description) VALUES (?, ?, ?, ?)",
            (amount, category, date, description),
        )
        return cursor.lastrowid


def delete_expense(expense_id: int) -> bool:
    """Loescht eine Ausgabe anhand ihrer ID."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        return cursor.rowcount > 0


def get_expenses(
    year: int | None = None,
    month: int | None = None,
) -> pd.DataFrame:
    """
    Holt Ausgaben aus der Datenbank, optional gefiltert nach Jahr/Monat.

    Returns:
        DataFrame mit Spalten: id, amount, category, date, description
    """
    query = "SELECT id, amount, category, date, description FROM expenses"
    params: list = []

    if year and month:
        query += " WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?"
        params = [str(year), f"{month:02d}"]
    elif year:
        query += " WHERE strftime('%Y', date) = ?"
        params = [str(year)]

    query += " ORDER BY date DESC"

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df["amount"] = df["amount"].astype(float)

    return df


def get_monthly_summary(year: int, month: int) -> dict:
    """
    Berechnet eine Zusammenfassung fuer einen Monat.

    Returns:
        Dictionary mit: total, count, daily_avg, top_category, by_category
    """
    df = get_expenses(year, month)

    if df.empty:
        return {
            "total": 0.0,
            "count": 0,
            "daily_avg": 0.0,
            "top_category": "—",
            "by_category": {},
        }

    by_category = df.groupby("category")["amount"].sum().to_dict()
    top_category = max(by_category, key=by_category.get)

    # Anzahl Tage im Monat mit Ausgaben fuer den Durchschnitt
    days_in_data = df["date"].dt.day.nunique()
    daily_avg = df["amount"].sum() / max(days_in_data, 1)

    return {
        "total": df["amount"].sum(),
        "count": len(df),
        "daily_avg": daily_avg,
        "top_category": top_category,
        "by_category": by_category,
    }


def set_budget(category: str, monthly_limit: float) -> None:
    """Setzt oder aktualisiert das monatliche Budget fuer eine Kategorie."""
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO budgets (category, monthly_limit)
               VALUES (?, ?)
               ON CONFLICT(category) DO UPDATE SET monthly_limit = ?""",
            (category, monthly_limit, monthly_limit),
        )


def get_budgets() -> dict[str, float]:
    """
    Holt alle Budget-Limits.

    Returns:
        Dictionary: Kategorie -> monatliches Limit
    """
    with get_connection() as conn:
        rows = conn.execute("SELECT category, monthly_limit FROM budgets").fetchall()
    return {row["category"]: row["monthly_limit"] for row in rows}


def get_budget_status(year: int, month: int) -> list[dict]:
    """
    Vergleicht Ausgaben mit Budget-Limits fuer einen Monat.

    Returns:
        Liste von Dicts mit: category, spent, limit, remaining, percentage
    """
    budgets = get_budgets()
    summary = get_monthly_summary(year, month)
    by_category = summary["by_category"]

    status = []
    for category, limit in budgets.items():
        spent = by_category.get(category, 0.0)
        remaining = limit - spent
        percentage = (spent / limit * 100) if limit > 0 else 0

        status.append({
            "category": category,
            "spent": spent,
            "limit": limit,
            "remaining": remaining,
            "percentage": min(percentage, 100),
            "over_budget": spent > limit,
        })

    return sorted(status, key=lambda x: x["percentage"], reverse=True)
