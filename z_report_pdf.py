"""
PDF report: Skinner illocutionary analysis of Králická Bible.
Generates output/final_summary/skinner_report.pdf

Sections:
  1. Primary intention distribution
  2. Illocutionary force  +  Secondary intention
  3. Primary strategy     +  Secondary strategy
  4. Convention types (top 20)
  5. Anti-anachronism analysis
  6. Political vocabulary
  7. By book (stacked)
  8. Extended sentence sample (all key columns)
"""

import io
import re
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as mcm
import pandas as pd
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak,
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from a_paths import OUTPUT_DIR as ROOT_OUTPUT

# ── Fonts ───────────────────────────────────────────────────────────────────
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
pdfmetrics.registerFont(TTFont("DV",     str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DV-B",   str(FONT_DIR / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DV-Ser", str(FONT_DIR / "DejaVuSerif.ttf")))

# ── Paths ────────────────────────────────────────────────────────────────────
OUT  = ROOT_OUTPUT / "final_summary"
OUT.mkdir(parents=True, exist_ok=True)

ANA = ROOT_OUTPUT / "q_skinner_analytics"
CORPUS_CSV      = ANA / "q_skinner_corpus_full.csv"
BY_BOOK_CSV     = ANA / "q_intention_by_book.csv"
INTENT_CNT_CSV  = ANA / "q_intention_counts.csv"
FORCE_CNT_CSV   = ANA / "q_illocutionary_force_counts.csv"
STRATEGY_CSV    = ANA / "q_strategy_counts.csv"
POLYVOC_CSV     = ANA / "q_political_vocabulary_counts.csv"

PDF_PATH = OUT / "skinner_report.pdf"

# ── Colour palettes ──────────────────────────────────────────────────────────

INTENTION_COLORS = {
    "record":                   "#4E79A7",
    "commanding":               "#E15759",
    "persuading":               "#F28E2B",
    "justifying":               "#76B7B2",
    "narrative":                "#59A14F",
    "legitimation":             "#EDC948",
    "declaring":                "#B07AA1",
    "intervention":             "#FF9DA7",
    "questioning":              "#9C755F",
    "unclassified":             "#BAB0AC",
    "ideological_contestation": "#D37295",
    "mobilizing":               "#A0CBE8",
    "praising":                 "#FABFD2",
    "promising":                "#8CD17D",
    "warning":                  "#F1CE63",
    "condemning":               "#499894",
}

FORCE_COLORS = {
    "assertive":   "#4E79A7",
    "directive":   "#E15759",
    "commissive":  "#F28E2B",
    "expressive":  "#59A14F",
    "declarative": "#B07AA1",
    "unknown":     "#BAB0AC",
}

STRATEGY_COLORS = {
    "unclassified":          "#BAB0AC",
    "direct_address":        "#4E79A7",
    "appeal_to_authority":   "#E15759",
    "appeal_to_scripture":   "#F28E2B",
    "repetition":            "#76B7B2",
    "narrative_example":     "#59A14F",
    "appeal_to_tradition":   "#EDC948",
    "conditional_threat":    "#B07AA1",
    "rhetorical_question":   "#FF9DA7",
    "promise_of_reward":     "#9C755F",
    "contrast":              "#D37295",
}

# Convention colours — generated from tab20 + tab20b colormaps
def _make_conv_colors(keys):
    cmap1 = mcm.get_cmap("tab20")
    cmap2 = mcm.get_cmap("tab20b")
    result = {}
    for i, k in enumerate(keys):
        if i < 20:
            result[k] = matplotlib.colors.to_hex(cmap1(i))
        else:
            result[k] = matplotlib.colors.to_hex(cmap2(i - 20))
    return result

# ── ReportLab colour helpers ─────────────────────────────────────────────────

def rl_color(hex_str):
    h = hex_str.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return colors.Color(r / 255, g / 255, b / 255)

def light_tint(hex_str, mix=0.15):
    c = rl_color(hex_str)
    return colors.Color(c.red*mix + (1-mix), c.green*mix + (1-mix), c.blue*mix + (1-mix))

# ── Paragraph styles ─────────────────────────────────────────────────────────

_base = getSampleStyleSheet()

