from dataclasses import dataclass, asdict
from typing import List, Optional
from pathlib import Path
import csv

from genre_maps import detect_book_genre as _genre_detect

from c_input import TextInput, create_input_from_text
from d_preprocessing import preprocess_text
from e_extraction import extract_features, SentenceFeatures
from f_semantics import semantic_enrichment, SemanticFeatures
import g_skinner_rules as rules


# ==========================================================
# LEXIKÓNY
# ==========================================================

REPORTED_SPEECH_LEMMAS = frozenset({
    "říci", "odpovědět", "mluvit", "volat", "pravit",
    "promluvit", "oznámit", "zvěstovat", "kázat",
})

GENEALOGICAL_LEMMAS = frozenset({
    "zplodit", "narodit", "pocházet", "porodit",
    "zrodit", "sploditi", "syn", "dcera",
    "otec", "matka", "rod", "pokolení",
})

HISTORICAL_EVENT_LEMMAS = frozenset({
    "stvořit", "učinit", "vzít", "dát", "poslat",
    "přijít", "odejít", "vstát", "padnout", "bojovat",
    "zabít", "postavit", "zničit", "dobýt",
})

UNCERTAINTY_LEMMAS = frozenset({
    "možná", "snad", "asi", "myslet", "domnívat",
    "pochybovat", "zdát", "zdáti",
})

REQUEST_LEMMAS = frozenset({
    "prosit", "žádat", "dát", "pomoci", "potřebovat",
})

WISDOM_LEMMAS = frozenset({
    "moudrý", "moudrost", "blázen", "bláznovství",
    "přísloví", "naučení", "lepší", "jako", "tak",
    "cesta", "srdce", "ústa", "jazyk", "spravedlivý",
})

# ── Parallelismus membrorum lexicons ────────────────────────────────────────

# Antithetic parallelism — opposing quality/moral terms used in contrast pairs
WISDOM_ANTITHETIC_LEMMAS = frozenset({
    "spravedlivý", "bezbožný", "moudrý", "blázen",
    "dobrý", "zlý", "živý", "mrtvý",
    "věrný", "nevěrný", "bohatý", "chudý",
    "pravda", "lež",
})

# "Lepší X než Y" graduated wisdom comparison
WISDOM_BETTER_THAN_LEMMAS = frozenset({
    "lepší", "více", "víc", "hůře", "lépe",
})

# Comparative connectors for simile/parallelism
WISDOM_COMPARATIVE_LEMMAS = frozenset({
    "jako", "přirovnat", "podobný", "podobně",
})

LYRICAL_LEMMAS = frozenset({
    "chválit", "velebit", "oslavovat", "zpívat",
    "žalm", "píseň", "nárek", "plakat", "volat",
    "blahoslavený", "vyznávat", "důvěřovat",
})

PROPHETIC_LEMMAS = frozenset({
    "praví", "hospodin", "prorok", "vidění",
    "slovo", "zvěstovat", "ohlásit", "proroctví",
})

LAMENT_HELP_LEMMAS = frozenset({
    "pomoci", "zachránit", "vytrhnout",
    "vysvobodit", "vyslyšet", "naklonit", "pohledět",
})
LAMENT_QUESTION_LEMMAS = frozenset({
    "proč", "dokud", "pokud", "dlouho",
})
LAMENT_DISTRESS_LEMMAS = frozenset({
    "nepřítel", "soužení", "tíseň",
    "zahynout", "sklesnouti", "pohltit", "obklíčit",
})
LAMENT_APPEAL_LEMMAS = frozenset({
    "hospodin", "hospodine", "hospodina",
    "bůh", "bože",
    "král", "volat",
})
LAMENT_ABANDONMENT_LEMMAS = frozenset({
    "daleko", "skrýt", "mlčet",
    "neodpovídat", "opustit",
})

