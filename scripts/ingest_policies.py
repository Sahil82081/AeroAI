#!/usr/bin/env python3
"""
Official Airline Policy Ingestion Pipeline (Enhanced Stage 5 RAG).

1. Parses raw policy documents from data/policies/raw/ (Text, HTML, PDF).
2. Performs section-aware semantic chunking on regulatory articles and clauses.
3. Attaches rich metadata:
   - document title, publisher, regulator, region, airline
   - section title & clause headings
   - source URL & effective date
4. Trains and computes dense Latent Semantic Analysis (LSA) continuous embeddings (64-dim).
5. Builds persistent FAISS IndexFlatIP (cosine similarity) and BM25 inverted index on disk.
6. Saves embedding model to data/policies/vector_store/embedding_model.joblib.
7. Tracks SHA-256 hashes for idempotency.
"""

import os
import sys
import re
import json
import math
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import pypdf

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

RAW_DIR = BASE_DIR / "data" / "policies" / "raw"
VECTOR_DIR = BASE_DIR / "data" / "policies" / "vector_store"
SOURCES_MANIFEST_PATH = BASE_DIR / "data" / "policies" / "sources.json"
INGESTION_MANIFEST_PATH = BASE_DIR / "data" / "policies" / "ingestion_manifest.json"

VECTOR_DIR.mkdir(parents=True, exist_ok=True)

from app.modules.policies.embedding_model import SemanticEmbeddingModel


def compute_file_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file for idempotency checking."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def clean_text(text: str) -> str:
    """Clean extraneous headers, whitespace, and formatting artifacts."""
    if not text:
        return ""
    text = text.replace("\u00a0", " ").replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        # Drop standalone page numbers or separator lines
        if re.match(r"^(?:page\s*\d+(?:\s*(?:of|\/)\s*\d+)?|\d+|[-=_\s]{4,})$", stripped, re.IGNORECASE):
            continue
        lines.append(line)
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def parse_document_text(filepath: Path) -> str:
    """Extracts raw text based on file format with HTML/PDF cleanup."""
    suffix = filepath.suffix.lower()
    if suffix in [".txt", ".md"]:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return clean_text(f.read())
    elif suffix in [".html", ".htm"]:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        return clean_text(soup.get_text(separator="\n"))
    elif suffix == ".pdf":
        text_parts = []
        try:
            reader = pypdf.PdfReader(str(filepath))
            for page in reader.pages:
                t = page.extract_text() or ""
                if t:
                    text_parts.append(t)
        except Exception as e:
            print(f"  [PDF ERROR] {filepath.name}: {e}")
        return clean_text("\n\n".join(text_parts))
    return ""


def extract_header_metadata(full_text: str) -> Dict[str, str]:
    """Extracts explicit metadata block if present at top of document."""
    meta = {}
    lines = full_text.split("\n")
    for line in lines[:15]:
        line_clean = line.strip()
        if line_clean.startswith("OFFICIAL POLICY DOCUMENT:"):
            meta["title"] = line_clean.replace("OFFICIAL POLICY DOCUMENT:", "").strip()
        elif line_clean.startswith("PUBLISHER:"):
            meta["publisher"] = line_clean.replace("PUBLISHER:", "").strip()
        elif line_clean.startswith("REGULATOR/AIRLINE:"):
            meta["regulator"] = line_clean.replace("REGULATOR/AIRLINE:", "").strip()
        elif line_clean.startswith("REGION:"):
            meta["region"] = line_clean.replace("REGION:", "").strip()
        elif line_clean.startswith("OFFICIAL URL:"):
            meta["source_url"] = line_clean.replace("OFFICIAL URL:", "").strip()
        elif line_clean.startswith("EFFECTIVE DATE:"):
            meta["effective_date"] = line_clean.replace("EFFECTIVE DATE:", "").strip()
    return meta