S_TITLE    = ParagraphStyle("STitle",   parent=_base["Normal"], fontName="DV-B",   fontSize=26, leading=32, textColor=colors.HexColor("#1a1a2e"), alignment=TA_CENTER, spaceAfter=6)
S_SUBTITLE = ParagraphStyle("SSubtit",  parent=_base["Normal"], fontName="DV",     fontSize=13, leading=18, textColor=colors.HexColor("#444466"), alignment=TA_CENTER, spaceAfter=4)
S_H1       = ParagraphStyle("SH1",      parent=_base["Normal"], fontName="DV-B",   fontSize=15, leading=20, textColor=colors.HexColor("#1a1a2e"), spaceBefore=12, spaceAfter=5)
S_H2       = ParagraphStyle("SH2",      parent=_base["Normal"], fontName="DV-B",   fontSize=11, leading=15, textColor=colors.HexColor("#333355"), spaceBefore=8, spaceAfter=4)
S_BODY     = ParagraphStyle("SBody",    parent=_base["Normal"], fontName="DV",     fontSize=9,  leading=13, textColor=colors.HexColor("#222222"))
S_SMALL    = ParagraphStyle("SSmall",   parent=_base["Normal"], fontName="DV",     fontSize=7.5,leading=11, textColor=colors.HexColor("#333333"))
S_SMALL_B  = ParagraphStyle("SSmallB",  parent=_base["Normal"], fontName="DV-B",   fontSize=7.5,leading=11, textColor=colors.HexColor("#333333"))
S_TINY     = ParagraphStyle("STiny",    parent=_base["Normal"], fontName="DV",     fontSize=6.5,leading=9,  textColor=colors.HexColor("#444444"))
S_CAPTION  = ParagraphStyle("SCaption", parent=_base["Normal"], fontName="DV-Ser", fontSize=8,  leading=11, textColor=colors.HexColor("#666666"), alignment=TA_CENTER, spaceAfter=6)
S_LEGEND   = ParagraphStyle("SLegend",  parent=_base["Normal"], fontName="DV",     fontSize=8.5,leading=12, textColor=colors.HexColor("#222222"))

# ── Label abbreviations ───────────────────────────────────────────────────────

SHORT_INTENTION = {
    "ideological_contestation": "ideo.cont.",
    "unclassified": "unclassif.",
}

SHORT_STRATEGY = {
    "unclassified":          "—",
    "direct_address":        "direct",
    "appeal_to_authority":   "auth.",
    "appeal_to_scripture":   "script.",
    "repetition":            "repet.",
    "narrative_example":     "narr.",
    "appeal_to_tradition":   "trad.",
    "conditional_threat":    "cond.thr.",
    "rhetorical_question":   "rhetor.q.",
    "promise_of_reward":     "promise",
    "contrast":              "contrast",
}

SHORT_CONVENTION = {
    "narrative_chronicle":            "narr.chron.",
    "apodictic_law":                  "apodictic",
    "deliberative_rhetoric":          "deliberat.",
    "theological_rationale":          "theol.rat.",
    "dialogic_controversy":           "dialogic",
    "elenctic_questioning":           "elenctic",
    "declarative_assertion":          "declar.",
    "enumerative_list":               "enum.",
    "theophanic_self_presentation":   "theoph.sp.",
    "royal_legitimation_formula":     "royal.leg.",
    "prophetic_admonition":           "proph.adm.",
    "antithetical_disputation":       "antithetic",
    "undetermined":                   "?",
    "theophanic_declaration":         "theoph.d.",
    "casuistic_law":                  "casuistic",
    "missionary_commission":          "mission.",
    "scriptural_warrant":             "script.w.",
    "universal_truth_claim":          "univ.truth",
    "attributive_praise":             "attr.pr.",
    "covenant_promise":               "cov.prom.",
}

def shorten(val, mapping, max_len=14):
    if not isinstance(val, str) or val in ("nan", ""):
        return "—"
    short = mapping.get(val, val)
    return short[:max_len] if len(short) > max_len else short

def flag_short(val):
    """Return brief anti-anachronism indicator."""
    if not isinstance(val, str) or val == "none_flagged":
        return "—"
    m = re.match(r'\s*(\w+)\s*:', val)
    return m.group(1) if m else "⚑"

# ── Figure helpers ────────────────────────────────────────────────────────────

def fig_to_image(fig, width_cm=15):
    fig_w, fig_h = fig.get_size_inches()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return Image(buf, width=width_cm*cm, height=width_cm*cm*(fig_h/fig_w))

def _hbar(ax, keys, vals, colors_dict, title, xlabel="Počet viet"):
    clrs = [colors_dict.get(k, "#aaaaaa") for k in keys]
    bars = ax.barh(keys, vals, color=clrs, height=0.65,
                   edgecolor="white", linewidth=0.5)
    for bar, v in zip(bars, vals):
        ax.text(v + max(vals)*0.01, bar.get_y() + bar.get_height()/2,
                f"{v:,}", va="center", ha="left", fontsize=7.5, color="#333333")
    ax.set_xlabel(xlabel, fontsize=8.5, color="#444444")
    ax.set_title(title, fontsize=11, fontweight="bold", color="#1a1a2e", pad=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=8)
    ax.tick_params(axis="x", labelsize=7.5, colors="#666666")
    ax.set_xlim(0, max(vals) * 1.2)
    ax.grid(axis="x", linestyle="--", linewidth=0.4, alpha=0.5, color="#cccccc")
    ax.set_facecolor("#f8f8fc")
    fig = ax.get_figure()
    fig.patch.set_facecolor("#f8f8fc")


