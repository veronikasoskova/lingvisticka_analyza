"""
genre_maps.py — authoritative biblical genre map, keyed by BKR filename.

Single source of truth replacing:
  - m_verbal_relations.BOOK_GENRES  (abbrev keys — many didn't match corpus filenames)
  - x_style_authorship._GENRE_MAP   (file keys, coarser granularity)
  - v_eval_pipeline.GENRE_MAP       (file keys, fine granularity — used as canonical here)

Genre granularity: fine (v_eval_pipeline schema).
For m_verbal_relations._GENRE_ADJ compatibility use detect_book_genre(fname, coarse=True).

REPORTED CONFLICTS between the three original maps (do not resolve here — awaiting decision):
  Pl  (Lamentations)   : m_verbal=lyrical      | x_style=prophetic    | v_eval=prophetic_major
  Pis (Song of Songs)  : m_verbal key "Pís"≠Pis| x_style=wisdom       | v_eval=wisdom_poetry
  Sk  (Acts)           : m_verbal=gospel        | x_style=acts         | v_eval=narrative_acts
  Zj  (Revelation)     : m_verbal=prophetic     | x_style=apocalyptic  | v_eval=apocalyptic
  Gn/Ex/Nu (Pentateuch): m_verbal=historical    | x_style=pentateuch   | v_eval=narrative_pentateuch
  Dt  (Deuteronomy)    : m_verbal=historical    | x_style=law          | v_eval=law_deuteronomic
  Lv  (Leviticus)      : m_verbal=historical    | x_style=law          | v_eval=law_levitical
  Z   (Psalms)         : m_verbal key "Ž"≠Z     | x_style=psalms       | v_eval=wisdom_psalms
  Pr  (Proverbs)       : m_verbal key "Př"≠Pr   | x_style=wisdom       | v_eval=wisdom_poetry
  Abk (Habakkuk)       : m_verbal key "Ab"≠Abk  | x_style=prophetic    | v_eval=prophetic_minor
  Jon (Jonah)          : m_verbal key "Jn"≠Jon  | x_style=prophetic    | v_eval=prophetic_minor
  Mal (Malachi)        : m_verbal key "Ml"≠Mal  | x_style=prophetic    | v_eval=prophetic_minor
  Da  (Daniel)         : m_verbal key "Dn"≠Da   | x_style=prophetic    | v_eval=prophetic_major
  R   (Romans)         : m_verbal key "Rl"≠R    | x_style=epistle      | v_eval=epistle_pauline
  Tit (Titus)          : m_verbal key "Tt"≠Tit  | x_style=epistle      | v_eval=epistle_pastoral
  Joz (Joshua)         : m_verbal key "Jz"≠Joz  | x_style=historical   | v_eval=narrative_historical
"""

from __future__ import annotations

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
    "bible_BKR_Pis.txt":  "wisdom_poetry",
    "bible_BKR_Iz.txt":   "prophetic_major",
    "bible_BKR_Jr.txt":   "prophetic_major",
    "bible_BKR_Pl.txt":   "lyrical_poetry",    # Lamentations — lyrical/lament (coarse: lyrical)
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
    "bible_BKR_Sk.txt":   "narrative_acts",    # Acts — narrative_historical category (coarse: historical)
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
    "bible_BKR_Zj.txt":   "apocalyptic",       # Revelation — coarse: prophetic (authorized)
}

# ── Coarse mapping for m_verbal_relations._GENRE_ADJ compatibility ───────────
# _GENRE_ADJ keys (all valid coarse targets): psalm, wisdom, prophetic,
#   epistle, gospel, historical, lyrical
# MISSING from _GENRE_ADJ: "law" — see PENDING entries below.
_FINE_TO_COARSE: dict[str, str] = {
    "narrative_pentateuch": "historical",   # authorized
    "narrative_historical": "historical",
    "narrative_acts":       "historical",   # authorized (was gospel — fixed)
    "wisdom_poetry":        "wisdom",
    "wisdom_psalms":        "psalm",
    "lyrical_poetry":       "lyrical",      # Pl (Lamentations) — authorized
    "prophetic_major":      "prophetic",
    "prophetic_minor":      "prophetic",
    "gospel_synoptic":      "gospel",
    "gospel_johannine":     "gospel",
    "epistle_pauline":      "epistle",
    "epistle_pastoral":     "epistle",
    "epistle_general":      "epistle",
    "epistle_johannine":    "epistle",
    "apocalyptic":          "prophetic",    # authorized
    "law_levitical":        "law",
    "law_deuteronomic":     "law",
}


def detect_book_genre(file_name: str, coarse: bool = False) -> str:
    """
    Return genre for a BKR file name (e.g. 'bible_BKR_Abd.txt').
    coarse=True returns m_verbal_relations._GENRE_ADJ-compatible coarse genre.
    """
    genre = BOOK_GENRES.get(file_name, "unknown")
    if coarse:
        return _FINE_TO_COARSE.get(genre, genre)
    return genre
