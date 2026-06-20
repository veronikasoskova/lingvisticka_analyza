from dataclasses import dataclass, asdict
from typing import List
from pathlib import Path
import csv

from c_input import TextInput, create_input_from_text
from d_preprocessing import preprocess_text
from e_extraction import extract_features
from f_semantics import semantic_enrichment
import g_skinner_rules as rules
from t_config_tradition import THEOLOGICAL_LEMMAS, MORAL_LEMMAS


# ==========================================================
# LEXIKÓNY
# ==========================================================

# ── Existing (unchanged) ────────────────────────────────────────────────────

SOCIAL_LEMMAS = frozenset({
    "král", "otec", "syn", "lid", "bratr",
    "žena", "muž", "služebník", "kněz", "prorok",
    "starší", "národ", "rodina", "soudce",
})

ATTRIBUTE_LEMMAS = frozenset({
    "veliký", "malý", "silný", "slabý",
    "krásný", "moudrý", "mocný", "věrný",
    "milosrdný", "spravedlivý", "svatý",
})

# ── New granular lexicons ────────────────────────────────────────────────────

# Legal / normative — law, commandments, covenant obligations
# Checked HIGH priority — these are distinctive even when hospodin appears
LEGAL_NORMATIVE_LEMMAS = frozenset({
    "zákon", "přikázání", "ustanovení", "nařízení", "statut",
    "smlouva", "svědectví", "předpis", "právo",
    "soudce", "rozsudek", "vina", "trest",
    "přestoupit", "zachovávat", "plnit", "poslouchat",
    "povinnost", "dluh", "dlužen",
})

# Ritual / liturgical — sacrificial, priestly, temple vocabulary
RITUAL_LITURGICAL_LEMMAS = frozenset({
    "oběť", "oltář", "kněz", "beránek", "krev",
    "posvětit", "zasvětit", "chrám", "kozel", "volek",
    "zápalný", "kadidlo", "roucho", "efod",
    "náprsník", "velekněz", "svatyně", "kadidlnice",
    "olej", "tuk", "skopec", "čerevec",
})

# Prophetic announcement — distinctive prophetic speech-formula lemmas
# NOTE: "hospodinovo" (possessive adj. of hospodin) is the most diagnostic
PROPHETIC_ANNOUNCE_LEMMAS = frozenset({
    "hospodinovo",   # "slovo Hospodinovo" — specific genitive construction
    "proroctví",
    "ohlásit",
    "výrok",
})

# Creation narrative — cosmogonic / primordial-act language
CREATION_NARRATIVE_LEMMAS = frozenset({
    "stvořit", "počátek", "dílo",
    "prázdnota", "tvar", "hlubina",
    # "nebe", "země" too common — only included via compound check below
})

# Wisdom maxim — proverbs, comparative sentences, aphorisms
WISDOM_MAXIM_LEMMAS = frozenset({
    "přísloví", "naučení", "poučení",
    "lepší", "lépe",          # better-than comparison
    "moudrý", "moudrost",
    "blázen", "bláznovství",
    "srdce", "ústa", "jazyk",  # wisdom body metaphors
})

# Genealogical record — lineage / genealogy
GENEALOGICAL_RECORD_LEMMAS = frozenset({
    "zplodit", "narodit", "pocházet", "porodit", "zrodit",
    "prvorozený", "potomek", "rodokmen", "pokolení",
})

# Eschatological — end-times, judgment, resurrection
# Use RARE/SPECIFIC terms only to avoid bias
ESCHATOLOGICAL_LEMMAS_P = frozenset({
    "vzkříšení", "vzkřísit",
    "skonání", "věčnost",
    "peklo", "záhubka",
    "posledního",  # "dne posledního" gen.
})


# ==========================================================
# HELPER — prophetic formula detection
# ==========================================================

