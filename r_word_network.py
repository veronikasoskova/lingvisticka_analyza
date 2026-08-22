from pathlib import Path
import csv
import math
from collections import Counter, defaultdict
from itertools import combinations

import numpy as np
import networkx as nx
try:
    import community as community_louvain
    _LOUVAIN_AVAILABLE = True
except ImportError:
    import warnings
    warnings.warn("python-louvain not installed; Louvain community detection will be skipped.")
    community_louvain = None
    _LOUVAIN_AVAILABLE = False
from scipy.sparse import lil_matrix
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

from a_paths import OUTPUT_DIR as ROOT_OUTPUT
from lexicons_common import (
    CLUSTER_NOISE_LEMMAS,
    SEMANTIC_STOP_LEMMAS,
    content_tokens,
)
from n_db import load_rows as _db_load, TABLE_REFINED
from t_config_tradition import (
    COVENANT_LAW,
    DIVINE_ELEMENTS,
    ESCHATOLOGY,
    GENEALOGY_LINEAGE,
    KINSHIP_ELEMENTS,
    LEGAL_ELEMENTS,
    LIFE_DEATH_ELEMENTS,
    MORAL_ELEMENTS,
    PROPHETIC_SPEECH,
    RITUAL_SACRIFICE,
    ROYAL_POWER_ELEMENTS,
    SACRED_SPACE,
    WAR_CONFLICT_ELEMENTS,
    WISDOM_ELEMENTS,
    canonicalize_lemma,
)


# ==========================================================
# R1. PATHS / CONFIG
# ==========================================================

OUTPUT_DIR_PMI        = ROOT_OUTPUT / "word_relations"
OUTPUT_DIR_CENTRALITY = ROOT_OUTPUT / "weighted_centrality"
OUTPUT_DIR_CLUSTERS   = ROOT_OUTPUT / "concept_clusters"
OUTPUT_DIR_GRAPH      = ROOT_OUTPUT / "word_network_graph"
OUTPUT_DIR_COMMUNITY  = ROOT_OUTPUT / "word_communities"
OUTPUT_DIR_EMBEDDINGS = ROOT_OUTPUT / "word_embeddings"

PER_TYPE_EXPORTS = {
    # Original three (kept for backward compat with existing CSVs)
    "theological_statement":  "pmi_theological.csv",
    "moral_statement":        "pmi_moral.csv",
    "social_relation":        "pmi_social.csv",
    # New granular types (p_refine_descriptions v2)
    "legal_normative":        "pmi_legal.csv",
    "ritual_liturgical":      "pmi_ritual.csv",
    "prophetic_announcement": "pmi_prophetic.csv",
    "wisdom_maxim":           "pmi_wisdom.csv",
    "creation_narrative":     "pmi_creation.csv",
    "eschatological":         "pmi_eschatological.csv",
    "genealogical_record":    "pmi_genealogical.csv",
}

