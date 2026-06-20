from pathlib import Path
import csv
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.cluster import KMeans, AgglomerativeClustering, SpectralClustering
from sklearn.decomposition import TruncatedSVD, PCA
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

from a_paths import BIBLE_FOLDER
from n_db import load_rows as _db_load, TABLE_REFINED
from genre_maps import BOOK_GENRES as _GENRE_MAP  # canonical file-keyed map

OUTPUT_DIR = Path("output/style_authorship")

N_CLUSTERS_RANGE = range(3, 11)

# DEAD: presunuté do genre_maps.py — coarser granularity (pentateuch/acts/psalms/...)
# _GENRE_MAP: dict[str, str] = { "bible_BKR_Gn.txt": "pentateuch", ... }


def load_documents():
    """
    Load lemma strings from refined_descriptions DB grouped by file_name.
    Falls back to raw bible text files when the DB table is empty.
    """
    db_rows = _db_load(TABLE_REFINED)

    if db_rows:
        by_file: dict = {}
        for row in db_rows:
            fname  = row.get("file_name", "")
            lemmas = row.get("lemmas", "")
            if not fname:
                continue
            by_file.setdefault(fname, []).append(lemmas)
        return [
            {"file_name": fname, "text": " ".join(parts)}
            for fname, parts in sorted(by_file.items())
        ]

    # fallback: raw text from bible files
    files = sorted(BIBLE_FOLDER.glob("*.txt"))
    if not files:
        raise FileNotFoundError(f"No txt files found: {BIBLE_FOLDER}")
    return [
        {"file_name": f.name, "text": f.read_text(encoding="utf-8")}
        for f in files
    ]


def build_matrix(docs):
    texts = [doc["text"] for doc in docs]
    doc_lengths = [len(t.split()) for t in texts]

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.85,
        max_features=5000,
        sublinear_tf=True,          # log(1+tf) — reduces long-book dominance
        token_pattern=r"(?u)\b[a-zá-ž]{3,}\b",
    )

    matrix = vectorizer.fit_transform(texts)
    return matrix, vectorizer, doc_lengths


def _reduce_dense(matrix, n_components: int = 50) -> np.ndarray:
    """TruncatedSVD → dense array for hierarchical/spectral/t-SNE."""
    k = min(n_components, matrix.shape[0] - 1, matrix.shape[1] - 1)
    return TruncatedSVD(n_components=k, random_state=42).fit_transform(matrix)


# ==========================================================
# X2b. HIERARCHICAL + SPECTRAL CLUSTERING
# ==========================================================

def cluster_hierarchical(reduced: np.ndarray, n_clusters: int) -> np.ndarray:
    """Ward agglomerative clustering on SVD-reduced matrix."""
    return AgglomerativeClustering(
        n_clusters=n_clusters, linkage="ward"
    ).fit_predict(reduced)


def cluster_spectral(reduced: np.ndarray, n_clusters: int) -> np.ndarray:
    """Spectral clustering with cosine affinity on SVD-reduced matrix."""
    try:
        aff = cosine_similarity(reduced)
        aff = np.clip(aff, 0, None)   # cosine can return tiny negatives
        return SpectralClustering(
            n_clusters=n_clusters, affinity="precomputed",
            assign_labels="kmeans", random_state=42,
        ).fit_predict(aff)
    except Exception:
        return np.zeros(len(reduced), dtype=int)


