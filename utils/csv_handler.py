"""
CSV Import und Export.

Ermoeglicht den Import von Kontoauszuegen und den Export
der eigenen Ausgaben als CSV-Datei.
"""

import io

import pandas as pd

from utils.expenses import add_expense, get_expenses


def export_expenses(year: int | None = None, month: int | None = None) -> str:
    """
    Exportiert Ausgaben als CSV-String.

    Args:
        year: Optional - nur Ausgaben aus diesem Jahr
        month: Optional - nur Ausgaben aus diesem Monat

    Returns:
        CSV-formatierter String zum Download
    """
    df = get_expenses(year, month)

    if df.empty:
        return "date,amount,category,description\n"

    export_df = df[["date", "amount", "category", "description"]].copy()
    export_df["date"] = export_df["date"].dt.strftime("%Y-%m-%d")

    return export_df.to_csv(index=False)


def import_from_csv(file_content: bytes) -> dict:
    """
    Importiert Ausgaben aus einer CSV-Datei.

    Erwartet mindestens die Spalten: date, amount, category
    Optional: description

    Returns:
        Dictionary mit: imported (Anzahl), skipped (Anzahl), errors (Liste)
    """
    result = {"imported": 0, "skipped": 0, "errors": []}

    try:
        df = pd.read_csv(io.BytesIO(file_content))
    except Exception as e:
        result["errors"].append(f"CSV konnte nicht gelesen werden: {e}")
        return result

    # Pflichtfelder pruefen
    required = {"date", "amount", "category"}
    missing = required - set(df.columns)
    if missing:
        result["errors"].append(f"Fehlende Spalten: {', '.join(missing)}")
        return result

    for idx, row in df.iterrows():
        try:
            amount = float(row["amount"])
            if amount <= 0:
                result["skipped"] += 1
                continue

            date = pd.to_datetime(row["date"]).strftime("%Y-%m-%d")
            category = str(row["category"]).strip()
            description = str(row.get("description", "")).strip()

            if description == "nan":
                description = ""

            add_expense(amount, category, date, description)
            result["imported"] += 1

        except (ValueError, TypeError) as e:
            result["skipped"] += 1
            result["errors"].append(f"Zeile {idx + 2}: {e}")

    return result