CLUSTER_SEEDS = {
    "cultic_cluster": set(RITUAL_SACRIFICE) | set(SACRED_SPACE) | {
        "stan", "schrána", "levita", "obětovat", "posvětit", "zápal",
        "svatyně", "roucho", "efod", "náprsník", "kadidlo",
    },
    "royal_cluster": set(ROYAL_POWER_ELEMENTS) | {
        "david", "šalomoun", "saul", "farao", "královna", "žezlo",
        "koruna", "místodržitel", "místokrál",
    },
    "kinship_cluster": set(KINSHIP_ELEMENTS) | set(GENEALOGY_LINEAGE) | {
        "pokolení", "vdova", "sirotek", "manžel", "nevěsta", "ženich",
        "dědictví", "rodina",
    },
    "war_cluster": set(WAR_CONFLICT_ELEMENTS) | {
        "štít", "luk", "vozba", "hradba", "obléhat", "vítězství",
        "porážka", "kořist", "tábor", "brána", "město",
    },
    "theological_cluster": set(DIVINE_ELEMENTS) | {
        "pravda", "hřích", "spasení", "spása", "evangelium", "církev",
        "kříž", "slovo", "víra", "milost", "duch", "svatý",
    },
    "wisdom_cluster": set(WISDOM_ELEMENTS) | {
        "srdce", "bázeň", "rozum", "blázen", "přísloví", "kázeň",
        "poznání", "moudrost",
    },
    "covenant_cluster": set(COVENANT_LAW) | set(LEGAL_ELEMENTS) | {
        "smlouva", "desatero", "svědectví", "ustanovení", "přikázání",
    },
    "judgment_cluster": {
        "soud", "hněv", "trest", "pokání", "vina", "rozsudek",
        "odplata", "zatracení", "proklít", "soudce", "svědek",
    },
    "salvation_cluster": set(LIFE_DEATH_ELEMENTS) | set(ESCHATOLOGY) | {
        "spasení", "spása", "vykoupení", "kříž", "odpuštění",
        "evangelium", "zachránit", "vysvobodit",
    },
    "creation_cluster": {
        "stvořit", "stvoření", "nebe", "země", "světlo", "tma",
        "počátek", "voda", "den", "temnota", "stvořitel",
    },
    "prophetic_cluster": set(PROPHETIC_SPEECH) | {
        "prorokovat", "břímě", "sen", "anděl", "vidění", "zjevení",
    },
    "moral_cluster": set(MORAL_ELEMENTS) | {
        "pokora", "pýcha", "milosrdenství", "odpuštění", "láska",
        "nenávist", "ctnost", "hřích", "nepravost",
    },
}


_NETWORK_STOP = SEMANTIC_STOP_LEMMAS | CLUSTER_NOISE_LEMMAS


# ==========================================================
# R2. LOAD
# ==========================================================

def load_rows():
    return _db_load(TABLE_REFINED)


# ==========================================================
# R3. PMI VÝPOČET
# ==========================================================

def _tokenize(sentence):
    """Strip punctuation, canonicalize, drop function words and cluster noise."""
    tokens = []
    for tok in content_tokens(sentence, stop=_NETWORK_STOP):
        canon = canonicalize_lemma(tok)
        if len(canon) >= 3 and canon not in _NETWORK_STOP:
            tokens.append(canon)
    return tokens


def _get_tokens(row):
    """
    Content tokens for PMI / centrality.

    Cleaning happens here, at the start of the word-network program:
    commas, colons and similar marks are stripped from each token, then
    BKR function words (jsem, kterýž, protož, jich, vám, takto, …) and
    formulaic speech verbs (řekl, praví, stalo) are dropped. Remaining
    tokens are canonicalised so "boha," / "tmy" match lexicon seeds.
    """
    raw = row.get("lemmas") or row.get("sentence") or ""
    return _tokenize(raw)


def compute_word_frequency(rows):

    counter = Counter()

    for row in rows:
        counter.update(_get_tokens(row))

    return counter


def compute_cooccurrence(rows):

    pair_counter = Counter()

    for row in rows:
        tokens = sorted(set(_get_tokens(row)))
        for pair in combinations(tokens, 2):
            pair_counter[pair] += 1

    return pair_counter


def compute_ppmi(
    word_counter,
    pair_counter,
    total_sentences,
    min_pair_count=5,
):
    """
    Computes PMI, PPMI (max(0,PMI)), PMI² and PPMI² per pair.
    PMI²(x,y) = PMI + log₂P(x,y) — penalises rare pairs proportional to their rarity,
    correcting the bias that inflates PMI scores for low-frequency pairs.
    Sort order: PPMI descending (positive associations first).
    """
    total_words = sum(word_counter.values())
    relations = []

    for (word1, word2), pair_count in pair_counter.items():
        if pair_count < min_pair_count:
            continue
        p_xy = pair_count / total_sentences
        p_x  = word_counter[word1] / total_words
        p_y  = word_counter[word2] / total_words

        pmi   = math.log2(p_xy / (p_x * p_y))
        ppmi  = max(0.0, pmi)
        pmi2  = pmi + math.log2(p_xy)   # PMI²: punishes rare pairs via log P(x,y)
        ppmi2 = max(0.0, pmi2)

        relations.append({
            "word1":      word1,
            "word2":      word2,
            "pair_count": pair_count,
            "pmi":        round(pmi,   3),
            "ppmi":       round(ppmi,  3),
            "pmi2":       round(pmi2,  3),
            "ppmi2":      round(ppmi2, 3),
        })

    return sorted(relations, key=lambda x: x["ppmi"], reverse=True)