def fig_bar_primary_intention(df_counts):
    df   = df_counts.sort_values("count", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    _hbar(ax, df["primary_intention"].tolist(), df["count"].tolist(),
          INTENTION_COLORS, "Distribúcia primárnych zámerov")
    fig.tight_layout()
    return fig


def fig_bar_secondary_intention(df_corpus):
    vc = df_corpus["secondary_intention"].dropna().value_counts().reset_index()
    vc.columns = ["secondary_intention", "count"]
    vc = vc.sort_values("count", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 3.8))
    _hbar(ax, vc["secondary_intention"].tolist(), vc["count"].tolist(),
          INTENTION_COLORS, "Distribúcia sekundárnych zámerov")
    fig.tight_layout()
    return fig


def fig_pie_force(df_force):
    labels = df_force["illocutionary_force"].tolist()
    vals   = df_force["count"].tolist()
    clrs   = [FORCE_COLORS.get(l, "#aaaaaa") for l in labels]
    fig, ax = plt.subplots(figsize=(7, 3.5))
    wedges, _, autotexts = ax.pie(
        vals, labels=None, colors=clrs, autopct="%1.1f%%",
        pctdistance=0.78, startangle=140,
        wedgeprops=dict(linewidth=1.2, edgecolor="white"),
    )
    for at in autotexts:
        at.set_fontsize(8.5); at.set_color("white"); at.set_fontweight("bold")
    ax.legend(wedges, [f"{l}  ({v:,})" for l, v in zip(labels, vals)],
              loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=9, frameon=False)
    ax.set_title("Ilokučná sila", fontsize=11, fontweight="bold", color="#1a1a2e", pad=8)
    fig.patch.set_facecolor("#f8f8fc")
    fig.tight_layout()
    return fig


def fig_bar_strategy(label, df_strategy, secondary_series=None):
    """primary or secondary strategy bar chart."""
    if secondary_series is not None:
        vc = secondary_series.dropna().value_counts().reset_index()
        vc.columns = ["strategy", "count"]
    else:
        vc = df_strategy.rename(columns={"primary_strategy": "strategy"})
    vc = vc.sort_values("count", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 3.5))
    _hbar(ax, vc["strategy"].tolist(), vc["count"].tolist(),
          STRATEGY_COLORS, label)
    fig.tight_layout()
    return fig


def fig_bar_conventions(df_corpus, top_n=20):
    vc = df_corpus["convention"].dropna().value_counts().head(top_n).reset_index()
    vc.columns = ["convention", "count"]
    vc = vc.sort_values("count", ascending=True)
    keys = vc["convention"].tolist()
    conv_colors = _make_conv_colors(
        df_corpus["convention"].dropna().value_counts().index.tolist()
    )
    clrs = [conv_colors.get(k, "#aaaaaa") for k in keys]
    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.barh(keys, vc["count"].tolist(), color=clrs,
                   height=0.65, edgecolor="white", linewidth=0.5)
    for bar, v in zip(bars, vc["count"].tolist()):
        ax.text(v + 80, bar.get_y() + bar.get_height()/2,
                f"{v:,}", va="center", ha="left", fontsize=7.5, color="#333333")
    ax.set_xlabel("Počet viet", fontsize=8.5, color="#444444")
    ax.set_title(f"Top {top_n} typov konvencie", fontsize=11,
                 fontweight="bold", color="#1a1a2e", pad=8)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=8)
    ax.tick_params(axis="x", labelsize=7.5, colors="#666666")
    ax.set_xlim(0, vc["count"].max() * 1.2)
    ax.grid(axis="x", linestyle="--", linewidth=0.4, alpha=0.5, color="#cccccc")
    ax.set_facecolor("#f8f8fc"); fig.patch.set_facecolor("#f8f8fc")
    fig.tight_layout()
    return fig, conv_colors


def fig_pie_anachronism(df_corpus):
    flagged   = (df_corpus["anti_anachronism"] != "none_flagged").sum()
    unflagged = len(df_corpus) - flagged
    vals   = [unflagged, flagged]
    labels = ["bez príznaku", "s príznakom"]
    clrs   = ["#76B7B2", "#E15759"]
    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    wedges, _, autotexts = ax.pie(
        vals, labels=None, colors=clrs, autopct="%1.1f%%",
        pctdistance=0.7, startangle=90,
        wedgeprops=dict(linewidth=1.2, edgecolor="white"),
    )
    for at in autotexts:
        at.set_fontsize(9); at.set_color("white"); at.set_fontweight("bold")
    ax.legend(wedges, [f"{l} ({v:,})" for l, v in zip(labels, vals)],
              loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=9, frameon=False)
    ax.set_title("Anti-anachronizmus", fontsize=11, fontweight="bold",
                 color="#1a1a2e", pad=6)
    fig.patch.set_facecolor("#f8f8fc")
    fig.tight_layout()
    return fig