def chunk_document_by_sections(
    doc_id: str,
    full_text: str,
    meta_lookup: Dict[str, Any],
    filepath: Path,
) -> List[Dict[str, Any]]:
    """
    Performs section-aware semantic chunking.
    Splits along numbered articles/sections (e.g. '1. DENIED BOARDING', '2. CANCELLATION')
    so each clause is stored as an independent semantic search target.
    """
    extracted_meta = extract_header_metadata(full_text)
    doc_meta = meta_lookup.get(filepath.name, {}) or meta_lookup.get(filepath.stem, {})

    title = extracted_meta.get("title") or doc_meta.get("title") or filepath.stem.replace("_", " ").title()
    publisher = extracted_meta.get("publisher") or doc_meta.get("publisher", "Civil Aviation Authority")
    regulator = extracted_meta.get("regulator") or doc_meta.get("regulator", "Civil Aviation Authority")
    region = extracted_meta.get("region") or doc_meta.get("region", "Global")
    airline = doc_meta.get("airline", "All Airlines")
    source_url = extracted_meta.get("source_url") or doc_meta.get("url", "https://www.dgca.gov.in")
    effective_date = extracted_meta.get("effective_date") or doc_meta.get("effective_date", "Current")

    # Strip header metadata lines to avoid repetitive noise
    body_lines = []
    in_header = True
    for line in full_text.split("\n"):
        if in_header:
            if any(line.strip().startswith(prefix) for prefix in [
                "OFFICIAL POLICY DOCUMENT:", "PUBLISHER:", "REGULATOR/AIRLINE:",
                "REGION:", "OFFICIAL URL:", "EFFECTIVE DATE:", "VERIFIED SOURCE STATUS:"
            ]):
                continue
            if not line.strip():
                continue
            in_header = False
        body_lines.append(line)
    body_text = "\n".join(body_lines).strip()

    # Split on numbered section headers e.g. "1. DENIED BOARDING", "2. CANCELLATION OF FLIGHTS"
    section_pattern = r"(?m)(?=^[0-9]+\.\s+[A-Z])"
    raw_sections = re.split(section_pattern, body_text)

    # Filter empty sections
    sections = [s.strip() for s in raw_sections if s.strip()]
    if not sections:
        sections = [body_text]

    chunks = []
    for s_idx, sec in enumerate(sections):
        lines = sec.split("\n")
        first_line = lines[0].strip()

        # Identify section title
        if re.match(r"^[0-9]+\.\s+", first_line):
            sec_title = first_line.rstrip(":").strip()
        else:
            sec_title = first_line[:70].strip() or f"Section {s_idx + 1}"

        # If a single section is very long (> 500 words), sub-chunk by paragraph
        words = sec.split()
        if len(words) > 500:
            sub_chunks = []
            current = []
            for p in sec.split("\n\n"):
                p_w = p.split()
                if len(current) + len(p_w) <= 350:
                    current.extend(p_w)
                else:
                    if current:
                        sub_chunks.append(" ".join(current))
                    current = p_w[-50:] + p_w
            if current:
                sub_chunks.append(" ".join(current))
        else:
            sub_chunks = [sec]

        for sub_idx, sub_content in enumerate(sub_chunks):
            cid = f"{doc_id}_s{s_idx + 1}"
            if len(sub_chunks) > 1:
                cid += f"_p{sub_idx + 1}"

            chunks.append({
                "chunk_id": cid,
                "document_title": title,
                "publisher": publisher,
                "regulator": regulator,
                "region": region,
                "airline": airline,
                "section_title": sec_title,
                "page_number": s_idx + 1,
                "source_url": source_url,
                "effective_date": effective_date,
                "text": sub_content,
                "token_estimate": len(sub_content.split()),
                "file_path": str(filepath.relative_to(BASE_DIR)).replace("\\", "/")
            })

    return chunks


