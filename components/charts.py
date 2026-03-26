"""
Chart-Erstellung mit Plotly.

Alle Diagramme fuer den Expense Tracker: Kategorie-Verteilung,
Zeitverlauf und Budget-Auslastung. Einheitliches Dark Theme.
"""

import pandas as pd
import plotly.graph_objects as go

# Design-Konstanten
BG_COLOR = "#0E1117"
ACCENT_COLOR = "#E20074"
GRID_COLOR = "#1E2330"
TEXT_COLOR = "#FAFAFA"
GREEN = "#00D26A"
RED = "#FF4444"
YELLOW = "#FFB800"

# Farbpalette fuer Kategorien
CATEGORY_COLORS = [
    "#E20074", "#00BFFF", "#FFA500", "#00D26A", "#FF6B6B",
    "#C084FC", "#F472B6", "#34D399", "#FBBF24", "#94A3B8",
]


def _apply_dark_layout(fig: go.Figure, title: str = "") -> go.Figure:
    """Wendet das einheitliche Dark Theme auf einen Chart an."""
    fig.update_layout(
        title=dict(text=title, font=dict(color=TEXT_COLOR, size=16)),
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(color=TEXT_COLOR),
        xaxis=dict(gridcolor=GRID_COLOR, showgrid=True),
        yaxis=dict(gridcolor=GRID_COLOR, showgrid=True),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_COLOR)),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def create_category_donut(by_category: dict[str, float]) -> go.Figure:
    """
    Erstellt ein Donut-Diagramm der Ausgaben nach Kategorie.

    Zeigt sowohl den Anteil als auch den absoluten Betrag pro Kategorie.
    """
    categories = list(by_category.keys())
    values = list(by_category.values())

    fig = go.Figure(data=[go.Pie(
        labels=categories,
        values=values,
        hole=0.5,
        marker=dict(colors=CATEGORY_COLORS[:len(categories)]),
        textinfo="label+percent",
        textfont=dict(color=TEXT_COLOR),
        hovertemplate="%{label}<br>%{value:.2f} EUR<br>%{percent}<extra></extra>",
    )])

    _apply_dark_layout(fig, "Ausgaben nach Kategorie")
    fig.update_layout(height=400, showlegend=True)

    return fig


def create_daily_trend(df: pd.DataFrame) -> go.Figure:
    """
    Erstellt einen Linien-Chart mit taeglichen Ausgaben.

    Zeigt den Verlauf ueber den Monat mit einer kumulativen Linie.
    """
    if df.empty:
        fig = go.Figure()
        _apply_dark_layout(fig, "Tagesausgaben")
        return fig

    daily = df.groupby(df["date"].dt.date)["amount"].sum().reset_index()
    daily.columns = ["date", "amount"]
    daily = daily.sort_values("date")
    daily["cumulative"] = daily["amount"].cumsum()

    fig = go.Figure()

    # Tagesbalken
    fig.add_trace(go.Bar(
        x=daily["date"],
        y=daily["amount"],
        name="Tagesausgaben",
        marker_color=ACCENT_COLOR,
        hovertemplate="%{y:.2f} EUR<extra></extra>",
    ))

    # Kumulative Linie
    fig.add_trace(go.Scatter(
        x=daily["date"],
        y=daily["cumulative"],
        name="Kumulativ",
        mode="lines+markers",
        line=dict(color="#00BFFF", width=2),
        marker=dict(size=4),
        yaxis="y2",
        hovertemplate="%{y:.2f} EUR<extra></extra>",
    ))

    _apply_dark_layout(fig, "Tagesausgaben")
    fig.update_layout(
        height=350,
        yaxis=dict(title="Tagesausgaben (EUR)"),
        yaxis2=dict(
            title="Kumulativ (EUR)",
            overlaying="y",
            side="right",
            gridcolor="rgba(0,0,0,0)",
        ),
        hovermode="x unified",
    )

    return fig


def create_budget_bars(budget_status: list[dict]) -> go.Figure:
    """
    Erstellt ein horizontales Balkendiagramm fuer die Budget-Auslastung.

    Gruen = unter Budget, Gelb = nahe am Limit, Rot = ueberschritten.
    """
    if not budget_status:
        fig = go.Figure()
        _apply_dark_layout(fig, "Budget-Auslastung")
        return fig

    categories = [b["category"] for b in budget_status]
    percentages = [b["percentage"] for b in budget_status]

    # Farbe je nach Auslastung
    colors = []
    for b in budget_status:
        if b["over_budget"]:
            colors.append(RED)
        elif b["percentage"] > 80:
            colors.append(YELLOW)
        else:
            colors.append(GREEN)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=categories,
        x=percentages,
        orientation="h",
        marker_color=colors,
        text=[f"{p:.0f}%" for p in percentages],
        textposition="auto",
        textfont=dict(color=TEXT_COLOR),
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
    ))

    _apply_dark_layout(fig, "Budget-Auslastung")
    fig.update_layout(
        height=max(200, len(categories) * 50),
        xaxis=dict(title="Auslastung (%)", range=[0, 110]),
        showlegend=False,
    )

    # 100%-Linie
    fig.add_vline(x=100, line_dash="dot", line_color=TEXT_COLOR, line_width=1)

    return fig


def create_monthly_comparison(df: pd.DataFrame) -> go.Figure:
    """
    Erstellt einen Vergleich der monatlichen Gesamtausgaben.

    Zeigt die letzten Monate als Balkendiagramm.
    """
    if df.empty:
        fig = go.Figure()
        _apply_dark_layout(fig, "Monatsvergleich")
        return fig

    df = df.copy()
    df["month"] = df["date"].dt.to_period("M").astype(str)
    monthly = df.groupby("month")["amount"].sum().reset_index()
    monthly = monthly.sort_values("month")

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=monthly["month"],
        y=monthly["amount"],
        marker_color=ACCENT_COLOR,
        hovertemplate="%{y:.2f} EUR<extra></extra>",
    ))

    _apply_dark_layout(fig, "Monatsvergleich")
    fig.update_layout(
        height=300,
        yaxis=dict(title="Gesamt (EUR)"),
        showlegend=False,
    )

    return fig