PRAISE_LYRICAL_LEMMAS = frozenset({
    "pastýř", "skála", "záštita",
    "světlo", "spása", "pevnost", "štít", "útočiště",
})
PRAISE_EXCLAMATION_LEMMAS = frozenset({
    "haleluja", "chválit", "velebit",
    "oslavovat", "zpívat", "jásat",
})
PRAISE_ATTRIBUTE_LYRICAL_LEMMAS = frozenset({
    "věčný", "mocný", "věrný",
    "milosrdný", "veliký", "slavný",
})

TRUST_LEMMAS = frozenset({
    "důvěřovat", "spoléhat", "útočiště",
    "doufat", "čekat", "naděje",
})
TRUST_METAPHOR_LEMMAS = frozenset({
    "pastýř", "skála", "pevnost",
    "záštita", "štít", "křídlo",
})
TRUST_FIRST_PERSON_LEMMAS = frozenset({
    "já", "můj", "mě", "mně", "mnou",
})

REMEMBRANCE_LEMMAS = frozenset({
    "rozpomenout", "rozpomeň",
    "pamětliv", "nezapomenout", "připomenout", "pamatovat",
})
REMEMBRANCE_HISTORICAL_LEMMAS = frozenset({
    "egypt", "poušť", "vyjít",
    "vysvobodit", "div", "zázrak", "předek", "david",
})
REMEMBRANCE_FORMULA_LEMMAS = frozenset({
    "jako", "jakož", "tak",
    "tehdy", "kdysi",
})

# Conjunctions that signal antithetic structure
_CONTRAST_CONJ = frozenset({"ale", "nýbrž", "kdežto", "avšak", "však"})


# ==========================================================
# ŽÁNROVÁ DETEKCIA (bod 2)
# ==========================================================

# DEAD: presunuté do genre_maps.py — kľúče (Ž, Př, Rl, Jz, Pís, Ab, Jn, Ml, Dn, Tt)
# nezodpovedali reálnym názvom súborov korpusu; nahradené file-keyed mapou.
# BOOK_GENRES: dict[str, str] = { "Ž": "psalm", "Př": "wisdom", ... }

# Per-genre confidence adjustments applied AFTER base classification.
# Positive = boost; negative = reduce.  Max final conf is capped at 0.95.
_GENRE_ADJ: dict[str, dict[str, float]] = {
    "psalm":     {"lyrical_relation":   +0.10, "reported_speech":        -0.05,
                  "wisdom_relation":    +0.05},
    "wisdom":    {"wisdom_relation":    +0.10, "lyrical_relation":       +0.05},
    "prophetic": {"prophetic_relation": +0.10, "lyrical_relation":       +0.05},
    "epistle":   {"wisdom_relation":    +0.05, "autoclitic_relation":    +0.05},
    "gospel":    {"reported_speech":    +0.05, "request_relation":       +0.03},
    "historical":{"historical_event_relation": +0.05,
                  "genealogical_relation":      +0.05},
    "lyrical":   {"lyrical_relation":   +0.08},
    "law":       {"request_relation":          +0.05,  # príkazy, zákazy (primárny mód)
                  "autoclitic_relation":       +0.05,  # podmienené klauzuly ("ak kto...")
                  "reported_speech":           +0.03,  # "Hospodin riekl Mojžíšovi" rámec
                  "historical_event_relation": -0.05,  # naratív nie je primárny
                  "descriptive_relation":      -0.05}, # deskripcia nie je primárna
}


def detect_book_genre(file_name: str) -> str:
    """Return coarse genre for _GENRE_ADJ (delegates to genre_maps, coarse=True)."""
    return _genre_detect(file_name, coarse=True)


def _apply_genre_adj(relation_type: str, confidence: float, genre: str) -> float:
    """Return confidence adjusted by genre-specific boost/penalty."""
    adj = _GENRE_ADJ.get(genre, {}).get(relation_type, 0.0)
    return min(round(confidence + adj, 3), 0.95)


# ==========================================================
# LYRICAL PATTERN HELPERS
# ==========================================================