def build_bm25_index(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Constructs an inverted BM25 index over chunk tokens for exact keyword recall."""
    doc_freqs: Dict[str, int] = {}
    doc_lengths: List[int] = []
    inverted_index: Dict[str, List[Dict[str, Any]]] = {}

    for doc_idx, chunk in enumerate(chunks):
        tokens = re.findall(r"\b\w{2,}\b", chunk["text"].lower())
        doc_lengths.append(len(tokens))
        term_counts: Dict[str, int] = {}
        for t in tokens:
            term_counts[t] = term_counts.get(t, 0) + 1

        for term, count in term_counts.items():
            doc_freqs[term] = doc_freqs.get(term, 0) + 1
            if term not in inverted_index:
                inverted_index[term] = []
            inverted_index[term].append({
                "doc_idx": doc_idx,
                "tf": count
            })

    total_docs = len(chunks)
    avg_dl = sum(doc_lengths) / max(1, total_docs)

    return {
        "total_docs": total_docs,
        "avg_dl": avg_dl,
        "doc_lengths": doc_lengths,
        "doc_freqs": doc_freqs,
        "inverted_index": inverted_index
    }


def ingest_all_policies(force: bool = False) -> Dict[str, Any]:
    """
    Main ingestion execution:
    1. Parses and chunks raw documents with section awareness.
    2. Fits SemanticEmbeddingModel on chunk corpus.
    3. Builds persistent FAISS semantic index and BM25 index on disk.
    """
    print("=" * 70)
    print("AEROAI: STAGE 5 TRAVEL POLICY RAG INGESTION PIPELINE")
    print(f"Raw Documents Directory: {RAW_DIR}")
    print(f"Vector Store Directory:  {VECTOR_DIR}")
    print("=" * 70)

    # 1. Load Sources Manifest
    metadata_lookup: Dict[str, Any] = {}
    if SOURCES_MANIFEST_PATH.exists():
        try:
            with open(SOURCES_MANIFEST_PATH, "r", encoding="utf-8") as f:
                sources_data = json.load(f)
            for s in sources_data.get("sources", []):
                fname = s.get("file_name")
                if fname:
                    metadata_lookup[fname] = s
                    metadata_lookup[Path(fname).stem] = s
                metadata_lookup[s.get("id")] = s
        except Exception as e:
            print(f"Warning: could not read sources manifest: {e}")

    # 2. Discover raw files
    raw_files = sorted([f for f in RAW_DIR.glob("*") if f.is_file() and f.suffix.lower() in [".txt", ".md", ".pdf", ".html"]])
    print(f"Found {len(raw_files)} policy documents in raw folder.\n")

    all_chunks: List[Dict[str, Any]] = []
    current_hashes: Dict[str, str] = {}

    for file_path in raw_files:
        f_hash = compute_file_sha256(file_path)
        current_hashes[file_path.name] = f_hash

        text = parse_document_text(file_path)
        if not text:
            print(f"  [SKIP EMPTY] {file_path.name}")
            continue

        doc_chunks = chunk_document_by_sections(
            doc_id=file_path.stem,
            full_text=text,
            meta_lookup=metadata_lookup,
            filepath=file_path
        )
        print(f"  Processed {file_path.name:<35} -> {len(doc_chunks)} section chunks")
        all_chunks.extend(doc_chunks)

    print(f"\nTotal policy section chunks generated: {len(all_chunks)}")

    # 3. Fit SemanticEmbeddingModel
    print("\nFitting Latent Semantic Analysis (LSA) dense embedding model...")
    all_texts = [c["text"] for c in all_chunks]
    embedding_model = SemanticEmbeddingModel(n_components=64)
    embedding_model.fit(all_texts)
    embedding_model.save(VECTOR_DIR / "embedding_model.joblib")

    # 4. Generate dense vectors for all chunks
    print("Encoding chunks into continuous L2-normalized float32 vectors...")
    dense_vectors = embedding_model.encode(all_texts)
    for idx, c in enumerate(all_chunks):
        c["vector"] = dense_vectors[idx].tolist()

    # 5. Build FAISS IndexFlatIP
    print("Building persistent FAISS Semantic Vector Index (IndexFlatIP)...")
    import faiss
    import numpy as np

    dim = dense_vectors.shape[1]
    faiss_index = faiss.IndexFlatIP(dim)
    faiss_index.add(dense_vectors)
    faiss_store_path = VECTOR_DIR / "policy_faiss.index"
    faiss.write_index(faiss_index, str(faiss_store_path))
    print(f"  FAISS Index written: {faiss_store_path} ({faiss_index.ntotal} vectors, dim={dim})")

    # 6. Build BM25 Inverted Index
    print("Building BM25 Inverted Index...")
    bm25_index = build_bm25_index(all_chunks)
    bm25_store_path = VECTOR_DIR / "bm25_index.json"
    with open(bm25_store_path, "w", encoding="utf-8") as f:
        json.dump(bm25_index, f)
    print(f"  BM25 Index written:  {bm25_store_path} ({bm25_index['total_docs']} documents)")

    # 7. Save Chunks JSON (without raw vector to keep JSON lightweight)
    chunks_store_path = VECTOR_DIR / "policy_chunks.json"
    clean_chunks = []
    for c in all_chunks:
        clean_c = dict(c)
        # Keep vector in memory for services that need direct dot products
        clean_chunks.append(clean_c)

    with open(chunks_store_path, "w", encoding="utf-8") as f:
        json.dump(clean_chunks, f, indent=2)
    print(f"  Policy Chunks Store: {chunks_store_path}")

    # 8. Save Ingestion Manifest
    ingest_manifest_data = {
        "last_ingested_at": datetime.now(timezone.utc).isoformat(),
        "total_files": len(raw_files),
        "total_chunks": len(all_chunks),
        "embedding_model": "SemanticEmbeddingModel (TF-IDF LSA TruncatedSVD)",
        "embedding_dim": dim,
        "vector_index": "FAISS IndexFlatIP (Cosine Similarity)",
        "keyword_index": "BM25 (Robertson-Sparck Jones IDF)",
        "file_hashes": current_hashes
    }
    with open(INGESTION_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(ingest_manifest_data, f, indent=2)

    print("\n" + "=" * 70)
    print(f"STAGE 5 INGESTION COMPLETE ✓ ({len(all_chunks)} chunks indexed)")
    print("=" * 70)
    return ingest_manifest_data


if __name__ == "__main__":
    force_flag = "--force" in sys.argv
    ingest_all_policies(force=force_flag)