def _is_prophetic_formula(feature, lemma_set: frozenset) -> bool:
    """
    Detect the prophetic speech-formula "praví Hospodin" and related forms.

    A single "praví" is too broad (it also means "he says" in narrative).
    Require either:
    - "praví" + divine name/possessive, OR
    - root_lemma is a prophetic noun
    """
    # "praví Hospodin" — Stanza cs-pdt lemmatizes "praví" (3sg pres.) → "pravit"
    if "pravit" in lemma_set and (
        "hospodin" in lemma_set
        or "hospodinův" in lemma_set
        or "hospodinovo" in lemma_set
    ):
        return True
    if feature.root_lemma and feature.root_lemma in {"proroctví", "vidění"}:
        return True
    return bool(lemma_set & PROPHETIC_ANNOUNCE_LEMMAS)


def _is_creation_sentence(feature, lemma_set: frozenset) -> bool:
    """
    "Bůh stvořil nebe a zemi" — creation verb is the primary signal.
    Also catches "na počátku" contexts.
    """
    if "stvořit" in lemma_set:
        return True
    if "počátek" in lemma_set and (
        "nebe" in lemma_set or "země" in lemma_set or "světlo" in lemma_set
    ):
        return True
    return bool(lemma_set & CREATION_NARRATIVE_LEMMAS)


# ==========================================================
# OUTPUT DATACLASS
# ==========================================================

@dataclass
class RefinedDescription:

    sentence_id: int
    sentence: str

    description_type: str
    confidence: float
    explanation: str

    root_lemma: str
    semantic_cluster: str
    lemmas: str
    dep_tree: str


# ==========================================================
# CORE CLASSIFIER
# ==========================================================