def has_lament_pattern(feature) -> bool:
    if (
        rules.has_any_lemma(feature, LAMENT_HELP_LEMMAS)
        and rules.has_any_lemma(feature, LAMENT_DISTRESS_LEMMAS)
    ):
        return True
    if (
        rules.has_any_lemma(feature, LAMENT_QUESTION_LEMMAS)
        and rules.has_any_lemma(feature, LAMENT_ABANDONMENT_LEMMAS)
    ):
        return True
    if (
        rules.has_any_lemma(feature, LAMENT_APPEAL_LEMMAS)
        and feature.has_question
    ):
        return True
    return False


def has_praise_lyrical_pattern(feature) -> bool:
    if rules.has_any_lemma(feature, PRAISE_EXCLAMATION_LEMMAS):
        return True
    if (
        rules.has_any_lemma(feature, PRAISE_LYRICAL_LEMMAS)
        and rules.has_any_lemma(feature, PRAISE_ATTRIBUTE_LYRICAL_LEMMAS)
    ):
        return True
    if (
        rules.has_any_lemma(feature, PRAISE_LYRICAL_LEMMAS)
        and rules.has_any_lemma(feature, LAMENT_APPEAL_LEMMAS)
    ):
        return True
    return False


def has_trust_confession_pattern(feature) -> bool:
    if (
        rules.has_any_lemma(feature, TRUST_LEMMAS)
        and rules.has_any_lemma(feature, TRUST_FIRST_PERSON_LEMMAS)
    ):
        return True
    if (
        rules.has_any_lemma(feature, TRUST_METAPHOR_LEMMAS)
        and rules.has_any_lemma(feature, TRUST_FIRST_PERSON_LEMMAS)
    ):
        return True
    if (
        rules.has_any_lemma(feature, TRUST_LEMMAS)
        and rules.has_any_lemma(feature, LAMENT_APPEAL_LEMMAS)
    ):
        return True
    return False


def has_remembrance_pattern(feature) -> bool:
    if rules.has_any_lemma(feature, REMEMBRANCE_LEMMAS):
        return True
    if (
        rules.has_any_lemma(feature, REMEMBRANCE_HISTORICAL_LEMMAS)
        and rules.has_any_lemma(feature, REMEMBRANCE_FORMULA_LEMMAS)
    ):
        return True
    if (
        rules.has_any_lemma(feature, REMEMBRANCE_HISTORICAL_LEMMAS)
        and rules.has_any_lemma(feature, LAMENT_APPEAL_LEMMAS)
    ):
        return True
    return False


# ==========================================================
# WISDOM / PARALLELISMUS HELPERS  (bod 3)
# ==========================================================

def has_comparative_structure(feature) -> bool:
    """
    Detect 'jako...tak' simile / comparative parallelism.

    The Hebrew mashal typically pairs a 'like X' clause with 'so Y' —
    in BKR Czech rendered as 'jako...tak'.  Both must be present in the
    same sentence for a reliable signal.

    Examples
    --------
    "Jako laně touží po potoce, tak má duše touží po tobě."  → True
    "Jako stín mé dny odcházejí."  → False (tak missing)
    """
    lemmas = set(feature.lemmas.split())
    return "jako" in lemmas and "tak" in lemmas


def has_antithetic_parallelism(feature) -> bool:
    """
    Detect antithetic parallelism — contrastive conjunction + opposing moral terms.

    Hebrew antithetic parallelism places opposite ideas in adjacent lines.
    BKR Czech renders the contrast with 'ale', 'nýbrž', 'kdežto' or 'avšak'
    alongside quality pairs like spravedlivý/bezbožný or moudrý/blázen.

    Examples
    --------
    "Spravedlivý žije svou věrností, ale bezbožný svou nevěrou."  → True
    "Moudrý syn působí otci radost, ale pošetilý je pohrdáním..."  → True
    "Hospodin je dobrý, ale tebe nechci chválit."  → False (no antithetic pair)
    """
    return (
        rules.has_any_lemma(feature, _CONTRAST_CONJ)
        and rules.has_any_lemma(feature, WISDOM_ANTITHETIC_LEMMAS)
    )


