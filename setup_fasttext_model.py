"""
setup_fasttext_model.py — Download OPUS Bible corpus and train BKR FastText model.

Default (train from scratch, fast, domain-adapted):
    python3 setup_fasttext_model.py

Fine-tune from cc.cs.300.bin (7 GB download, better coverage of modern Czech):
    python3 setup_fasttext_model.py --pretrained

Output: models/bkr_fasttext.bin
"""

from __future__ import annotations

import sys
import gzip
import shutil
import urllib.request
from pathlib import Path

from a_paths import DATA_DIR, MODELS_DIR

CORPUS_DIR   = DATA_DIR / "fasttext_corpus"
MODEL_OUTPUT = MODELS_DIR / "bkr_fasttext.bin"
CC_CS_BIN    = MODELS_DIR / "cc.cs.300.bin"
CC_CS_URL    = "https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.cs.300.bin.gz"

# OPUS Bible monolingual texts (verse-per-line) — multiple URL variants to try
# The Pouta CSC object storage URL structure changes between versions.
_OPUS_URL_TEMPLATES = [
    "https://object.pouta.csc.fi/OPUS-Bible-uedin/v1/mono/{lang}.txt.gz",
    "https://object.pouta.csc.fi/OPUS-bible-uedin/v1/mono/{lang}.txt.gz",
    "https://opus.nlpl.eu/download.php?f=Bible-uedin%2Fv1%2Fmono%2F{lang}.txt.gz",
]

OPUS_URLS: dict[str, str] = {
    lang: _OPUS_URL_TEMPLATES[0].format(lang=lang)
    for lang in ("cs", "sk", "en")
}


# ==========================================================
# DOWNLOAD HELPERS
# ==========================================================