def find_optimal_clusters_all(matrix, reduced: np.ndarray):
    """
    Compare KMeans, Agglomerative (Ward), Spectral across N_CLUSTERS_RANGE.
    Returns best (n, method, labels, score) per method and overall best.
    """
    import warnings
    n_samples = matrix.shape[0]
    if n_samples < 3:
        warnings.warn(f"Too few samples ({n_samples}) for clustering; skipping.")
        return {}, {}
    effective_range = range(N_CLUSTERS_RANGE.start, min(N_CLUSTERS_RANGE.stop, n_samples))

    results: dict = {"kmeans": {}, "hierarchical": {}, "spectral": {}}

    for n in effective_range:
        # KMeans
        km_labels = KMeans(n_clusters=n, random_state=42, n_init=20).fit_predict(matrix)
        results["kmeans"][n] = (silhouette_score(matrix, km_labels), km_labels)

        # Hierarchical
        hi_labels = cluster_hierarchical(reduced, n)
        results["hierarchical"][n] = (silhouette_score(reduced, hi_labels), hi_labels)

        # Spectral
        sp_labels = cluster_spectral(reduced, n)
        if len(set(sp_labels)) > 1:
            results["spectral"][n] = (silhouette_score(reduced, sp_labels), sp_labels)
        else:
            results["spectral"][n] = (-1.0, sp_labels)

    best_per_method = {}
    for method, scores_dict in results.items():
        best_n = max(scores_dict, key=lambda k: scores_dict[k][0])
        best_score, best_labels = scores_dict[best_n]
        best_per_method[method] = (best_n, best_score, best_labels)

    return results, best_per_method


def find_optimal_clusters(matrix):
    import warnings
    n_samples = matrix.shape[0]
    if n_samples < 3:
        warnings.warn(f"Too few samples ({n_samples}) for clustering; skipping.")
        return N_CLUSTERS_RANGE.start, (-1.0, None, None)
    effective_range = range(N_CLUSTERS_RANGE.start, min(N_CLUSTERS_RANGE.stop, n_samples))

    print(f"\n{'n':>4}  {'silhouette':>12}")
    print(f"  {'-'*16}")

    best_n     = effective_range.start
    best_score = -1.0
    scores     = {}

    for n in effective_range:
        model = KMeans(
            n_clusters=n,
            random_state=42,
            n_init=20,
        )
        labels = model.fit_predict(matrix)
        score  = silhouette_score(matrix, labels)
        scores[n] = (score, labels, model)
        marker = "  ←" if score > best_score else ""

        if score > best_score:
            best_score = score
            best_n     = n

        print(f"  {n:>2}    {score:>10.4f}{marker}")

    return best_n, scores[best_n]


def cluster_books(docs, matrix, n_clusters, model):

    file_names = [doc["file_name"] for doc in docs]
    labels = model.labels_
    score  = silhouette_score(matrix, labels)

    return [
        {
            "file_name":       fname,
            "style_cluster":   f"style_{label}",
            "silhouette_score": round(score, 4),
        }
        for fname, label in zip(file_names, labels)
    ]


def get_top_terms(matrix, vectorizer, labels, n_clusters, top_n=10):

    feature_names = vectorizer.get_feature_names_out()
    cluster_terms = []

    for cluster_id in range(n_clusters):
        mask   = labels == cluster_id
        if not mask.any():
            continue
        centroid = matrix[mask].mean(axis=0)
        centroid = np.asarray(centroid).flatten()
        top_idx  = centroid.argsort()[::-1][:top_n]

        for rank, idx in enumerate(top_idx, 1):
            cluster_terms.append({
                "cluster":  f"style_{cluster_id}",
                "rank":     rank,
                "term":     feature_names[idx],
                "tfidf_mean": round(float(centroid[idx]), 5),
            })

    return cluster_terms


def export_clusters_csv(rows):

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / "book_style_clusters.csv"

    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["file_name", "style_cluster", "silhouette_score"]
        )
        writer.writeheader()
        writer.writerows(rows)

    return out


def export_top_terms_csv(cluster_terms):

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / "cluster_top_terms.csv"

    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["cluster", "rank", "term", "tfidf_mean"]
        )
        writer.writeheader()
        writer.writerows(cluster_terms)

    return out


# ==========================================================
# X3. BURROWS' DELTA
# ==========================================================

