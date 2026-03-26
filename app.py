"""
Expense Tracker — Hauptapplikation.

Streamlit Entry Point mit drei Tabs: Dashboard, Ausgabe erfassen,
Einstellungen. Datenbank wird beim Start automatisch initialisiert.

Starten mit: streamlit run app.py
"""

from datetime import datetime, date

import pandas as pd
import streamlit as st

from utils.database import init_database, CATEGORIES
from utils.expenses import (
    add_expense,
    delete_expense,
    get_expenses,
    get_monthly_summary,
    get_budget_status,
    set_budget,
    get_budgets,
)
from utils.csv_handler import export_expenses, import_from_csv
from components.charts import (
    create_category_donut,
    create_daily_trend,
    create_budget_bars,
    create_monthly_comparison,
)

# Datenbank initialisieren
init_database()

# ── Seiten-Konfiguration ──────────────────────────────────────────────
st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0E1117; }
    h1, h2, h3 { color: #2DD4A8 !important; }

    [data-testid="stMetric"] {
        background-color: #161B22;
        border: 1px solid #1E2330;
        border-radius: 8px;
        padding: 12px 16px;
    }

    [data-testid="stMetricLabel"] { color: #8B949E !important; }

    [data-testid="stSidebar"] {
        background-color: #0D1117;
        border-right: 1px solid #1E2330;
    }

    .stButton > button {
        background-color: #2DD4A8;
        color: white;
        border: none;
        border-radius: 6px;
    }
    .stButton > button:hover {
        background-color: #22A885;
        color: white;
    }

    .stTabs [data-baseweb="tab"] {
        color: #8B949E;
    }
    .stTabs [aria-selected="true"] {
        color: #2DD4A8 !important;
        border-bottom-color: #2DD4A8 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar: Monatsauswahl ─────────────────────────────────────────────
st.sidebar.title("Expense Tracker")

today = date.today()
selected_year = st.sidebar.selectbox(
    "Jahr",
    options=list(range(today.year, today.year - 5, -1)),
    index=0,
)
selected_month = st.sidebar.selectbox(
    "Monat",
    options=list(range(1, 13)),
    index=today.month - 1,
    format_func=lambda m: datetime(2000, m, 1).strftime("%B"),
)

st.sidebar.markdown("---")

# CSV Import
st.sidebar.subheader("CSV Import")
uploaded_file = st.sidebar.file_uploader(
    "CSV-Datei hochladen",
    type=["csv"],
    help="Spalten: date, amount, category, description (optional)",
)

if uploaded_file and st.sidebar.button("Importieren"):
    result = import_from_csv(uploaded_file.getvalue())
    if result["imported"] > 0:
        st.sidebar.success(f"{result['imported']} Ausgaben importiert.")
    if result["skipped"] > 0:
        st.sidebar.warning(f"{result['skipped']} Zeilen uebersprungen.")
    if result["errors"]:
        for err in result["errors"][:3]:
            st.sidebar.error(err)
    st.rerun()

# CSV Export
st.sidebar.subheader("CSV Export")
csv_data = export_expenses(selected_year, selected_month)
st.sidebar.download_button(
    label="Monat als CSV exportieren",
    data=csv_data,
    file_name=f"expenses_{selected_year}_{selected_month:02d}.csv",
    mime="text/csv",
    use_container_width=True,
)

# ── Tabs ───────────────────────────────────────────────────────────────
tab_dashboard, tab_add, tab_settings = st.tabs(
    ["Dashboard", "Ausgabe erfassen", "Budgets"]
)

# ── Tab 1: Dashboard ──────────────────────────────────────────────────
with tab_dashboard:
    summary = get_monthly_summary(selected_year, selected_month)

    # Metrikkarten
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Gesamtausgaben", f"{summary['total']:.2f} EUR")
    with col2:
        st.metric("Anzahl Buchungen", summary["count"])
    with col3:
        st.metric("Tagesdurchschnitt", f"{summary['daily_avg']:.2f} EUR")
    with col4:
        st.metric("Top Kategorie", summary["top_category"])

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    if summary["by_category"]:
        col_left, col_right = st.columns(2)

        with col_left:
            donut = create_category_donut(summary["by_category"])
            st.plotly_chart(donut, use_container_width=True, config={"displayModeBar": False})

        with col_right:
            df_month = get_expenses(selected_year, selected_month)
            trend = create_daily_trend(df_month)
            st.plotly_chart(trend, use_container_width=True, config={"displayModeBar": False})

        # Budget-Auslastung
        budget_status = get_budget_status(selected_year, selected_month)
        if budget_status:
            budget_chart = create_budget_bars(budget_status)
            st.plotly_chart(budget_chart, use_container_width=True, config={"displayModeBar": False})

        # Monatsvergleich (alle Daten)
        all_expenses = get_expenses()
        if not all_expenses.empty:
            comparison = create_monthly_comparison(all_expenses)
            st.plotly_chart(comparison, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info(
            "Noch keine Ausgaben fuer diesen Monat. "
            "Erfasse deine erste Ausgabe im Tab 'Ausgabe erfassen'."
        )

    # Transaktionsliste
    if summary["count"] > 0:
        st.subheader("Letzte Buchungen")
        df_display = get_expenses(selected_year, selected_month)
        df_display["date"] = df_display["date"].dt.strftime("%d.%m.%Y")
        df_display["amount"] = df_display["amount"].apply(lambda x: f"{x:.2f} EUR")

        for _, row in df_display.head(20).iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 3, 4, 1])
            with col1:
                st.text(row["date"])
            with col2:
                st.text(row["amount"])
            with col3:
                st.text(row["category"])
            with col4:
                st.text(row["description"] if row["description"] else "—")
            with col5:
                if st.button("X", key=f"del_{row['id']}"):
                    delete_expense(row["id"])
                    st.rerun()

# ── Tab 2: Ausgabe erfassen ────────────────────────────────────────────
with tab_add:
    st.subheader("Neue Ausgabe erfassen")

    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            amount = st.number_input(
                "Betrag (EUR)",
                min_value=0.01,
                step=0.50,
                format="%.2f",
            )
            category = st.selectbox("Kategorie", options=CATEGORIES)

        with col2:
            expense_date = st.date_input("Datum", value=today)
            description = st.text_input(
                "Beschreibung",
                placeholder="z.B. Wocheneinkauf REWE",
            )

        submitted = st.form_submit_button(
            "Ausgabe speichern",
            use_container_width=True,
        )

        if submitted:
            add_expense(
                amount=amount,
                category=category,
                date=expense_date.strftime("%Y-%m-%d"),
                description=description,
            )
            st.success(
                f"{amount:.2f} EUR in '{category}' gespeichert."
            )
            st.rerun()

# ── Tab 3: Budgets ─────────────────────────────────────────────────────
with tab_settings:
    st.subheader("Monatliche Budget-Limits")
    st.caption("Setze Limits pro Kategorie, um deine Ausgaben im Blick zu behalten.")

    current_budgets = get_budgets()

    with st.form("budget_form"):
        cols = st.columns(2)

        for i, category in enumerate(CATEGORIES):
            with cols[i % 2]:
                current_value = current_budgets.get(category, 0.0)
                new_value = st.number_input(
                    category,
                    min_value=0.0,
                    value=current_value,
                    step=50.0,
                    format="%.2f",
                    key=f"budget_{category}",
                )

        save_budgets = st.form_submit_button(
            "Budgets speichern",
            use_container_width=True,
        )

        if save_budgets:
            for category in CATEGORIES:
                value = st.session_state.get(f"budget_{category}", 0.0)
                if value > 0:
                    set_budget(category, value)
            st.success("Budget-Limits gespeichert.")
            st.rerun()