def _download(url: str, dest: Path, desc: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading {desc} ...", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp, dest.open("wb") as f:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk = 1 << 20  # 1 MB
        while True:
            data = resp.read(chunk)
            if not data:
                break
            f.write(data)
            downloaded += len(data)
            if total:
                pct = downloaded * 100 // total
                print(f"\r    {pct:>3}%  {downloaded >> 20} MB / {total >> 20} MB",
                      end="", flush=True)
    print(f"\r  Saved → {dest}  ({dest.stat().st_size >> 20} MB)")


def _try_download(url: str, dest: Path, desc: str) -> bool:
    """Try downloading from url; return True on success, False on any error."""
    try:
        _download(url, dest, desc)
        return True
    except Exception as e:
        print(f"  [fail] {e}")
        if dest.exists():
            dest.unlink()
        return False


def download_opus(langs: tuple[str, ...] = ("cs", "sk")) -> list[Path]:
    """
    Download OPUS Bible monolingual texts.  Tries multiple URL variants per
    language; silently skips languages that are unavailable.
    """
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for lang in langs:
        txt_path = CORPUS_DIR / f"opus_bible_{lang}.txt"
        if txt_path.exists():
            n = sum(1 for _ in txt_path.open(encoding="utf-8"))
            print(f"  [skip] {txt_path.name} ({n} lines)")
            paths.append(txt_path)
            continue

        gz_path = CORPUS_DIR / f"opus_bible_{lang}.txt.gz"
        ok = False
        for tmpl in _OPUS_URL_TEMPLATES:
            url = tmpl.format(lang=lang)
            print(f"  Trying {url[:60]}...")
            if _try_download(url, gz_path, f"OPUS Bible {lang.upper()}"):
                ok = True
                break

        if not ok:
            print(f"  [skip] OPUS {lang.upper()} unavailable — continuing without it")
            continue

        print(f"  Decompressing {gz_path.name} ...", end=" ", flush=True)
        with gzip.open(gz_path, "rt", encoding="utf-8") as fin, \
             txt_path.open("w", encoding="utf-8") as fout:
            shutil.copyfileobj(fin, fout)
        gz_path.unlink()
        n = sum(1 for _ in txt_path.open(encoding="utf-8"))
        print(f"{n} lines")
        paths.append(txt_path)
    return paths


# ==========================================================
# BKR TEXT EXPORT (from DB or bible_files)
# ==========================================================

def export_bkr_text() -> Path:
    bkr_path = CORPUS_DIR / "bkr_lemmas.txt"
    if bkr_path.exists():
        n = sum(1 for _ in bkr_path.open(encoding="utf-8"))
        print(f"  [skip] {bkr_path.name} ({n} lines)")
        return bkr_path

    print("  Exporting BKR lemmas from DB ...", flush=True)
    try:
        from n_db import load_rows, TABLE_REFINED
        rows = load_rows(TABLE_REFINED)
        with bkr_path.open("w", encoding="utf-8") as f:
            for row in rows:
                lemmas = row.get("lemmas", "").strip()
                if lemmas:
                    f.write(lemmas + "\n")
        print(f"  Saved {len(rows)} lines → {bkr_path}")
    except Exception as e:
        print(f"  DB unavailable ({e}); falling back to bible_files")
        from a_paths import list_bible_files
        n = 0
        with bkr_path.open("w", encoding="utf-8") as f:
            for txt in list_bible_files():
                for line in txt.open(encoding="utf-8"):
                    line = line.strip()
                    if line:
                        f.write(line + "\n")
                        n += 1
        print(f"  Saved {n} lines (raw text) → {bkr_path}")
    return bkr_path


# ==========================================================
# CORPUS ASSEMBLY
# ==========================================================

def combine_corpus(paths: list[Path]) -> Path:
    combined = CORPUS_DIR / "combined_bkr_opus.txt"
    total = 0
    with combined.open("w", encoding="utf-8") as fout:
        for p in paths:
            n = 0
            with p.open(encoding="utf-8") as fin:
                for line in fin:
                    fout.write(line)
                    n += 1
            total += n
            print(f"    + {p.name:<35} {n:>7} lines")
    print(f"  Combined corpus: {total} lines → {combined}")
    return combined


# ==========================================================
# FASTTEXT TRAINING
# ==========================================================

def download_pretrained_czech() -> Path:
    if CC_CS_BIN.exists():
        print(f"  [skip] {CC_CS_BIN.name} ({CC_CS_BIN.stat().st_size >> 20} MB)")
        return CC_CS_BIN
    gz_path = MODELS_DIR / "cc.cs.300.bin.gz"
    _download(CC_CS_URL, gz_path, "cc.cs.300.bin (FastText pretrained Czech, ~2.5 GB compressed)")
    print("  Decompressing (~7 GB) ...", flush=True)
    with gzip.open(gz_path, "rb") as fin, CC_CS_BIN.open("wb") as fout:
        shutil.copyfileobj(fin, fout)
    gz_path.unlink()
    print(f"  Done: {CC_CS_BIN} ({CC_CS_BIN.stat().st_size >> 20} MB)")
    return CC_CS_BIN


def _export_pretrained_vectors(pretrained_bin: Path, out_vec: Path, max_words: int = 200_000) -> None:
    if out_vec.exists():
        print(f"  [skip] {out_vec.name}")
        return
    print(f"  Exporting top-{max_words} pretrained vectors to .vec ...", flush=True)
    import fasttext
    pre = fasttext.load_model(str(pretrained_bin))
    words = pre.words[:max_words]
    with out_vec.open("w", encoding="utf-8") as f:
        f.write(f"{len(words)} 300\n")
        for w in words:
            vec = " ".join(f"{v:.6f}" for v in pre.get_word_vector(w))
            f.write(f"{w} {vec}\n")
    print(f"  Saved: {out_vec}")


def train_fasttext(corpus_path: Path, pretrained_bin: Path | None = None) -> None:
    import fasttext

    kwargs: dict = dict(
        input=str(corpus_path),
        model="skipgram",
        dim=300,
        ws=5,
        epoch=10,
        minCount=2,
        minn=2,
        maxn=5,
        thread=4,
        verbose=2,
    )

    if pretrained_bin and pretrained_bin.exists():
        vec_path = MODELS_DIR / "cc.cs_subset.vec"
        _export_pretrained_vectors(pretrained_bin, vec_path)
        kwargs["pretrainedVectors"] = str(vec_path)
        print(f"  Fine-tuning from pretrained vectors: {vec_path}")
    else:
        print("  Training from scratch (skipgram, dim=300, epoch=10)")

    print(f"  Corpus: {corpus_path}", flush=True)
    model = fasttext.train_unsupervised(**kwargs)
    model.save_model(str(MODEL_OUTPUT))

    print(f"\n  Model saved: {MODEL_OUTPUT}")
    print(f"  Vocabulary:  {len(model.words)} words")
    # Quick sanity check
    for w in ["bůh", "hospodin", "zákon", "duch", "království"]:
        try:
            nn = model.get_nearest_neighbors(w, k=3)
            print(f"  nn({w}): {[x[1] for x in nn]}")
        except Exception:
            pass


# ==========================================================
# MAIN
# ==========================================================

def main() -> None:
    pretrained_mode = "--pretrained" in sys.argv
    langs = ("cs", "sk") if "--en" not in sys.argv else ("cs", "sk", "en")

    print("=== BKR FastText Model Setup ===")
    print(f"  Mode  : {'fine-tune from cc.cs.300.bin' if pretrained_mode else 'train from scratch'}")
    print(f"  OPUS  : {', '.join(l.upper() for l in langs)}")
    print(f"  Output: {MODEL_OUTPUT}\n")

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    print("[1] OPUS Bible corpus")
    opus_paths = download_opus(langs=langs)

    print("\n[2] BKR lemma text")
    bkr_path = export_bkr_text()

    print("\n[3] Combining corpus")
    combined = combine_corpus([bkr_path] + opus_paths)

    pretrained_bin = None
    if pretrained_mode:
        print("\n[4] Pretrained Czech FastText (cc.cs.300.bin)")
        pretrained_bin = download_pretrained_czech()

    print("\n[5] Training FastText model")
    train_fasttext(combined, pretrained_bin)

    print("\nSetup complete.")
    print("Run k_apply_all_to_bible.py to regenerate DB with embedding_cluster field.")


if __name__ == "__main__":
    main()