def compute_ppmi_per_type(rows, description_type, min_pair_count=3):
    type_rows = [r for r in rows if r["description_type"] == description_type]
    if not type_rows:
        return []
    word_counter = Counter()
    pair_counter = Counter()
    for row in type_rows:
        tokens = sorted(set(_get_tokens(row)))
        word_counter.update(tokens)
        for pair in combinations(tokens, 2):
            pair_counter[pair] += 1
    return compute_ppmi(word_counter, pair_counter, len(type_rows), min_pair_count)


# ==========================================================
# R3c. SPARSE PPMI MATRIX  (scipy.sparse — replaces list-of-dicts
#      for matrix operations and LSA downstream)
# ==========================================================

def build_ppmi_matrix_from_counters(word_counter, pair_counter, total_sentences, min_count=5):
    """
    Build a symmetric scipy sparse PPMI matrix from pre-computed counters.
    Returns (vocab_list, csr_matrix).  vocab_list[i] = word at column/row i.
    """
    # Sort by frequency desc so vocab[0..N] = most common words (important for LSA subset)
    vocab = sorted(
        (w for w, c in word_counter.items() if c >= min_count),
        key=lambda w: -word_counter[w],
    )
    if not vocab:
        return [], None
    w2i = {w: i for i, w in enumerate(vocab)}
    V = len(vocab)
    total_words = sum(word_counter[w] for w in vocab)

    M = lil_matrix((V, V), dtype=np.float32)
    for (w1, w2), cnt in pair_counter.items():
        if cnt < min_count:
            continue
        i = w2i.get(w1)
        j = w2i.get(w2)
        if i is None or j is None:
            continue
        p_xy = cnt / total_sentences
        p_x  = word_counter[w1] / total_words
        p_y  = word_counter[w2] / total_words
        pmi  = math.log2(p_xy / (p_x * p_y))
        if pmi > 0:
            M[i, j] = pmi
            M[j, i] = pmi

    return vocab, M.tocsr()


def export_relations(relations, output_path, max_rows=1000):
    if not relations:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(relations[0].keys()))
        writer.writeheader()
        writer.writerows(relations[:max_rows])


# ==========================================================
# R4. WEIGHTED CENTRALITY  (legacy heuristic — kept for backward compat)
# ==========================================================

def compute_weighted_centrality(relations):

    stats = defaultdict(lambda: {
        "connection_count": 0,
        "pmi_sum":          0.0,
        "pair_count_sum":   0,
    })

    for row in relations:

        pmi        = float(row["pmi"])
        pair_count = int(row["pair_count"])

        for word in (row["word1"], row["word2"]):
            stats[word]["connection_count"] += 1
            stats[word]["pmi_sum"]          += pmi
            stats[word]["pair_count_sum"]   += pair_count

    out_rows = []

    for word, v in stats.items():
        conn = v["connection_count"]
        out_rows.append({
            "word":             word,
            "connection_count": conn,
            "pmi_sum":          round(v["pmi_sum"], 3),
            "avg_pmi":          round(v["pmi_sum"] / conn, 3) if conn else 0.0,
            "pair_count_sum":   v["pair_count_sum"],
            "weighted_score":   round(v["pmi_sum"] * v["pair_count_sum"], 3),
        })

    return sorted(out_rows, key=lambda r: r["weighted_score"], reverse=True)


def export_centrality_csv(rows, output_path):

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "word", "connection_count", "pmi_sum",
                "avg_pmi", "pair_count_sum", "weighted_score",
            ]
        )
        writer.writeheader()
        writer.writerows(rows)


# ==========================================================
# R5. CONCEPT CLUSTERS
# ==========================================================