def refine_description(
    feature,
    semantic
) -> RefinedDescription:
    """
    Assign a granular description_type label to a sentence.

    Priority hierarchy — rationale
    --------------------------------
    Categories are ordered from most specific / least ambiguous to most
    general, with the key bias fix being that "theological_statement" is
    DEMOTED to near-last position and requires a stronger signal.

    Problem solved: THEOLOGICAL_LEMMAS contains "hospodin" and "bůh" which
    appear in >50 % of BKR sentences.  With the old hierarchy (theological
    first), almost every sentence was "theological_statement", making the
    downstream PMI in r_word_network.py blind to all other lexical patterns.

    New threshold for theological_statement:
        ≥ 2 THEOLOGICAL_LEMMA hits, OR
        1 hit + copular_description (e.g. "Hospodin jest Bůh" = identity claim)
    This excludes incidental divine references in legal, ritual, narrative, etc.

    Priority
    --------
    1.  genealogical_record     — most distinctive (zplodit/prvorozený)
    2.  ritual_liturgical       — specific cult vocabulary
    3.  legal_normative         — law / commandment vocabulary
    4.  prophetic_announcement  — "praví Hospodin" formula
    5.  creation_narrative      — stvořit / počátek
    6.  eschatological          — vzkříšení / skonání (rare terms only)
    7.  wisdom_maxim            — přísloví / lepší / moudrý
    8.  social_relation         — social / kinship roles
    9.  moral_statement         — evaluative moral language
    10. attribute_description   — quality adjectives
    11. theological_statement   — DEMOTED; stronger signal required
    12. state_description       — semantic_cluster == "description"
    13. general_narrative       — fallback
    """
    lemma_set = rules.lemma_set_of(feature)

    description_type = "general_narrative"
    confidence       = 0.5
    explanation      = "General descriptive statement."

    # ── 1. Genealogical ─────────────────────────────────────────────────────
    if lemma_set & GENEALOGICAL_RECORD_LEMMAS:
        description_type = "genealogical_record"
        confidence       = 0.80
        explanation      = "Contains lineage / genealogical record vocabulary."

    # ── 2. Ritual / liturgical ───────────────────────────────────────────────
    elif lemma_set & RITUAL_LITURGICAL_LEMMAS:
        description_type = "ritual_liturgical"
        confidence       = 0.80
        explanation      = "Contains sacrificial, priestly, or temple vocabulary."

    # ── 3. Legal / normative ─────────────────────────────────────────────────
    elif lemma_set & LEGAL_NORMATIVE_LEMMAS:
        description_type = "legal_normative"
        confidence       = 0.78
        explanation      = "Contains legal or covenant-normative vocabulary."

    # ── 4. Prophetic announcement ───────────────────────────────────────────
    elif _is_prophetic_formula(feature, lemma_set):
        description_type = "prophetic_announcement"
        confidence       = 0.78
        explanation      = (
            "Contains prophetic speech-formula ('praví Hospodin') "
            "or prophetic announcement vocabulary."
        )

    # ── 5. Creation narrative ────────────────────────────────────────────────
    elif _is_creation_sentence(feature, lemma_set):
        description_type = "creation_narrative"
        confidence       = 0.78
        explanation      = "Contains creation or cosmogonic vocabulary."

    # ── 6. Eschatological ────────────────────────────────────────────────────
    elif lemma_set & ESCHATOLOGICAL_LEMMAS_P:
        description_type = "eschatological"
        confidence       = 0.75
        explanation      = "Contains eschatological vocabulary (resurrection, judgment)."

    # ── 7. Wisdom maxim ──────────────────────────────────────────────────────
    elif lemma_set & WISDOM_MAXIM_LEMMAS:
        description_type = "wisdom_maxim"
        confidence       = 0.72
        explanation      = "Contains wisdom / gnomic / comparative vocabulary."

    # ── 8. Social relation ───────────────────────────────────────────────────
    elif lemma_set & SOCIAL_LEMMAS:
        description_type = "social_relation"
        confidence       = 0.70
        explanation      = "Contains social or kinship relations."

    # ── 9. Moral statement ───────────────────────────────────────────────────
    elif lemma_set & MORAL_LEMMAS:
        description_type = "moral_statement"
        confidence       = 0.70
        explanation      = "Contains moral or evaluative language."

    # ── 10. Theological statement (DEMOTED + TIGHTENED) ─────────────────────
    # Placed BEFORE attribute_description so that "Hospodin jest Bůh věrný"
    # (2 theological hits + attributes) is classified as theological, not
    # merely as attribute_description.
    #
    # Requires ≥ 2 theological lemma hits, OR 1 hit in a copular identity
    # structure ("Hospodin jest Bůh" = pure theological identity claim).
    # Single incidental mentions of "hospodin" in legal, ritual, or narrative
    # context are already captured by higher-priority categories above.
    elif (
        len(lemma_set & THEOLOGICAL_LEMMAS) >= 2
        or (
            len(lemma_set & THEOLOGICAL_LEMMAS) >= 1
            and feature.local_pattern == "copular_description"
        )
    ):
        description_type = "theological_statement"
        confidence       = 0.72
        explanation      = (
            "Contains ≥ 2 theological entities or concepts, or a theological "
            "copular identity claim."
        )

    # ── 11. Attribute description ────────────────────────────────────────────
    # Catches quality adjectives in sentences without theological context.
    # Examples: "David był silný" (but David is social_relation, so this
    # catches purely descriptive sentences: "Hora byla veliká.")
    elif lemma_set & ATTRIBUTE_LEMMAS:
        description_type = "attribute_description"
        confidence       = 0.70
        explanation      = "Describes attributes or qualities."

    # ── 12. State description ────────────────────────────────────────────────
    elif semantic.semantic_cluster == "description":
        description_type = "state_description"
        confidence       = 0.65
        explanation      = "Describes state or condition."

    return RefinedDescription(
        sentence_id=feature.sentence_id,
        sentence=feature.sentence,
        description_type=description_type,
        confidence=confidence,
        explanation=explanation,
        root_lemma=feature.root_lemma,
        semantic_cluster=semantic.semantic_cluster,
        lemmas=feature.lemmas,
        dep_tree=getattr(feature, "dep_tree", ""),
    )


# ==========================================================
# PIPELINE WRAPPER
# ==========================================================

