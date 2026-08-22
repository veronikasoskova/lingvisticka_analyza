"""
genre_maps.py — authoritative biblical genre map, keyed by BKR filename.

Single source of truth replacing:
  - m_verbal_relations.BOOK_GENRES  (abbrev keys — many didn't match corpus filenames)
  - x_style_authorship._GENRE_MAP   (file keys, coarser granularity)
  - v_eval_pipeline.GENRE_MAP       (file keys, fine granularity — used as canonical here)

Genre granularity: fine (v_eval_pipeline schema).
For m_verbal_relations._GENRE_ADJ compatibility use detect_book_genre(fname, coarse=True).

Resolved literary-genre decisions (canon groups in the UI stay separate):
  Pl  (Lamentations)  : lyrical_poetry     (lament; not prophetic)
  Pis (Song of Songs) : lyrical_poetry     (love lyric; not wisdom)
  Sk  (Acts)          : narrative_acts     (coarse: historical; not gospel)
  Zj  (Revelation)    : apocalyptic        (coarse: prophetic)
  Gn/Ex/Nu            : narrative_pentateuch
  Lv                  : law_levitical
  Dt                  : law_deuteronomic
  Z   (Psalms)        : wisdom_psalms      (coarse: psalm)
"""

from __future__ import annotations

from pathlib import Path

# ── Canonical map (file-keyed, fine granularity) ─────────────────────────────

BOOK_GENRES: dict[str, str] = {
    "bible_BKR_Gn.txt":   "narrative_pentateuch",
    "bible_BKR_Ex.txt":   "narrative_pentateuch",
    "bible_BKR_Lv.txt":   "law_levitical",
    "bible_BKR_Nu.txt":   "narrative_pentateuch",
    "bible_BKR_Dt.txt":   "law_deuteronomic",
    "bible_BKR_Joz.txt":  "narrative_historical",
    "bible_BKR_Sd.txt":   "narrative_historical",
    "bible_BKR_Rt.txt":   "narrative_historical",
    "bible_BKR_1S.txt":   "narrative_historical",
    "bible_BKR_2S.txt":   "narrative_historical",
    "bible_BKR_1Kr.txt":  "narrative_historical",
    "bible_BKR_2Kr.txt":  "narrative_historical",
    "bible_BKR_1Pa.txt":  "narrative_historical",
    "bible_BKR_2Pa.txt":  "narrative_historical",
    "bible_BKR_Ezd.txt":  "narrative_historical",
    "bible_BKR_Neh.txt":  "narrative_historical",
    "bible_BKR_Est.txt":  "narrative_historical",
    "bible_BKR_Jb.txt":   "wisdom_poetry",
    "bible_BKR_Z.txt":    "wisdom_psalms",
    "bible_BKR_Pr.txt":   "wisdom_poetry",
    "bible_BKR_Kaz.txt":  "wisdom_poetry",
    "bible_BKR_Pis.txt":  "lyrical_poetry",   # Song of Songs — love lyric, not wisdom
    "bible_BKR_Iz.txt":   "prophetic_major",
    "bible_BKR_Jr.txt":   "prophetic_major",
    "bible_BKR_Pl.txt":   "lyrical_poetry",    # Lamentations — lament (coarse: lyrical)
    "bible_BKR_Ez.txt":   "prophetic_major",
    "bible_BKR_Da.txt":   "prophetic_major",
    "bible_BKR_Oz.txt":   "prophetic_minor",
    "bible_BKR_Jl.txt":   "prophetic_minor",
    "bible_BKR_Am.txt":   "prophetic_minor",
    "bible_BKR_Abd.txt":  "prophetic_minor",
    "bible_BKR_Jon.txt":  "prophetic_minor",
    "bible_BKR_Mi.txt":   "prophetic_minor",
    "bible_BKR_Na.txt":   "prophetic_minor",
    "bible_BKR_Abk.txt":  "prophetic_minor",
    "bible_BKR_Sf.txt":   "prophetic_minor",
    "bible_BKR_Ag.txt":   "prophetic_minor",
    "bible_BKR_Za.txt":   "prophetic_minor",
    "bible_BKR_Mal.txt":  "prophetic_minor",
    "bible_BKR_Mt.txt":   "gospel_synoptic",
    "bible_BKR_Mk.txt":   "gospel_synoptic",
    "bible_BKR_L.txt":    "gospel_synoptic",
    "bible_BKR_J.txt":    "gospel_johannine",
    "bible_BKR_Sk.txt":   "narrative_acts",    # Acts — narrative (coarse: historical)
    "bible_BKR_R.txt":    "epistle_pauline",
    "bible_BKR_1K.txt":   "epistle_pauline",
    "bible_BKR_2K.txt":   "epistle_pauline",
    "bible_BKR_Ga.txt":   "epistle_pauline",
    "bible_BKR_Ef.txt":   "epistle_pauline",
    "bible_BKR_Fp.txt":   "epistle_pauline",
    "bible_BKR_Ko.txt":   "epistle_pauline",
    "bible_BKR_1Te.txt":  "epistle_pauline",
    "bible_BKR_2Te.txt":  "epistle_pauline",
    "bible_BKR_1Tm.txt":  "epistle_pastoral",
    "bible_BKR_2Tm.txt":  "epistle_pastoral",
    "bible_BKR_Tit.txt":  "epistle_pastoral",
    "bible_BKR_Fm.txt":   "epistle_pauline",
    "bible_BKR_Zd.txt":   "epistle_general",
    "bible_BKR_Jk.txt":   "epistle_general",
    "bible_BKR_1P.txt":   "epistle_general",
    "bible_BKR_2P.txt":   "epistle_general",
    "bible_BKR_1J.txt":   "epistle_johannine",
    "bible_BKR_2J.txt":   "epistle_johannine",
    "bible_BKR_3J.txt":   "epistle_johannine",
    "bible_BKR_Ju.txt":   "epistle_general",
    "bible_BKR_Zj.txt":   "apocalyptic",       # Revelation — coarse: prophetic
}