def assign_clusters(relations):

    cluster_edges = defaultdict(list)

    for row in relations:

        word1      = row["word1"]
        word2      = row["word2"]
        pmi        = float(row["pmi"])
        pair_count = int(row["pair_count"])

        for cluster_name, seeds in CLUSTER_SEEDS.items():
            hit1 = word1 in seeds
            hit2 = word2 in seeds
            if not (hit1 or hit2):
                continue
            # Drop edges whose non-seed side is formulaic noise / a stop lemma.
            partner = word2 if hit1 else word1
            if (
                partner not in seeds
                and (
                    partner in CLUSTER_NOISE_LEMMAS
                    or partner in SEMANTIC_STOP_LEMMAS
                )
            ):
                continue
            cluster_edges[cluster_name].append({
                "cluster":      cluster_name,
                "word1":        word1,
                "word2":        word2,
                "pair_count":   pair_count,
                "pmi":          pmi,
                "matched_seed": word1 if hit1 else word2,
            })

    return cluster_edges


def export_cluster_edges(cluster_edges):

    OUTPUT_DIR_CLUSTERS.mkdir(parents=True, exist_ok=True)

    all_rows = []

    for cluster_name, rows in cluster_edges.items():

        sorted_rows = sorted(
            rows,
            key=lambda r: (r["pair_count"], r["pmi"]),
            reverse=True,
        )[:300]

        out = OUTPUT_DIR_CLUSTERS / f"{cluster_name}.csv"

        with out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "cluster", "word1", "word2",
                    "pair_count", "pmi", "matched_seed",
                ]
            )
            writer.writeheader()
            writer.writerows(sorted_rows)

        all_rows.extend(sorted_rows)

    combined = OUTPUT_DIR_CLUSTERS / "all_concept_clusters.csv"

    with combined.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "cluster", "word1", "word2",
                "pair_count", "pmi", "matched_seed",
            ]
        )
        writer.writeheader()
        writer.writerows(all_rows)


def export_cluster_summary(cluster_edges):

    out = OUTPUT_DIR_CLUSTERS / "cluster_summary.csv"

    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["cluster", "edge_count", "avg_pmi", "total_pair_count"]
        )
        writer.writeheader()

        for cluster_name, rows in cluster_edges.items():
            n = len(rows)
            writer.writerow({
                "cluster":          cluster_name,
                "edge_count":       n,
                "avg_pmi":          round(sum(r["pmi"] for r in rows) / n, 3) if n else 0,
                "total_pair_count": sum(r["pair_count"] for r in rows),
            })


# ==========================================================
# R4b. NETWORKX GRAPH CENTRALITY
#      betweenness + eigenvector + degree  (replaces heuristic weighted score)
# ==========================================================

def build_nx_graph(relations, weight_field="ppmi"):
    """Build undirected weighted NetworkX graph from a relations list."""
    G = nx.Graph()
    for r in relations:
        w = float(r.get(weight_field) or r.get("pmi", 0))
        if w > 0:
            G.add_edge(
                r["word1"], r["word2"],
                weight=w,
                pair_count=int(r.get("pair_count", 0)),
            )
    return G


def compute_nx_centrality(G, k_approx=500):
    """
    Degree, betweenness (k-sample approximation), eigenvector centrality.
    Returns list of dicts sorted by betweenness_centrality desc.
    """
    if len(G) == 0:
        return []

    k = min(k_approx, len(G))
    deg_c = nx.degree_centrality(G)
    btw_c = nx.betweenness_centrality(G, weight="weight", k=k, normalized=True)
    try:
        eig_c = nx.eigenvector_centrality_numpy(G, weight="weight")
    except Exception:
        eig_c = {n: 0.0 for n in G.nodes()}

    out = []
    for node in G.nodes():
        out.append({
            "word":                   node,
            "degree":                 G.degree(node),
            "degree_centrality":      round(deg_c.get(node, 0.0), 6),
            "betweenness_centrality": round(btw_c.get(node, 0.0), 6),
            "eigenvector_centrality": round(eig_c.get(node, 0.0), 6),
            "weighted_degree":        round(
                sum(d["weight"] for _, _, d in G.edges(node, data=True)), 3
            ),
        })
    return sorted(out, key=lambda x: x["betweenness_centrality"], reverse=True)