def has_better_than_structure(feature) -> bool:
    """
    Detect 'lepší X než Y' graduated wisdom comparison.

    The 'better-than' saying (tov-saying) is a staple of Proverbs and
    Ecclesiastes.  BKR Czech uses 'lepší...než' or 'lépe...nežli'.

    Examples
    --------
    "Lepší je moudrost než zlato."  → True
    "Lépe je přebývat v koutě, nežli s hádavou ženou."  → True
    "Moudrý je lepší."  → False (no 'než')
    """
    lemmas = set(feature.lemmas.split())
    has_comp = bool(lemmas & WISDOM_BETTER_THAN_LEMMAS)
    has_than = "než" in lemmas or "nežli" in lemmas
    return has_comp and has_than


def has_parallelismus_pattern(feature) -> bool:
    """
    Return True if the sentence shows any parallelismus membrorum pattern:
    comparative (jako/tak), antithetic (ale + opposing pair), or better-than
    (lepší/než).
    """
    return (
        has_comparative_structure(feature)
        or has_antithetic_parallelism(feature)
        or has_better_than_structure(feature)
    )


# Canonical relation_type vocabulary emitted by classify_relation().
# generate_demo_db and UI labels must stay in sync with this set.
RELATION_TYPE_VALUES = frozenset({
    "descriptive_relation",
    "lyrical_relation",
    "reported_speech",
    "request_relation",
    "genealogical_relation",
    "wisdom_relation",
    "historical_event_relation",
    "autoclitic_relation",
    "prophetic_relation",
})


# ==========================================================
# OUTPUT DATACLASS
# ==========================================================

@dataclass
class VerbalRelation:

    sentence_id: int
    sentence: str

    relation_type: str
    subtype: str
    confidence: float
    explanation: str

    root_lemma: Optional[str]
    local_pattern: str
    semantic_cluster: str


# ==========================================================
# CORE CLASSIFIER  (bod 1 — opravená hierarchia)
# ==========================================================