# Legacy abbrev keys from the old m_verbal_relations map that did not match
# corpus filenames (Ž≠Z, Př≠Pr, …).  detect_book_genre() accepts these too.
_ABBREV_ALIASES: dict[str, str] = {
    "Ž": "Z",
    "Př": "Pr",
    "Pís": "Pis",
    "Rl": "R",
    "Jz": "Joz",
    "Ab": "Abk",   # Habakkuk (Obadiah is Abd)
    "Jn": "Jon",   # Jonah (John is J)
    "Ml": "Mal",
    "Dn": "Da",
    "Tt": "Tit",
}

# ── Coarse mapping for m_verbal_relations._GENRE_ADJ compatibility ───────────
# _GENRE_ADJ keys: psalm, wisdom, prophetic, epistle, gospel, historical,
#   lyrical, law
FINE_TO_COARSE: dict[str, str] = {
    "narrative_pentateuch": "historical",
    "narrative_historical": "historical",
    "narrative_acts":       "historical",
    "wisdom_poetry":        "wisdom",
    "wisdom_psalms":        "psalm",
    "lyrical_poetry":       "lyrical",
    "prophetic_major":      "prophetic",
    "prophetic_minor":      "prophetic",
    "gospel_synoptic":      "gospel",
    "gospel_johannine":     "gospel",
    "epistle_pauline":      "epistle",
    "epistle_pastoral":     "epistle",
    "epistle_general":      "epistle",
    "epistle_johannine":    "epistle",
    "apocalyptic":          "prophetic",
    "law_levitical":        "law",
    "law_deuteronomic":     "law",
}

# Keep the private alias so existing imports of the name still work in-module.
_FINE_TO_COARSE = FINE_TO_COARSE

FINE_GENRES = frozenset(FINE_TO_COARSE)
COARSE_GENRES = frozenset(FINE_TO_COARSE.values())