def fig_bar_anachronism_terms(df_corpus):
    terms = []
    for val in df_corpus["anti_anachronism"].dropna():
        if val == "none_flagged":
            continue
        for chunk in str(val).split(";"):
            m = re.match(r'\s*(\w+)\s*:', chunk.strip())
            if m:
                terms.append(m.group(1).strip())
    ctr   = Counter(terms).most_common(12)
    keys  = [k for k, _ in reversed(ctr)]
    vals  = [v for _, v in reversed(ctr)]
    clrs  = ["#E15759"] * len(keys)
    fig, ax = plt.subplots(figsize=(8, 3.8))
    bars = ax.barh(keys, vals, color=clrs, height=0.65,
                   edgecolor="white", linewidth=0.5)
    for bar, v in zip(bars, vals):
        ax.text(v + 10, bar.get_y() + bar.get_height()/2,
                f"{v:,}", va="center", ha="left", fontsize=8, color="#333333")
    ax.set_xlabel("Výskyty príznaku", fontsize=8.5, color="#444444")
    ax.set_title("Top anachronické termíny", fontsize=11, fontweight="bold",
                 color="#1a1a2e", pad=8)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=9)
    ax.tick_params(axis="x", labelsize=8, colors="#666666")
    ax.set_xlim(0, max(vals) * 1.2)
    ax.grid(axis="x", linestyle="--", linewidth=0.4, alpha=0.5, color="#cccccc")
    ax.set_facecolor("#f8f8fc"); fig.patch.set_facecolor("#f8f8fc")
    fig.tight_layout()
    return fig


def fig_bar_polyvoc(df_polyvoc, top_n=15):
    df   = df_polyvoc.head(top_n).sort_values("count", ascending=True)
    keys = df["term"].tolist()
    vals = df["count"].tolist()
    fig, ax = plt.subplots(figsize=(10, 5))
    _hbar(ax, keys, vals, {k: "#4E79A7" for k in keys},
          f"Top {top_n} politických termínov", xlabel="Výskyty")
    fig.tight_layout()
    return fig


def fig_stacked_books(df_books):
    intent_cols = [c for c in INTENTION_COLORS if c in df_books.columns]
    books   = [p.replace("bible_BKR_", "").replace(".txt", "") for p in df_books["file_name"]]
    bottoms = [0] * len(df_books)
    fig, ax = plt.subplots(figsize=(13, 5))
    for col in intent_cols:
        vals = df_books[col].fillna(0).tolist()
        ax.bar(books, vals, bottom=bottoms, color=INTENTION_COLORS[col], label=col,
               edgecolor="white", linewidth=0.3)
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax.set_ylabel("Počet viet", fontsize=9, color="#444444")
    ax.set_title("Zámer podľa knihy", fontsize=12, fontweight="bold", color="#1a1a2e", pad=10)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(axis="y", linestyle="--", linewidth=0.4, alpha=0.5, color="#cccccc")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=7.5, frameon=False)
    ax.set_facecolor("#f8f8fc"); fig.patch.set_facecolor("#f8f8fc")
    fig.tight_layout()
    return fig


# ── Generic table builders ────────────────────────────────────────────────────