def classify_relation(
    feature: SentenceFeatures,
    semantic: SemanticFeatures,
    file_name: str = "",
) -> VerbalRelation:
    """
    Classify verbal relation type for a sentence.

    Methodological note
    -------------------
    This classifier is intentionally hybrid: it combines selected B.F. Skinner
    verbal-behavior operant proxies (currently request/mand-like and
    uncertainty/autoclitic-like) with Bible-genre relation categories
    (genealogical, wisdom, historical_event, prophetic, lyrical, reported).
    The hybrid layer is specific to the biblical corpus use case.

    Priority waterfall — rationale for ordering
    -------------------------------------------
    1.  Lyrical (strong signals: lament / praise / trust / remembrance)
        Checked BEFORE reported_speech because PRAISE_EXCLAMATION_LEMMAS
        ("haleluja", "chválit", "oslavovat") and LAMENT_APPEAL_LEMMAS
        ("hospodine", "bože") frequently co-occur with REPORTED_SPEECH_LEMMAS
        ("zvěstovat", "volat") in hymns.  Without this guard, "Haleluja!
        Zvěstujte jeho skutky!" is mis-classified as reported_speech.

    2.  Reported speech  (verbum dicendi, but no dominant lyrical signal)

    3.  Request / mand  (imperative, modal-question, request verbs)

    4.  Genealogical  (zplodit/narodit/rod — no reported-speech overlap)

    5.  Wisdom  (gnomic maxim, parallelismus membrorum — checked before
        historical because wisdom verbs like "jít" can appear in proverbs)

    6.  Historical event  (past-tense action verbs without speech/imperative)

    7.  Uncertainty / autoclitic

    8.  Prophetic  (checked late: shares "hospodin"/"slovo" with lyrical)

    9.  Generic lyrical  (LYRICAL_LEMMAS fallback without specific subtype)

    10. Descriptive fallback

    Genre adjustment
    ----------------
    If *file_name* is supplied, detect_book_genre() maps it to a genre
    ("psalm", "wisdom", "prophetic", etc.) and _apply_genre_adj() adds a
    small confidence boost/penalty to reward genre-consistent predictions.

    Parameters
    ----------
    file_name : str, optional
        BKR file name (e.g. "bible_BKR_Ž.txt").  Used for genre adjustment.
        Backward-compatible default is "" (no adjustment).
    """
    genre = detect_book_genre(file_name) if file_name else "unknown"

    if feature.root_lemma is None:
        return VerbalRelation(
            sentence_id=feature.sentence_id,
            sentence=feature.sentence,
            relation_type="descriptive_relation",
            subtype="no_root_lemma",
            confidence=0.0,
            explanation="No root lemma available.",
            root_lemma=None,
            local_pattern=feature.local_pattern,
            semantic_cluster=semantic.semantic_cluster,
        )

    relation_type = "descriptive_relation"
    subtype       = "general_description"
    confidence    = 0.5
    explanation   = "General verbal relation."
    root          = feature.root_lemma.lower()

    # ── 1. LYRICAL (strong subtypes — MUST precede reported_speech) ─────────
    # Hymns and psalms routinely use verbum dicendi (zvěstovat, volat) alongside
    # explicit praise/lament vocabulary.  Lyrical priority prevents the verbum
    # dicendi from hijacking hymnic sentences.

    if has_lament_pattern(feature):
        relation_type = "lyrical_relation"
        subtype       = "lament"
        confidence    = 0.75
        explanation   = "Sentence expresses lamentation or cry for help."

    elif has_praise_lyrical_pattern(feature):
        relation_type = "lyrical_relation"
        subtype       = "praise_lyrical"
        confidence    = 0.75
        explanation   = "Sentence expresses lyrical praise or exaltation."

    elif has_trust_confession_pattern(feature):
        relation_type = "lyrical_relation"
        subtype       = "trust_confession"
        confidence    = 0.70
        explanation   = "Sentence expresses trust or personal confession of faith."

    elif has_remembrance_pattern(feature):
        relation_type = "lyrical_relation"
        subtype       = "remembrance"
        confidence    = 0.70
        explanation   = "Sentence recalls historical saving acts or divine memory."

    # ── 2. REPORTED / DIALOGIC SPEECH ───────────────────────────────────────

    elif (
        root in REPORTED_SPEECH_LEMMAS
        or rules.has_any_lemma(feature, REPORTED_SPEECH_LEMMAS)
    ):
        relation_type = "reported_speech"
        subtype       = "dialogic_or_reported_utterance"
        confidence    = 0.80
        explanation   = "Sentence reports verbal interaction or quoted speech."

    # ── B.F. Skinner operant types ───────────────────────────────────────────
    # ── 3. REQUEST / MAND ───────────────────────────────────────────────────

    elif (
        (
            feature.is_imperative_like
            or feature.local_pattern in {
                "imperative_action_object",
                "modal_question_request_like",
            }
            or rules.has_any_lemma(feature, REQUEST_LEMMAS)
        )
        and not has_praise_lyrical_pattern(feature)
    ):
        relation_type = "request_relation"
        subtype       = "mand_like_relation"
        confidence    = 0.80
        explanation   = "Sentence expresses request-like verbal relation."

    # ── Bible-genre specific relation types ─────────────────────────────────
    # ── 4. GENEALOGICAL ─────────────────────────────────────────────────────

    elif (
        root in {"zplodit", "narodit", "pocházet", "porodit"}
        or (
            rules.has_any_lemma(feature, GENEALOGICAL_LEMMAS)
            and not rules.has_reported_speech_pattern(feature)
        )
    ):
        relation_type = "genealogical_relation"
        subtype       = "lineage_record"
        confidence    = 0.80
        explanation   = "Sentence expresses genealogical relation."

    # ── 5. WISDOM / PARALLELISMUS MEMBRORUM ─────────────────────────────────
    # Checked before historical_event because wisdom verbs (jít, vzít) appear
    # in proverbs but the parallelismus / wisdom lexicon is the primary signal.

    elif (
        (
            rules.has_any_lemma(feature, WISDOM_LEMMAS)
            or has_parallelismus_pattern(feature)
        )
        and feature.local_pattern in {
            "general_statement",
            "copular_description",
            "negated_statement",
        }
        and not rules.has_reported_speech_pattern(feature)
    ):
        relation_type = "wisdom_relation"

        if has_comparative_structure(feature):
            subtype     = "comparative_parallelism"
            confidence  = 0.75
            explanation = (
                "Sentence uses 'jako...tak' comparative parallelism "
                "(simile / Hebrew mashal structure)."
            )
        elif has_antithetic_parallelism(feature):
            subtype     = "antithetic_parallelism"
            confidence  = 0.75
            explanation = (
                "Sentence uses antithetic parallelism — contrastive conjunction "
                "(ale/nýbrž/kdežto) with opposing quality pair."
            )
        elif has_better_than_structure(feature):
            subtype     = "better_than_maxim"
            confidence  = 0.75
            explanation = (
                "Sentence uses 'lepší...než' graduated wisdom comparison "
                "(tov-saying structure)."
            )
        else:
            subtype     = "gnomic_maxim"
            confidence  = 0.70
            explanation = "Sentence expresses a wisdom saying or gnomic maxim."

    # ── 6. HISTORICAL EVENT ──────────────────────────────────────────────────

    elif (
        (
            root in HISTORICAL_EVENT_LEMMAS
            or rules.has_any_lemma(feature, HISTORICAL_EVENT_LEMMAS)
        )
        and not rules.has_reported_speech_pattern(feature)
        and not feature.is_imperative_like
        and not rules.has_any_lemma(feature, UNCERTAINTY_LEMMAS)
    ):
        relation_type = "historical_event_relation"
        subtype       = "event_or_creation_statement"
        confidence    = 0.75
        explanation   = "Sentence describes event or creation."

    # ── B.F. Skinner operant types ───────────────────────────────────────────
    # ── 7. UNCERTAINTY / AUTOCLITIC ─────────────────────────────────────────

    elif (
        semantic.uncertainty_score > 0
        or rules.has_any_lemma(feature, UNCERTAINTY_LEMMAS)
        or semantic.semantic_cluster == "uncertainty"
    ):
        relation_type = "autoclitic_relation"
        subtype       = "uncertainty_marker"
        confidence    = 0.60
        explanation   = "Sentence contains uncertainty or qualification."

    # ── 8. PROPHETIC ─────────────────────────────────────────────────────────
    # Checked late: PROPHETIC_LEMMAS ("hospodin", "slovo") overlap heavily with
    # lyrical lexicons.  By this point, lyrical subtypes have already been ruled
    # out, so prophetic is the correct classification.

    elif (
        rules.has_any_lemma(feature, PROPHETIC_LEMMAS)
        and not rules.has_reported_speech_pattern(feature)
    ):
        relation_type = "prophetic_relation"
        subtype       = "prophetic_announcement"
        confidence    = 0.70
        explanation   = "Sentence contains prophetic or oracular language."

    # ── 9. GENERIC LYRICAL (LYRICAL_LEMMAS fallback) ────────────────────────

    elif (
        rules.has_any_lemma(feature, LYRICAL_LEMMAS)
        and not rules.has_reported_speech_pattern(feature)
    ):
        relation_type = "lyrical_relation"
        subtype       = "psalm_or_hymnic_utterance"
        confidence    = 0.70
        explanation   = "Sentence is a psalm, hymn, or lyrical utterance."

    # ── Genre-specific confidence adjustment ────────────────────────────────
    confidence = _apply_genre_adj(relation_type, confidence, genre)

    return VerbalRelation(
        sentence_id=feature.sentence_id,
        sentence=feature.sentence,
        relation_type=relation_type,
        subtype=subtype,
        confidence=confidence,
        explanation=explanation,
        root_lemma=root,
        local_pattern=feature.local_pattern,
        semantic_cluster=semantic.semantic_cluster,
    )


