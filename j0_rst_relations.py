from __future__ import annotations

from typing import List, Optional

# ── RST connectors (match against first ~3 lemmas of current sentence) ────────

_CONNECTORS: list[tuple[str, set[str]]] = [
    ("condition",   {"jestliže", "pakliť", "li", "kdyby"}),
    ("cause",       {"neboť", "protože", "poněvadž", "protož", "tedy"}),
    ("contrast",    {"ale", "však", "nýbrž", "naopak"}),
    ("elaboration", {"totiž", "zajisté"}),
    ("temporal",    {"potom", "pak", "tehdy", "když"}),
]


def _head_lemmas(feature) -> set[str]:
    """Return the first ≤3 lemmas of a sentence as a lowercase set."""
    lemmas = getattr(feature, "lemmas", "") or ""
    return {t.lower() for t in lemmas.split()[:3]}


def classify_rst_relation(prev_feature, cur_feature) -> str:
    """
    Return the RST relation between prev_feature and cur_feature.
    Connector check is tried first; structural heuristics are the fallback.
    """
    if getattr(cur_feature, "has_conditional", False):
        return "condition"

    head = _head_lemmas(cur_feature)

    for label, tokens in _CONNECTORS:
        if head & tokens:
            return label

    prev_q   = getattr(prev_feature, "has_question",      False)
    cur_q    = getattr(cur_feature,  "has_question",      False)
    prev_imp = getattr(prev_feature, "is_imperative_like", False)

    if prev_q:
        return "answer"
    if cur_q:
        return "question"
    if prev_imp:
        return "motivation"
    return "continuation"


def annotate_rst(features) -> List[str]:
    """
    Return one RST label per feature (same length as features).
    The first sentence always gets 'continuation' (no previous sentence).
    """
    if not features:
        return []

    labels = ["continuation"]
    for i in range(1, len(features)):
        labels.append(classify_rst_relation(features[i - 1], features[i]))
    return labels


def rst_profile(relations: List[str]) -> dict:
    """
    Return counts per relation type and coherence_density
    (proportion of non-continuation relations).
    """
    if not relations:
        return {"total": 0, "coherence_density": 0.0}

    counts: dict[str, int] = {}
    for r in relations:
        counts[r] = counts.get(r, 0) + 1

    total = len(relations)
    non_cont = total - counts.get("continuation", 0)
    return {
        **counts,
        "total": total,
        "coherence_density": round(non_cont / total, 4),
    }