def burrows_delta(docs: list[dict], n_features: int = 500) -> tuple:
    """
    Burrows' Delta stylometric distance matrix.
    Δ(A,B) = mean_i |z_i(A) − z_i(B)|
    where z_i = (freq_i − mean_i) / std_i  (z-score of relative frequency).

    Returns (delta_matrix, z_matrix, feature_names).
    """
    texts = [doc["text"] for doc in docs]
    cv = CountVectorizer(
        lowercase=True,
        token_pattern=r"(?u)\b[a-zá-ž]{3,}\b",
        max_features=n_features,
        min_df=2,
    )
    raw = cv.fit_transform(texts).toarray().astype(np.float64)

    # Relative frequency (normalize by document length)
    row_sums = raw.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    freq = raw / row_sums

    # Z-score standardisation per feature
    means = freq.mean(axis=0)
    stds  = freq.std(axis=0)
    stds[stds == 0] = 1
    z = (freq - means) / stds  # shape (n_docs, n_features)

    # Vectorised Delta: mean(|z[i] − z[j]|) for all pairs
    z_a = z[:, np.newaxis, :]   # (n, 1, f)
    z_b = z[np.newaxis, :, :]   # (1, n, f)
    delta = np.abs(z_a - z_b).mean(axis=2).astype(np.float32)

    return delta, z, cv.get_feature_names_out()


def export_delta_csv(delta: np.ndarray, book_names: list[str]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    short = [b.replace("bible_BKR_", "").replace(".txt", "") for b in book_names]
    path  = OUTPUT_DIR / "burrows_delta.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["book"] + short)
        writer.writeheader()
        for i, name in enumerate(short):
            writer.writerow({"book": name, **{short[j]: round(float(delta[i, j]), 4)
                                               for j in range(len(short))}})
    return path


def export_nearest_neighbours_csv(delta: np.ndarray, book_names: list[str],
                                   top_n: int = 5) -> Path:
    """Per-book nearest stylistic neighbours by Delta."""
    short  = [b.replace("bible_BKR_", "").replace(".txt", "") for b in book_names]
    path   = OUTPUT_DIR / "delta_neighbours.csv"
    rows   = []
    for i, name in enumerate(short):
        dists = [(delta[i, j], short[j]) for j in range(len(short)) if j != i]
        dists.sort()
        for rank, (d, neighbour) in enumerate(dists[:top_n], 1):
            rows.append({"book": name, "rank": rank,
                         "neighbour": neighbour, "delta": round(float(d), 4)})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["book", "rank", "neighbour", "delta"])
        writer.writeheader()
        writer.writerows(rows)
    return path


# ==========================================================
# X4. PCA / t-SNE VIZUALIZÁCIA
# ==========================================================