def export_nx_centrality(centrality_rows, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "word", "degree", "degree_centrality",
            "betweenness_centrality", "eigenvector_centrality", "weighted_degree",
        ])
        writer.writeheader()
        writer.writerows(centrality_rows)


# ==========================================================
# R5b. COMMUNITY DETECTION  (Louvain — replaces seed-based clustering)
# ==========================================================

def detect_communities_louvain(G, resolution=1.0):
    """
    Louvain community detection via python-louvain.
    Returns (partition, modularity, n_communities).
    partition: {node: community_id}
    """
    if not _LOUVAIN_AVAILABLE:
        import warnings
        warnings.warn("python-louvain not available; skipping Louvain step.")
        return {}, 0.0, 0
    if len(G) < 2:
        return {}, 0.0, 0
    partition  = community_louvain.best_partition(G, weight="weight", resolution=resolution)
    modularity = community_louvain.modularity(partition, G, weight="weight")
    return partition, modularity, len(set(partition.values()))


def export_communities(G, partition, output_path, top_per_community=30):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    communities: dict = defaultdict(list)
    for node, cid in partition.items():
        communities[cid].append(node)

    out_rows = []
    for cid in sorted(communities):
        members = communities[cid]
        scored = sorted(
            members,
            key=lambda n: sum(d["weight"] for _, _, d in G.edges(n, data=True)),
            reverse=True,
        )
        for rank, node in enumerate(scored[:top_per_community], 1):
            out_rows.append({
                "community_id":      cid,
                "rank_in_community": rank,
                "word":              node,
                "community_size":    len(members),
                "weighted_degree":   round(
                    sum(d["weight"] for _, _, d in G.edges(node, data=True)), 3
                ),
            })

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "community_id", "rank_in_community", "word",
            "community_size", "weighted_degree",
        ])
        writer.writeheader()
        writer.writerows(out_rows)


def export_community_summary(G, partition, modularity, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    communities: dict = defaultdict(list)
    for node, cid in partition.items():
        communities[cid].append(node)

    out_rows = []
    for cid in sorted(communities):
        members = communities[cid]
        internal = [
            (u, v, d) for u, v, d in G.edges(data=True)
            if partition.get(u) == cid and partition.get(v) == cid
        ]
        avg_w = (
            sum(d["weight"] for _, _, d in internal) / len(internal)
            if internal else 0.0
        )
        top5 = sorted(
            members,
            key=lambda n: sum(d["weight"] for _, _, d in G.edges(n, data=True)),
            reverse=True,
        )[:5]
        out_rows.append({
            "community_id":    cid,
            "size":            len(members),
            "internal_edges":  len(internal),
            "avg_edge_weight": round(avg_w, 3),
            "modularity":      round(modularity, 4),
            "top5_hubs":       ", ".join(top5),
        })

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "community_id", "size", "internal_edges",
            "avg_edge_weight", "modularity", "top5_hubs",
        ])
        writer.writeheader()
        writer.writerows(out_rows)


# ==========================================================
# R6b. GEPHI EXPORT  (GEXF + CSV edge/node tables)
# ==========================================================

def export_gephi_gexf(G, partition, centrality_rows, output_path):
    """
    GEXF export for Gephi — includes community, betweenness, eigenvector as node attrs.
    Open in Gephi → File → Open → run Layout (ForceAtlas2) → colour by Community.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cent_lookup = {r["word"]: r for r in centrality_rows}
    for node in G.nodes():
        G.nodes[node]["community"]   = int(partition.get(node, -1))
        c = cent_lookup.get(node, {})
        G.nodes[node]["betweenness"] = c.get("betweenness_centrality", 0.0)
        G.nodes[node]["eigenvector"] = c.get("eigenvector_centrality", 0.0)
        G.nodes[node]["degree"]      = c.get("degree", 0)
    nx.write_gexf(G, str(output_path))


def export_gephi_csv_edges(G, output_path):
    """Gephi Data Laboratory edge list: Source, Target, Weight, Type."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["Source", "Target", "Weight", "pair_count", "Type"]
        )
        writer.writeheader()
        for u, v, d in G.edges(data=True):
            writer.writerow({
                "Source": u, "Target": v,
                "Weight": round(d.get("weight", 0), 3),
                "pair_count": d.get("pair_count", 0),
                "Type": "Undirected",
            })