def _counts_table(df, key_col, count_col, total, colors_dict, key_label="Typ"):
    """Build a colour-coded 3-column counts table (Key | Count | %)."""
    header = [Paragraph(f"<b>{key_label}</b>", S_SMALL),
              Paragraph("<b>Počet</b>", S_SMALL),
              Paragraph("<b>%</b>", S_SMALL)]
    data = [header]
    sorted_df = df.sort_values(count_col, ascending=False)
    for _, r in sorted_df.iterrows():
        pct = r[count_col] / total * 100
        data.append([
            Paragraph(str(r[key_col]).replace("_", " ").title(), S_SMALL),
            Paragraph(f"{r[count_col]:,}", S_SMALL),
            Paragraph(f"{pct:.1f}%", S_SMALL),
        ])
    data.append([Paragraph("<b>CELKOM</b>", S_SMALL),
                 Paragraph(f"<b>{total:,}</b>", S_SMALL),
                 Paragraph("<b>100%</b>", S_SMALL)])

    tbl = Table(data, colWidths=[6*cm, 3*cm, 2.5*cm])
    style = [
        ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "DV-B"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ALIGN",         (1, 0), (-1, -1), "RIGHT"),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
        ("BACKGROUND",    (0, -1), (-1, -1), colors.HexColor("#ededf5")),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for i, (_, r) in enumerate(sorted_df.iterrows(), start=1):
        hex_c = colors_dict.get(str(r[key_col]), "#aaaaaa")
        style.append(("BACKGROUND", (0, i), (0, i), rl_color(hex_c)))
        style.append(("TEXTCOLOR",  (0, i), (0, i), colors.white))
        style.append(("BACKGROUND", (1, i), (-1, i), light_tint(hex_c)))
    tbl.setStyle(TableStyle(style))
    return tbl


def _counts_table_2col(df, key_col, count_col, total, colors_dict):
    """Two side-by-side colour-coded counts blocks in one table (saves vertical space)."""
    sorted_rows = df.sort_values(count_col, ascending=False).reset_index(drop=True)
    half = (len(sorted_rows) + 1) // 2
    left_rows  = sorted_rows.iloc[:half]
    right_rows = sorted_rows.iloc[half:]

    # Build paired rows: [swatch_l, label_l, cnt_l, pct_l, gap, swatch_r, label_r, cnt_r, pct_r]
    col_w = [0.4*cm, 4.2*cm, 1.6*cm, 1.3*cm,  0.3*cm,  0.4*cm, 4.2*cm, 1.6*cm, 1.3*cm]

    header = [
        Paragraph("<b>▌</b>", S_TINY),
        Paragraph("<b>Konvencia</b>", S_SMALL),
        Paragraph("<b>Počet</b>", S_SMALL),
        Paragraph("<b>%</b>", S_SMALL),
        Paragraph("", S_TINY),
        Paragraph("<b>▌</b>", S_TINY),
        Paragraph("<b>Konvencia</b>", S_SMALL),
        Paragraph("<b>Počet</b>", S_SMALL),
        Paragraph("<b>%</b>", S_SMALL),
    ]
    data = [header]

    for i in range(half):
        lr = left_rows.iloc[i]
        l_pct = lr[count_col] / total * 100
        if i < len(right_rows):
            rr = right_rows.iloc[i]
            r_pct = rr[count_col] / total * 100
            r_cells = [
                "",
                Paragraph(str(rr[key_col]).replace("_", " ").title(), S_SMALL),
                Paragraph(f"{rr[count_col]:,}", S_SMALL),
                Paragraph(f"{r_pct:.1f}%", S_SMALL),
            ]
        else:
            rr = None
            r_cells = ["", Paragraph("", S_SMALL), Paragraph("", S_SMALL), Paragraph("", S_SMALL)]

        data.append([
            "",
            Paragraph(str(lr[key_col]).replace("_", " ").title(), S_SMALL),
            Paragraph(f"{lr[count_col]:,}", S_SMALL),
            Paragraph(f"{l_pct:.1f}%", S_SMALL),
            "",
        ] + r_cells)

    tbl = Table(data, colWidths=col_w)
    style = [
        ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "DV-B"),
        ("FONTSIZE",      (0, 0), (-1, -1), 7.5),
        ("ALIGN",         (2, 0), (3, -1), "RIGHT"),
        ("ALIGN",         (7, 0), (8, -1), "RIGHT"),
        ("GRID",          (0, 0), (3, -1), 0.3, colors.HexColor("#dddddd")),
        ("GRID",          (5, 0), (8, -1), 0.3, colors.HexColor("#dddddd")),
        ("BACKGROUND",    (4, 0), (4, -1), colors.white),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 3),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
    ]
    for i, (_, lr) in enumerate(left_rows.iterrows(), start=1):
        hex_c = colors_dict.get(str(lr[key_col]), "#aaaaaa")
        style.append(("BACKGROUND", (0, i), (0, i), rl_color(hex_c)))
        style.append(("BACKGROUND", (1, i), (3, i), light_tint(hex_c, 0.12)))
    for i, (_, rr) in enumerate(right_rows.iterrows(), start=1):
        hex_c = colors_dict.get(str(rr[key_col]), "#aaaaaa")
        style.append(("BACKGROUND", (5, i), (5, i), rl_color(hex_c)))
        style.append(("BACKGROUND", (6, i), (8, i), light_tint(hex_c, 0.12)))

    tbl.setStyle(TableStyle(style))
    return tbl


# ── Extended sentence table ───────────────────────────────────────────────────
# Columns: Zámer | 2.zámer | Sila | Stratégia | Konvencia | Anti. | K. | Veta

SENT_COL_W = [2.5*cm, 2.2*cm, 1.8*cm, 2.0*cm, 2.5*cm, 1.1*cm, 0.9*cm, 4.8*cm]