def apply_refined_descriptions(
    text_input: TextInput
) -> List[RefinedDescription]:

    preprocessed = preprocess_text(text_input)
    features     = extract_features(preprocessed)
    semantics    = semantic_enrichment(features)

    return [
        refine_description(feat, sem)
        for feat, sem in zip(features, semantics)
    ]


def export_refined_csv(results, output_path):

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = [asdict(r) for r in results]
    if not rows:
        raise ValueError("No rows to export.")

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


# ==========================================================
# TEST BLOCK
# ==========================================================

if __name__ == "__main__":

    _TESTS = [
        # (sentence, expected_type, description)
        # ── Bias fix — these used to be theological_statement ──
        ("Zákon Hospodinův jest dokonalý.",         "legal_normative",       "law + hospodin → legal"),
        ("Přinesl zápalnou oběť na oltář.",         "ritual_liturgical",     "sacrifice + altar"),
        ("Praví Hospodin: přijdu k vám.",           "prophetic_announcement","praví Hospodin formula"),
        ("Na počátku stvořil Bůh nebe a zemi.",     "creation_narrative",    "stvořil → creation"),
        ("Abraham zplodil Izáka.",                  "genealogical_record",   "genealogical"),
        # ── Still theological when 2+ hits ──
        ("Hospodin jest Bůh věrný a milostivý.",    "theological_statement", "2 theological lemmas"),
        ("Hospodin jest Bůh.",                      "theological_statement", "copular + theological"),
        # ── Other categories ──
        ("David byl silný a mocný muž.",            "social_relation",       "social (David+muž)"),
        ("Spravedlivý žije, ale bezbožný zahyne.",  "moral_statement",       "moral (MORAL_LEMMAS)"),
        ("Lepší je moudrost než zlato.",            "wisdom_maxim",          "wisdom maxim"),
        ("Vzkříšení spravedlivých přijde.",         "eschatological",        "resurrection"),
    ]

    print(f"\n{'VETA':<52} {'got':<26} {'expected':<26} {'OK?'}")
    print("-" * 115)
    all_ok = True

    for sent, expected, desc in _TESTS:
        inp  = create_input_from_text(sent, source="written_record")
        pre  = preprocess_text(inp)
        feat = extract_features(pre)
        sem  = semantic_enrichment(feat)

        if not feat:
            print(f"  SKIP: {sent[:50]}")
            continue

        r  = refine_description(feat[0], sem[0])
        ok = "✓" if r.description_type == expected else "✗"
        if r.description_type != expected:
            all_ok = False
        print(
            f"{sent[:50]:<52} "
            f"{r.description_type:<26} "
            f"{expected:<26} {ok}  {desc}"
        )
        if r.description_type != expected:
            hits_theo = len(set(feat[0].lemmas.split()) & THEOLOGICAL_LEMMAS)
            print(f"    lemmas={feat[0].lemmas[:60]}  theo_hits={hits_theo}")

    print()
    print("ALL PASS" if all_ok else "SOME FAILED")

    # ── Distribution demo on the test corpus ──────────────────────────────
    from collections import Counter
    counts = Counter(r.description_type for _sent, expected, _ in _TESTS
                     for r in [refine_description(
                         extract_features(preprocess_text(
                             create_input_from_text(_sent, source="written_record")
                         ))[0],
                         semantic_enrichment(
                             extract_features(preprocess_text(
                                 create_input_from_text(_sent, source="written_record")
                             ))
                         )[0],
                     )])
    print("\n=== Distribution (test sentences) ===")
    for dtype, n in counts.most_common():
        print(f"  {dtype:<30} {n:>3}")

    export_refined_csv(
        [refine_description(
             extract_features(preprocess_text(create_input_from_text(s, source="written_record")))[0],
             semantic_enrichment(extract_features(preprocess_text(create_input_from_text(s, source="written_record"))))[0],
         )
         for s, *_ in _TESTS],
        "output/refined_descriptions_test.csv",
    )
    print("\nCSV exported: output/refined_descriptions_test.csv")