def export_gephi_csv_nodes(G, partition, centrality_rows, output_path):
    """Gephi Data Laboratory node list: Id, Label, Community, centrality attrs."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cent_lookup = {r["word"]: r for r in centrality_rows}
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Id", "Label", "Community",
            "Betweenness", "Eigenvector", "Degree", "WeightedDegree",
        ])
        writer.writeheader()
        for node in sorted(G.nodes()):
            c = cent_lookup.get(node, {})
            writer.writerow({
                "Id": node, "Label": node,
                "Community":      partition.get(node, -1),
                "Betweenness":    c.get("betweenness_centrality", 0.0),
                "Eigenvector":    c.get("eigenvector_centrality", 0.0),
                "Degree":         c.get("degree", 0),
                "WeightedDegree": c.get("weighted_degree", 0.0),
            })


# ==========================================================
# R7. LSA EMBEDDINGS  (PPMI sparse matrix + TruncatedSVD)
#     Complement to PMI: captures latent semantic dimensions.
#     gensim Word2Vec is unavailable → SVD on PPMI matrix (= LSA/LSI).
# ==========================================================

def compute_fasttext_similarities(
    vocab: list[str],
    models_dir: Path,
    top_n: int = 1000,
    min_sim: float = 0.50,
    max_vocab: int = 600,
) -> list[tuple[str, str, float]]:
    """
    Compute top-N word-pair cosine similarities from the BKR FastText model.
    Complement to LSA: FastText uses subword n-grams so handles BKR OOV.
    Returns [(word1, word2, cosine_sim)] sorted desc.
    Returns empty list if model unavailable.
    """
    model_path = models_dir / "bkr_fasttext.bin"
    if not model_path.exists():
        return []
    try:
        import fasttext as _ft
    except ImportError:
        return []

    model = _ft.load_model(str(model_path))
    V = min(len(vocab), max_vocab)
    vocab_sub = vocab[:V]

    vecs = np.array(
        [model.get_word_vector(w) for w in vocab_sub],
        dtype=np.float32,
    )
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    vecs = vecs / norms

    sims = (vecs @ vecs.T).astype(float)
    pairs = []
    for i in range(V):
        for j in range(i + 1, V):
            s = float(sims[i, j])
            if s >= min_sim:
                pairs.append((vocab_sub[i], vocab_sub[j], round(s, 4)))
    return sorted(pairs, key=lambda x: x[2], reverse=True)[:top_n]


def export_fasttext_similarities(
    pairs: list[tuple[str, str, float]],
    output_path: Path,
) -> None:
    if not pairs:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["word1", "word2", "cosine_sim"])
        writer.writeheader()
        for w1, w2, s in pairs:
            writer.writerow({"word1": w1, "word2": w2, "cosine_sim": s})


def compute_lsa_embeddings(vocab, ppmi_matrix, n_components=100):
    """
    TruncatedSVD on sparse PPMI matrix → L2-normalised word vectors.
    Returns numpy array of shape (len(vocab), n_components), or None on failure.
    """
    if ppmi_matrix is None or len(vocab) < n_components + 2:
        return None
    k = min(n_components, len(vocab) - 1, ppmi_matrix.shape[1] - 1)
    svd = TruncatedSVD(n_components=k, random_state=42)
    vecs = svd.fit_transform(ppmi_matrix)
    return normalize(vecs, norm="l2")


def export_lsa_similarities(vocab, word_vectors, output_path,
                            top_n=1000, min_sim=0.50, max_vocab=600):
    """
    Export top-N most similar word pairs by cosine similarity from LSA vectors.
    Only the top max_vocab words (by vocab index, already filtered by min_count)
    are compared to keep computation tractable.
    """
    if word_vectors is None or not vocab:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)

    V = min(len(vocab), max_vocab)
    vecs = word_vectors[:V]      # already L2-normalised
    vocab_sub = vocab[:V]

    sims = (vecs @ vecs.T).astype(float)  # V × V cosine similarity

    sim_pairs = []
    for i in range(V):
        for j in range(i + 1, V):
            s = float(sims[i, j])
            if s >= min_sim:
                sim_pairs.append((vocab_sub[i], vocab_sub[j], round(s, 4)))

    sim_pairs.sort(key=lambda x: x[2], reverse=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["word1", "word2", "cosine_sim"])
        writer.writeheader()
        for w1, w2, s in sim_pairs[:top_n]:
            writer.writerow({"word1": w1, "word2": w2, "cosine_sim": s})


# ==========================================================
# R6. MAIN
# ==========================================================

def main():

    rows = load_rows()
    print(f"Loaded rows: {len(rows)}")

    # ── R3: PPMI + PMI² ──────────────────────────────────
    word_counter = compute_word_frequency(rows)
    pair_counter = compute_cooccurrence(rows)
    relations    = compute_ppmi(word_counter, pair_counter, len(rows))

    export_relations(relations, OUTPUT_DIR_PMI / "semantic_relations.csv")
    print(f"\nGlobal PPMI pairs: {len(relations)}")
    print("Top 10 PPMI pairs:")
    for r in relations[:10]:
        print(
            f"  {r['word1']:<20} {r['word2']:<20} "
            f"ppmi={r['ppmi']:>6.3f}  pmi2={r['pmi2']:>7.3f}  n={r['pair_count']}"
        )

    per_type_relations = {}
    for description_type, filename in PER_TYPE_EXPORTS.items():
        type_rels = compute_ppmi_per_type(rows, description_type)
        export_relations(type_rels, OUTPUT_DIR_PMI / filename)
        per_type_relations[description_type] = type_rels
        short = description_type.replace("_statement", "").replace("_relation", "")
        print(f"  {short:<22} {len(type_rels):>5} pairs → {filename}")

    # Build the network from PPMI²-sorted relations (bias-corrected, penalises rare pairs).
    # PPMI² sorts by max(0, PMI + log₂P(x,y)), so rare low-count pairs sink naturally.
    relations_by_ppmi2 = sorted(relations, key=lambda x: x["ppmi2"], reverse=True)
    relations_network = relations_by_ppmi2[:2000]

    # ── R3c: SPARSE PPMI MATRIX ───────────────────────────
    print("\nBuilding sparse PPMI matrix ...")
    vocab, ppmi_matrix = build_ppmi_matrix_from_counters(
        word_counter, pair_counter, len(rows), min_count=5
    )
    print(f"  vocab size: {len(vocab)}  nnz: {ppmi_matrix.nnz if ppmi_matrix is not None else 0}")

    # ── R4: LEGACY WEIGHTED CENTRALITY (backward compat) ─
    centrality = compute_weighted_centrality(relations_network)
    export_centrality_csv(
        centrality,
        OUTPUT_DIR_CENTRALITY / "weighted_semantic_centrality.csv"
    )

    type_map = {
        "theological":    "theological_statement",
        "moral":          "moral_statement",
        "social":         "social_relation",
        "legal":          "legal_normative",
        "ritual":         "ritual_liturgical",
        "prophetic":      "prophetic_announcement",
        "wisdom":         "wisdom_maxim",
        "creation":       "creation_narrative",
        "eschatological": "eschatological",
        "genealogical":   "genealogical_record",
    }
    for type_name, dtype in type_map.items():
        type_rels = per_type_relations.get(dtype, [])[:1000]
        if not type_rels:
            continue
        export_centrality_csv(
            compute_weighted_centrality(type_rels),
            OUTPUT_DIR_CENTRALITY / f"centrality_{type_name}.csv",
        )

    # ── R4b: NETWORKX GRAPH CENTRALITY ───────────────────
    print("\nBuilding NetworkX graph ...")
    G = build_nx_graph(relations_network, weight_field="ppmi")
    print(f"  nodes: {G.number_of_nodes()}  edges: {G.number_of_edges()}")

    print("Computing betweenness + eigenvector centrality ...")
    nx_centrality = compute_nx_centrality(G)
    export_nx_centrality(nx_centrality, OUTPUT_DIR_GRAPH / "nx_centrality.csv")
    print("Top 10 by betweenness:")
    for r in nx_centrality[:10]:
        print(
            f"  {r['word']:<22} btw={r['betweenness_centrality']:.4f} "
            f"eig={r['eigenvector_centrality']:.4f}  deg={r['degree']}"
        )

    # ── R5: LEGACY SEED CLUSTERS (backward compat) ───────
    cluster_edges = assign_clusters(relations_network)
    export_cluster_edges(cluster_edges)
    export_cluster_summary(cluster_edges)
    print("\nConcept clusters:")
    for name, rows in sorted(cluster_edges.items(), key=lambda x: -len(x[1])):
        print(f"  {name:<22} {len(rows):>4} edges")

    # ── R5b: LOUVAIN COMMUNITY DETECTION ─────────────────
    print("\nLouvain community detection ...")
    partition, modularity, n_comm = detect_communities_louvain(G)
    print(f"  communities: {n_comm}  modularity: {modularity:.4f}")
    export_communities(G, partition, OUTPUT_DIR_COMMUNITY / "communities.csv")
    export_community_summary(G, partition, modularity, OUTPUT_DIR_COMMUNITY / "community_summary.csv")

    # ── R6b: GEPHI EXPORT ────────────────────────────────
    print("Exporting Gephi files ...")
    export_gephi_gexf(G, partition, nx_centrality, OUTPUT_DIR_GRAPH / "word_network.gexf")
    export_gephi_csv_edges(G, OUTPUT_DIR_GRAPH / "gephi_edges.csv")
    export_gephi_csv_nodes(G, partition, nx_centrality, OUTPUT_DIR_GRAPH / "gephi_nodes.csv")

    # ── R7: LSA EMBEDDINGS ───────────────────────────────
    print("Computing LSA embeddings (TruncatedSVD on PPMI) ...")
    word_vectors = compute_lsa_embeddings(vocab, ppmi_matrix, n_components=100)
    if word_vectors is not None:
        export_lsa_similarities(
            vocab, word_vectors,
            OUTPUT_DIR_EMBEDDINGS / "lsa_similarities.csv",
        )
        print(f"  word vectors: {word_vectors.shape}  → lsa_similarities.csv")
    else:
        print("  LSA skipped (insufficient vocabulary)")

    # ── R7b: FASTTEXT EMBEDDINGS ─────────────────────────
    from a_paths import MODELS_DIR as _MODELS_DIR
    ft_pairs = compute_fasttext_similarities(vocab, _MODELS_DIR)
    if ft_pairs:
        export_fasttext_similarities(
            ft_pairs, OUTPUT_DIR_EMBEDDINGS / "fasttext_similarities.csv"
        )
        print(f"  FastText pairs: {len(ft_pairs)}  → fasttext_similarities.csv")
    else:
        print("  FastText skipped — run setup_fasttext_model.py to create models/bkr_fasttext.bin")

    print(f"\nDONE")
    print(f"  PMI/PPMI   → {OUTPUT_DIR_PMI}")
    print(f"  Centrality → {OUTPUT_DIR_CENTRALITY}")
    print(f"  Clusters   → {OUTPUT_DIR_CLUSTERS}")
    print(f"  Graph/Gephi→ {OUTPUT_DIR_GRAPH}")
    print(f"  Community  → {OUTPUT_DIR_COMMUNITY}")
    print(f"  Embeddings → {OUTPUT_DIR_EMBEDDINGS}")


if __name__ == "__main__":
    main()