def build_extended_sentence_table(df_corpus, n_per_intent=2):
    rows = []
    for intent in INTENTION_COLORS:
        subset = df_corpus[df_corpus["primary_intention"] == intent].head(n_per_intent)
        for _, row in subset.iterrows():
            rows.append({
                "intention":   intent,
                "sec_intent":  str(row.get("secondary_intention", "")) or "—",
                "force":       str(row.get("illocutionary_force", "")),
                "strategy":    str(row.get("primary_strategy", "")) or "—",
                "convention":  str(row.get("convention", "")) or "—",
                "anti":        flag_short(str(row.get("anti_anachronism", "none_flagged"))),
                "conf":        f"{row.get('confidence', 0):.2f}",
                "sentence":    str(row.get("sentence", ""))[:100],
            })

    if not rows:
        return None

    header_style = [
        Paragraph("<b>Zámer</b>",      S_TINY),
        Paragraph("<b>2. zámer</b>",   S_TINY),
        Paragraph("<b>Sila</b>",       S_TINY),
        Paragraph("<b>Stratégia</b>",  S_TINY),
        Paragraph("<b>Konvencia</b>",  S_TINY),
        Paragraph("<b>Anti.</b>",      S_TINY),
        Paragraph("<b>K.</b>",         S_TINY),
        Paragraph("<b>Veta (100 znakov)</b>", S_TINY),
    ]
    data = [header_style]
    for r in rows:
        data.append([
            Paragraph(shorten(r["intention"], SHORT_INTENTION),   S_TINY),
            Paragraph(shorten(r["sec_intent"], SHORT_INTENTION),  S_TINY),
            Paragraph(r["force"],                                  S_TINY),
            Paragraph(shorten(r["strategy"], SHORT_STRATEGY),     S_TINY),
            Paragraph(shorten(r["convention"], SHORT_CONVENTION),  S_TINY),
            Paragraph(r["anti"],                                   S_TINY),
            Paragraph(r["conf"],                                   S_TINY),
            Paragraph(r["sentence"],                               S_TINY),
        ])

    tbl = Table(data, colWidths=SENT_COL_W, repeatRows=1)
    style_cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "DV-B"),
        ("FONTSIZE",      (0, 0), (-1, 0), 7),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 2),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
    ]
    for i, r in enumerate(rows, start=1):
        hex_c = INTENTION_COLORS.get(r["intention"], "#eeeeee")
        style_cmds.append(("BACKGROUND", (0, i), (0, i), rl_color(hex_c)))
        style_cmds.append(("TEXTCOLOR",  (0, i), (0, i), colors.white))
        style_cmds.append(("FONTNAME",   (0, i), (0, i), "DV-B"))
        style_cmds.append(("BACKGROUND", (1, i), (-1, i), light_tint(hex_c, 0.10)))
        # highlight anti column red if flagged
        if r["anti"] != "—":
            style_cmds.append(("TEXTCOLOR", (5, i), (5, i), rl_color("#E15759")))
            style_cmds.append(("FONTNAME",  (5, i), (5, i), "DV-B"))

    tbl.setStyle(TableStyle(style_cmds))
    return tbl


# ── Anti-anachronism sample table ─────────────────────────────────────────────

def build_anachronism_examples(df_corpus, n=12):
    flagged = df_corpus[df_corpus["anti_anachronism"] != "none_flagged"].copy()
    flagged = flagged.sort_values("anti_anachronism").head(n)

    header = [Paragraph("<b>Kniha</b>", S_SMALL),
              Paragraph("<b>Zámer</b>", S_SMALL),
              Paragraph("<b>Príznak (anti-anachronizmus)</b>", S_SMALL),
              Paragraph("<b>Veta (skrátená)</b>", S_SMALL)]
    data = [header]
    for _, row in flagged.iterrows():
        intent = str(row.get("primary_intention", ""))
        data.append([
            Paragraph(str(row.get("file_name", "")).replace("bible_BKR_", "").replace(".txt", ""), S_SMALL),
            Paragraph(shorten(intent, SHORT_INTENTION), S_SMALL),
            Paragraph(str(row.get("anti_anachronism", ""))[:120], S_SMALL),
            Paragraph(str(row.get("sentence", ""))[:80], S_SMALL),
        ])

    tbl = Table(data, colWidths=[1.5*cm, 2.2*cm, 6.5*cm, 7.0*cm], repeatRows=1)
    style_cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "DV-B"),
        ("FONTSIZE",      (0, 0), (-1, -1), 7.5),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for i, (_, row) in enumerate(flagged.iterrows(), start=1):
        intent = str(row.get("primary_intention", ""))
        hex_c  = INTENTION_COLORS.get(intent, "#aaaaaa")
        style_cmds.append(("BACKGROUND", (1, i), (1, i), rl_color(hex_c)))
        style_cmds.append(("TEXTCOLOR",  (1, i), (1, i), colors.white))
        bg_warn = light_tint("#E15759", 0.12)
        style_cmds.append(("BACKGROUND", (2, i), (2, i), bg_warn))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


# ── Cover legend ─────────────────────────────────────────────────────────────