# CS / SK / EN labels for the Streamlit UI (fine + coarse + unknown).
GENRE_LABELS: dict[str, dict[str, str]] = {
    "cs": {
        "narrative_pentateuch": "Pentateuch (narativ)",
        "narrative_historical": "Historický narativ",
        "narrative_acts": "Skutky (narativ)",
        "law_levitical": "Levitický zákon",
        "law_deuteronomic": "Deuteronomický zákon",
        "wisdom_poetry": "Mudroslovná poezie",
        "wisdom_psalms": "Žalmy",
        "lyrical_poetry": "Lyrická poezie",
        "prophetic_major": "Velcí proroci",
        "prophetic_minor": "Malí proroci",
        "gospel_synoptic": "Synoptická evangelia",
        "gospel_johannine": "Janovo evangelium",
        "epistle_pauline": "Pavlovské listy",
        "epistle_pastoral": "Pastorální listy",
        "epistle_general": "Obecné listy",
        "epistle_johannine": "Janovy listy",
        "apocalyptic": "Apokalyptika",
        "historical": "Historický",
        "law": "Zákon",
        "wisdom": "Mudrosloví",
        "psalm": "Žalm",
        "lyrical": "Lyrický",
        "prophetic": "Prorocký",
        "gospel": "Evangelium",
        "epistle": "List",
        "unknown": "Neznámý",
    },
    "sk": {
        "narrative_pentateuch": "Pentateuch (naratív)",
        "narrative_historical": "Historický naratív",
        "narrative_acts": "Skutky (naratív)",
        "law_levitical": "Levitický zákon",
        "law_deuteronomic": "Deuteronomický zákon",
        "wisdom_poetry": "Mudroslovná poézia",
        "wisdom_psalms": "Žalmy",
        "lyrical_poetry": "Lyrická poézia",
        "prophetic_major": "Veľkí proroci",
        "prophetic_minor": "Malí proroci",
        "gospel_synoptic": "Synoptické evanjeliá",
        "gospel_johannine": "Jánovo evanjelium",
        "epistle_pauline": "Pavlovské listy",
        "epistle_pastoral": "Pastorálne listy",
        "epistle_general": "Všeobecné listy",
        "epistle_johannine": "Jánove listy",
        "apocalyptic": "Apokalyptika",
        "historical": "Historický",
        "law": "Zákon",
        "wisdom": "Mudroslovie",
        "psalm": "Žalm",
        "lyrical": "Lyrický",
        "prophetic": "Prorocký",
        "gospel": "Evanjelium",
        "epistle": "List",
        "unknown": "Neznámy",
    },
    "en": {
        "narrative_pentateuch": "Pentateuch narrative",
        "narrative_historical": "Historical narrative",
        "narrative_acts": "Acts (narrative)",
        "law_levitical": "Levitical law",
        "law_deuteronomic": "Deuteronomic law",
        "wisdom_poetry": "Wisdom poetry",
        "wisdom_psalms": "Psalms",
        "lyrical_poetry": "Lyrical poetry",
        "prophetic_major": "Major prophets",
        "prophetic_minor": "Minor prophets",
        "gospel_synoptic": "Synoptic gospels",
        "gospel_johannine": "Johannine gospel",
        "epistle_pauline": "Pauline epistles",
        "epistle_pastoral": "Pastoral epistles",
        "epistle_general": "General epistles",
        "epistle_johannine": "Johannine epistles",
        "apocalyptic": "Apocalyptic",
        "historical": "Historical",
        "law": "Law",
        "wisdom": "Wisdom",
        "psalm": "Psalm",
        "lyrical": "Lyrical",
        "prophetic": "Prophetic",
        "gospel": "Gospel",
        "epistle": "Epistle",
        "unknown": "Unknown",
    },
}


def canonical_bkr_filename(file_name: str | Path | None) -> str:
    """Normalize a path, stem, abbreviation, or legacy alias to ``bible_BKR_*.txt``.

    Returns ``""`` when *file_name* is empty.  The result is not required to
    exist in ``BOOK_GENRES`` — callers that need a mapped key should look it up.
    """
    if file_name is None:
        return ""
    name = Path(str(file_name)).name.strip()
    if not name:
        return ""
    if name in BOOK_GENRES:
        return name
    stem = name
    if stem.lower().startswith("bible_bkr_"):
        stem = stem[len("bible_BKR_"):]
    if stem.endswith(".txt"):
        stem = stem[:-4]
    stem = _ABBREV_ALIASES.get(stem, stem)
    if not stem:
        return name
    return f"bible_BKR_{stem}.txt"


def detect_book_genre(file_name: str | Path | None, coarse: bool = False) -> str:
    """
    Return genre for a BKR file name (e.g. 'bible_BKR_Abd.txt'), a Path,
    a stem, or a short abbreviation ('Gn', 'Z', legacy 'Ž').
    coarse=True returns m_verbal_relations._GENRE_ADJ-compatible coarse genre.
    """
    key = canonical_bkr_filename(file_name)
    genre = BOOK_GENRES.get(key, "unknown")
    if coarse:
        return FINE_TO_COARSE.get(genre, genre)
    return genre