# ==========================================================
# PIPELINE WRAPPER
# ==========================================================

def apply_verbal_relations(
    text_input: TextInput,
    file_name: str = "",
) -> List[VerbalRelation]:

    preprocessed = preprocess_text(text_input)
    features     = extract_features(preprocessed)
    semantics    = semantic_enrichment(features)

    return [
        classify_relation(feat, sem, file_name=file_name)
        for feat, sem in zip(features, semantics)
    ]


def export_relations_csv(results, output_path):

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = [asdict(r) for r in results]
    if not rows:
        raise ValueError("No relations to export.")

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


# ==========================================================
# TEST BLOCK
# ==========================================================

if __name__ == "__main__":

    _TESTS = [
        # (sentence, expected_relation_type, description)
        # ── Lyrical priority over reported_speech (bod 1) ──
        ("Chvalte Hospodina a zvěstujte jeho skutky.",
         "lyrical_relation",
         "hymn with zvěstovat — should be lyrical, not reported_speech"),
        ("Zpívejte Hospodinu, oznamujte po všech národech jeho skutky.",
         "lyrical_relation",
         "hymn with oznámit — should be lyrical, not reported_speech"),
        ("Proč jsi mě opustil, Bože?",
         "lyrical_relation",
         "lament — Eloi Eloi"),
        ("Hospodin jest pastýř můj, nebudu míti nedostatku.",
         "lyrical_relation",
         "trust confession — Psalm 23"),
        # ── Wisdom: parallelismus membrorum (bod 3) ──
        ("Jako laně touží po potoce vody, tak má duše touží po tobě.",
         "wisdom_relation",
         "comparative parallelism jako/tak"),
        ("Spravedlivý žije svou věrností, ale bezbožný svou nevěrou.",
         "wisdom_relation",
         "antithetic parallelism ale + opposing pair"),
        ("Lepší je moudrost než zlato a stříbro.",
         "wisdom_relation",
         "better-than maxim lepší/než"),
        # ── Other relations ──
        ("Hospodin řekl Mojžíšovi toto slovo.",
         "reported_speech",
         "pure reported speech — verbum dicendi, no lyrical"),
        ("Abraham zplodil Izáka a Izák zplodil Jákoba.",
         "genealogical_relation",
         "genealogical record"),
    ]

    # Process each sentence INDEPENDENTLY to avoid Stanza alignment drift.
    print(f"\n{'VETA':<55} {'got':<28} {'expected':<28} {'OK?'}")
    print("-" * 130)
    all_ok   = True
    all_rels = []

    for sent, expected, desc in _TESTS:
        inp  = create_input_from_text(sent, source="written_record")
        pre  = preprocess_text(inp)
        feat = extract_features(pre)
        sem  = semantic_enrichment(feat)

        if not feat:
            print(f"  SKIP (no features): {sent[:50]}")
            continue

        rel = classify_relation(feat[0], sem[0])
        all_rels.append(rel)
        ok  = "✓" if rel.relation_type == expected else "✗"
        if rel.relation_type != expected:
            all_ok = False
        print(
            f"{sent[:53]:<55} "
            f"{rel.relation_type:<28} "
            f"{expected:<28} {ok}  {desc}"
        )
        if rel.relation_type != expected:
            print(f"    subtype={rel.subtype}  lemmas={feat[0].lemmas[:60]}")

    print()
    print("ALL PASS" if all_ok else "SOME FAILED")

    # ── Genre adjustment demo (bod 2) ─────────────────────────────────────
    print("\n=== Genre adjustment demo ===")
    _genre_demos = [
        ("bible_BKR_Ž.txt",   "psalm"),
        ("bible_BKR_1K.txt",  "epistle"),
        ("bible_BKR_Jr.txt",  "prophetic"),
        ("bible_BKR_Př.txt",  "wisdom"),
        ("bible_BKR_Gn.txt",  "historical"),
        ("",                   "unknown"),
    ]
    for fname, expected_genre in _genre_demos:
        got = detect_book_genre(fname) if fname else "unknown"
        adj = _GENRE_ADJ.get(got, {})
        ok  = "✓" if got == expected_genre else "✗"
        print(f"  {ok} {fname or '(none)':<22} genre={got:<12} adj={adj}")
    print()

    if all_rels:
        export_relations_csv(all_rels, "output/verbal_relations_test.csv")
        print("CSV exported: output/verbal_relations_test.csv")