def build_legend_table():
    items = list(INTENTION_COLORS.items())
    half  = (len(items) + 1) // 2
    left, right = items[:half], items[half:]
    rows = []
    for i in range(half):
        l_intent, _ = left[i]
        r_intent = right[i][0] if i < len(right) else ""
        rows.append([
            "", Paragraph(l_intent.replace("_", " ").title(), S_LEGEND),
            "", Paragraph(r_intent.replace("_", " ").title(), S_LEGEND) if r_intent else Paragraph("", S_LEGEND),
        ])
    tbl = Table(rows, colWidths=[0.55*cm, 7.5*cm, 0.55*cm, 7.5*cm], rowHeights=0.6*cm)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",   (0, 0), (-1, -1), 0, colors.white),
        ("LEFTPADDING",  (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]
    for i in range(half):
        style.append(("BACKGROUND", (0, i), (0, i), rl_color(left[i][1])))
        if i < len(right) and right[i][0]:
            style.append(("BACKGROUND", (2, i), (2, i), rl_color(right[i][1])))
    tbl.setStyle(TableStyle(style))
    return tbl


# ── Page template ─────────────────────────────────────────────────────────────

PAGE_W, PAGE_H = A4
MARGIN = 2.0 * cm


def make_doc(path):
    doc = BaseDocTemplate(
        str(path), pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )
    frame = Frame(MARGIN, MARGIN, PAGE_W - 2*MARGIN, PAGE_H - 2*MARGIN, id="main")

    def _hf(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#ccccdd"))
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, PAGE_H - 1.3*cm, PAGE_W - MARGIN, PAGE_H - 1.3*cm)
        canvas.setFont("DV", 7)
        canvas.setFillColor(colors.HexColor("#888888"))
        canvas.drawRightString(PAGE_W - MARGIN, 0.8*cm, f"Strana {doc.page}")
        canvas.restoreState()

    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=_hf)])
    return doc


def hr():
    return HRFlowable(width="100%", thickness=0.8,
                      color=colors.HexColor("#ccccdd"), spaceAfter=8)


# ── Main ──────────────────────────────────────────────────────────────────────