def compute_visualization_coords(reduced: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    PCA to 2D + t-SNE to 2D from SVD-reduced matrix.
    Returns (pca_2d, tsne_2d) arrays of shape (n_docs, 2).
    """
    pca2 = PCA(n_components=2, random_state=42).fit_transform(reduced)

    perplexity = min(30, max(2, len(reduced) // 4))
    tsne2 = TSNE(
        n_components=2, perplexity=perplexity,
        learning_rate="auto", init="pca", random_state=42,
    ).fit_transform(reduced)

    return pca2, tsne2


def export_visualization_csv(
    docs: list[dict],
    doc_lengths: list[int],
    pca2: np.ndarray,
    tsne2: np.ndarray,
    labels_kmeans: np.ndarray,
    labels_hierarchical: np.ndarray,
) -> Path:
    path = OUTPUT_DIR / "visualization_coords.csv"
    rows = []
    for i, doc in enumerate(docs):
        fname = doc["file_name"]
        rows.append({
            "file_name":           fname,
            "short_name":          fname.replace("bible_BKR_", "").replace(".txt", ""),
            "genre":               _GENRE_MAP.get(fname, "unknown"),
            "doc_length_tokens":   doc_lengths[i],
            "cluster_kmeans":      int(labels_kmeans[i]),
            "cluster_hierarchical": int(labels_hierarchical[i]),
            "pc1":  round(float(pca2[i, 0]),  4),
            "pc2":  round(float(pca2[i, 1]),  4),
            "tsne1": round(float(tsne2[i, 0]), 4),
            "tsne2": round(float(tsne2[i, 1]), 4),
        })
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def export_cluster_comparison_csv(
    docs: list[dict],
    best_per_method: dict,
) -> Path:
    """One row per book: cluster assignment from each method."""
    fname_to_idx = {doc["file_name"]: i for i, doc in enumerate(docs)}
    path = OUTPUT_DIR / "cluster_comparison.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "file_name", "genre",
            "kmeans_cluster", "kmeans_score",
            "hierarchical_cluster", "hierarchical_score",
            "spectral_cluster", "spectral_score",
        ])
        writer.writeheader()
        for fname, i in sorted(fname_to_idx.items()):
            writer.writerow({
                "file_name": fname,
                "genre": _GENRE_MAP.get(fname, "unknown"),
                "kmeans_cluster":       int(best_per_method["kmeans"][2][i]),
                "kmeans_score":         round(best_per_method["kmeans"][1], 4),
                "hierarchical_cluster": int(best_per_method["hierarchical"][2][i]),
                "hierarchical_score":   round(best_per_method["hierarchical"][1], 4),
                "spectral_cluster":     int(best_per_method["spectral"][2][i]),
                "spectral_score":       round(best_per_method["spectral"][1], 4),
            })
    return path


def main():

    docs = load_documents()
    print(f"Loaded books: {len(docs)}")

    matrix, vectorizer, doc_lengths = build_matrix(docs)
    print(f"  TF-IDF matrix: {matrix.shape}  (sublinear_tf=True, max_features=5000)")
    print(f"  Doc lengths:   min={min(doc_lengths)}  max={max(doc_lengths)}  "
          f"median={sorted(doc_lengths)[len(doc_lengths)//2]}")

    # SVD reduction for dense-input methods
    reduced = _reduce_dense(matrix, n_components=50)

    # ── KMeans (baseline, kept for backward compat) ───────
    best_n, (best_score, best_labels, best_model) = find_optimal_clusters(matrix)
    print(f"\nKMeans optimal n={best_n}  silhouette={best_score:.4f}")

    rows = cluster_books(docs, matrix, best_n, best_model)
    export_clusters_csv(rows)

    cluster_terms = get_top_terms(matrix, vectorizer, best_labels, best_n, top_n=10)
    export_top_terms_csv(cluster_terms)

    print("Top 5 terms per KMeans cluster:")
    current = None
    for r in cluster_terms:
        if r["cluster"] != current:
            current = r["cluster"]
            print(f"  [{current}]")
        if r["rank"] <= 5:
            print(f"    {r['rank']}. {r['term']:<30} {r['tfidf_mean']:.5f}")

    # ── All methods comparison ─────────────────────────────
    print(f"\nComparing KMeans / Agglomerative / Spectral ...")
    all_results, best_per_method = find_optimal_clusters_all(matrix, reduced)

    print(f"\n  {'Method':<16} {'best n':>7}  {'silhouette':>12}")
    for method, (best_n_m, best_s_m, _) in best_per_method.items():
        print(f"  {method:<16} {best_n_m:>7}  {best_s_m:>12.4f}")

    export_cluster_comparison_csv(docs, best_per_method)

    # ── Burrows' Delta ─────────────────────────────────────
    print(f"\nComputing Burrows' Delta (n_features=500) ...")
    book_names = [doc["file_name"] for doc in docs]
    delta, z_matrix, feat_names = burrows_delta(docs, n_features=500)
    export_delta_csv(delta, book_names)
    export_nearest_neighbours_csv(delta, book_names)

    # Most "average" style (lowest mean Delta) vs. most "outlier"
    mean_deltas = delta.mean(axis=1)
    avg_idx = int(np.argmin(mean_deltas))
    out_idx = int(np.argmax(mean_deltas))
    short = lambda n: n.replace("bible_BKR_", "").replace(".txt", "")
    print(f"  Most average style:  {short(book_names[avg_idx])}  "
          f"(mean Δ={mean_deltas[avg_idx]:.3f})")
    print(f"  Most outlier style:  {short(book_names[out_idx])}  "
          f"(mean Δ={mean_deltas[out_idx]:.3f})")

    # ── PCA / t-SNE ───────────────────────────────────────
    print(f"\nComputing PCA + t-SNE ...")
    pca2, tsne2 = compute_visualization_coords(reduced)
    viz_path = export_visualization_csv(
        docs, doc_lengths, pca2, tsne2,
        best_per_method["kmeans"][2],
        best_per_method["hierarchical"][2],
    )
    print(f"  Visualization coords → {viz_path.name}")

    print(f"\nDONE — Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