def build_report():
    df_corpus = pd.read_csv(CORPUS_CSV)    if CORPUS_CSV.exists()     else pd.DataFrame()
    df_books  = pd.read_csv(BY_BOOK_CSV)   if BY_BOOK_CSV.exists()    else pd.DataFrame()
    df_counts = pd.read_csv(INTENT_CNT_CSV) if INTENT_CNT_CSV.exists() else pd.DataFrame()
    df_force  = pd.read_csv(FORCE_CNT_CSV)  if FORCE_CNT_CSV.exists()  else pd.DataFrame()
    df_strat  = pd.read_csv(STRATEGY_CSV)   if STRATEGY_CSV.exists()   else pd.DataFrame()
    df_polyvoc= pd.read_csv(POLYVOC_CSV)    if POLYVOC_CSV.exists()    else pd.DataFrame()

    if df_force.empty and not df_corpus.empty:
        fc = df_corpus["illocutionary_force"].value_counts().reset_index()
        fc.columns = ["illocutionary_force", "count"]
        df_force = fc

    story = []

    # ── Cover ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 2.2*cm))
    story.append(Paragraph("Skinner Pipeline", S_TITLE))
    story.append(Paragraph("Ilokučná analýza Králickej Biblie (BKR)", S_SUBTITLE))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="80%", thickness=2, color=colors.HexColor("#4E79A7"),
                             spaceAfter=12, spaceBefore=4))
    if not df_corpus.empty:
        story.append(Paragraph(
            f"Celkový korpus: <b>{len(df_corpus):,} viet</b> z <b>{df_corpus['file_name'].nunique()} kníh</b>",
            S_SUBTITLE))
    story.append(Spacer(1, 1.0*cm))
    story.append(Paragraph("Farebná legenda zámerov", S_H2))
    story.append(Spacer(1, 0.2*cm))
    story.append(build_legend_table())

    # ── Sec 1: Primary intention ──────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("1. Primárny zámer", S_H1)); story.append(hr())
    if not df_counts.empty:
        story.append(fig_to_image(fig_bar_primary_intention(df_counts), 16))
        story.append(Paragraph("Obr. 1 — Počet viet podľa primárneho zámeru.", S_CAPTION))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph("Tabuľka 1 — Prehľad primárnych zámerov", S_H2))
        total_n = df_counts["count"].sum()
        story.append(_counts_table(df_counts, "primary_intention", "count",
                                   total_n, INTENTION_COLORS, "Zámer"))

    # ── Sec 2+3: Force + Secondary intention (one page) ──────────────────────
    story.append(PageBreak())
    story.append(Paragraph("2. Ilokučná sila", S_H1)); story.append(hr())
    if not df_force.empty:
        story.append(fig_to_image(fig_pie_force(df_force), 11))
        story.append(Paragraph("Obr. 2 — Rozdelenie ilokučnej sily.", S_CAPTION))

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("3. Sekundárny zámer", S_H1)); story.append(hr())
    if not df_corpus.empty:
        story.append(fig_to_image(fig_bar_secondary_intention(df_corpus), 15))
        story.append(Paragraph("Obr. 3 — Počet viet podľa sekundárneho zámeru.", S_CAPTION))

    # ── Sec 4: Primary strategy (new page) ───────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("4. Primárna stratégia", S_H1)); story.append(hr())
    if not df_strat.empty:
        story.append(fig_to_image(
            fig_bar_strategy("Distribúcia primárnej stratégie", df_strat), 15))
        story.append(Paragraph("Obr. 4 — Počet viet podľa primárnej stratégie.", S_CAPTION))
        total_strat = df_strat["count"].sum()
        story.append(Paragraph("Tabuľka 3 — Primárna stratégia", S_H2))
        story.append(_counts_table(df_strat, "primary_strategy", "count",
                                   total_strat, STRATEGY_COLORS, "Stratégia"))

    # ── Sec 5: Secondary strategy (continues same page if space, else next) ──
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("5. Sekundárna stratégia", S_H1)); story.append(hr())
    if not df_corpus.empty and "secondary_strategy" in df_corpus.columns:
        story.append(fig_to_image(
            fig_bar_strategy("Distribúcia sekundárnej stratégie", None,
                             df_corpus["secondary_strategy"]), 15))
        story.append(Paragraph("Obr. 5 — Počet viet podľa sekundárnej stratégie.", S_CAPTION))

    # ── Sec 6: Convention types ───────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("6. Typy konvencie", S_H1)); story.append(hr())
    if not df_corpus.empty and "convention" in df_corpus.columns:
        fig_conv, conv_colors = fig_bar_conventions(df_corpus, top_n=20)
        story.append(fig_to_image(fig_conv, 16))
        story.append(Paragraph("Obr. 6 — Top 20 typov rétorickej konvencie.", S_CAPTION))

        # Convention table — 2-column layout to halve vertical space
        vc = df_corpus["convention"].dropna().value_counts().reset_index()
        vc.columns = ["convention", "count"]
        total_conv = vc["count"].sum()
        story.append(Paragraph("Tabuľka 4 — Všetky typy konvencie", S_H2))
        story.append(_counts_table_2col(vc, "convention", "count",
                                        total_conv, conv_colors))

    # ── Sec 7: Anti-anachronism ───────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("7. Anti-anachronizmus", S_H1)); story.append(hr())
    story.append(Paragraph(
        "Pipeline označuje termíny, ktoré môžu mať v kontexte BKR moderný sémantický nádych. "
        "Celkovo bolo identifikovaných 9 problematických termínov.", S_BODY))
    story.append(Spacer(1, 0.3*cm))
    if not df_corpus.empty and "anti_anachronism" in df_corpus.columns:
        story.append(fig_to_image(fig_pie_anachronism(df_corpus), 10))
        story.append(Paragraph("Obr. 7 — Podiel viet s anachronickým príznakom.", S_CAPTION))
        story.append(fig_to_image(fig_bar_anachronism_terms(df_corpus), 13))
        story.append(Paragraph("Obr. 8 — Frekvencie anachronických termínov.", S_CAPTION))
        story.append(Spacer(1, 0.4*cm))
        story.append(Paragraph("Tabuľka 5 — Vzorka viet s príznakom anachronizmu", S_H2))
        story.append(build_anachronism_examples(df_corpus, n=12))

    # ── Sec 8: Political vocabulary ───────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("8. Politická slovná zásoba", S_H1)); story.append(hr())
    if not df_polyvoc.empty:
        story.append(fig_to_image(fig_bar_polyvoc(df_polyvoc, top_n=15), 15))
        story.append(Paragraph(
            "Obr. 9 — Top 15 politických termínov detekovaných v korpuse.", S_CAPTION))

    # ── Sec 9: By book ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("9. Zámer podľa knihy", S_H1)); story.append(hr())
    if not df_books.empty:
        story.append(fig_to_image(fig_stacked_books(df_books), 16))
        story.append(Paragraph(
            "Obr. 10 — Kumulatívny počet zámerov podľa biblickej knihy ([:10] korpus).",
            S_CAPTION))

    # ── Sec 10: Extended sentence table ──────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("10. Rozšírená vzorka viet", S_H1)); story.append(hr())
    story.append(Paragraph(
        "Pre každý zámer sú zobrazené 2 vzorové vety so všetkými kľúčovými stĺpcami. "
        "<b>Anti.</b> = skratka anachronického termínu, — = bez príznaku.", S_BODY))
    story.append(Spacer(1, 0.25*cm))
    if not df_corpus.empty:
        tbl = build_extended_sentence_table(df_corpus, n_per_intent=2)
        if tbl:
            story.append(tbl)
            story.append(Paragraph(
                "Tab. 6 — 2 vzorové vety na zámer: Zámer | 2.zámer | Sila | Stratégia | Konvencia | Anti. | K. | Veta",
                S_CAPTION))

    doc = make_doc(PDF_PATH)
    doc.build(story)
    print(f"PDF uložený: {PDF_PATH}")


if __name__ == "__main__":
    build_report()
