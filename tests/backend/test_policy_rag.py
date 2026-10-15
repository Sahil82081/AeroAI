"""
Tests for AeroAI Stage 5: Travel Policy RAG System.

Covers:
- Ingestion verification and chunk metadata completeness
- SemanticEmbeddingModel (LSA projection, L2 norm, dimension match)
- Vector store & FAISS IndexFlatIP cosine similarity
- Hybrid search (BM25 + FAISS + RRF + metadata boosts)
- Relevant document retrieval across all 6 core travel-policy domains:
    1. Flight Delays (refreshments, refund, compensation)
    2. Cancellation (advance notice, compensation tiers)
    3. Refund (mandatory refund, 7-day timeline)
    4. Baggage (15kg checked, 7kg cabin, Montreal Convention 1288 SDR)
    5. Rebooking (alternate flight rights)
    6. Passenger Eligibility (PRM wheelchair, denied boarding, name typo fixes)
- Irrelevant questions & Anti-Hallucination refusal
- Missing evidence refusal (out-of-corpus topics e.g. radioactive plutonium)
- Source attribution completeness (document, section, regulator, URL, direct quote)
- Multi-turn conversational memory & query rewriting
- FastAPI endpoints (/api/v1/chat, /api/v1/chat/semantic-search)
"""

import os
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.modules.policies.embedding_model import SemanticEmbeddingModel
from app.modules.policies.policy_rag_service import policy_rag_service

client = TestClient(app)

VECTOR_DIR = Path(__file__).resolve().parents[2] / "data" / "policies" / "vector_store"


# =========================================================================
# 1. INGESTION & VECTOR STORE TESTS
# =========================================================================

def test_ingestion_artifacts_exist():
    """Verifies that all ingestion artifacts and indexes are present on disk."""
    chunks_file = VECTOR_DIR / "policy_chunks.json"
    bm25_file = VECTOR_DIR / "bm25_index.json"
    faiss_file = VECTOR_DIR / "policy_faiss.index"
    model_file = VECTOR_DIR / "embedding_model.joblib"

    assert chunks_file.exists(), f"Missing chunks file at {chunks_file}"
    assert bm25_file.exists(), f"Missing BM25 index at {bm25_file}"
    assert faiss_file.exists(), f"Missing FAISS index at {faiss_file}"
    assert model_file.exists(), f"Missing embedding model at {model_file}"


def test_chunks_metadata_schema():
    """Verifies that each chunk contains complete legal provenance and metadata."""
    chunks_file = VECTOR_DIR / "policy_chunks.json"
    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    assert len(chunks) >= 30, f"Expected at least 30 section chunks, found {len(chunks)}"

    required_keys = [
        "chunk_id", "document_title", "publisher", "regulator",
        "region", "section_title", "page_number", "source_url",
        "effective_date", "text"
    ]
    for c in chunks:
        for k in required_keys:
            assert k in c, f"Missing key '{k}' in chunk {c.get('chunk_id')}"
            assert c[k] is not None, f"Key '{k}' is None in chunk {c.get('chunk_id')}"
        assert len(c["text"].strip()) > 30, f"Chunk {c.get('chunk_id')} text too short"


# =========================================================================
# 2. EMBEDDING MODEL TESTS
# =========================================================================

def test_embedding_model_encode_and_dimensionality():
    """Verifies that SemanticEmbeddingModel produces dense, L2-normalized vectors."""
    model_file = VECTOR_DIR / "embedding_model.joblib"
    model = SemanticEmbeddingModel.load(str(model_file))

    vec = model.encode("flight delayed compensation refreshments")
    assert vec.ndim == 2, "Expected 2D array output"
    assert vec.shape[1] in [37, 38], f"Expected dimension 37 or 38, got {vec.shape[1]}"

    # L2 norm check
    l2_norm = float((vec ** 2).sum())
    assert abs(l2_norm - 1.0) < 1e-4, f"Vector is not L2-normalized: norm={l2_norm}"

    # Batch encoding
    batch = model.encode(["baggage allowance", "refund cancellation"])
    assert batch.shape == (2, vec.shape[1])


# =========================================================================
# 3. RETRIEVAL & HYBRID SEARCH TESTS
# =========================================================================

def test_semantic_faiss_search():
    """Verifies that FAISS nearest-neighbor search executes and returns similarity scores."""
    results = policy_rag_service.search_semantic_faiss("flight delay 4 hours compensation", top_k=5)
    assert len(results) > 0
    top = results[0]
    assert "faiss_similarity_score" in top
    assert top["faiss_similarity_score"] > 0.30
    assert "text" in top


def test_hybrid_search_rrf():
    """Verifies that hybrid search fuses BM25 and FAISS ranks effectively."""
    chunks = policy_rag_service.search_policies(
        query="DGCA CAR Series M Part IV cancellation refund",
        airline="Air India",
        region="India",
        top_k=5
    )
    assert len(chunks) > 0
    for c in chunks:
        assert "rrf_score" in c
        assert "faiss_similarity_score" in c


# =========================================================================
# 4. RELEVANT DOMAIN RETRIEVAL TESTS (6 CORE DOMAINS)
# =========================================================================

@pytest.mark.asyncio
async def test_domain_flight_delays():
    """Domain 1: Flight Delays & Refreshments."""
    res = await policy_rag_service.answer_question(
        "What refreshments or compensation am I entitled to if my flight is delayed by 4 hours?"
    )
    assert res["sufficient_evidence"] is True
    assert res["confidence"] >= 0.90
    assert len(res["citations"]) > 0
    answer = res["answer"].lower()
    assert any(term in answer for term in ["refreshment", "meal", "delay", "hours"])
    assert "disclaimer" in answer


@pytest.mark.asyncio
async def test_domain_cancellation():
    """Domain 2: Flight Cancellation & Advance Notice."""
    res = await policy_rag_service.answer_question(
        "What are my rights if the airline cancels my flight less than 24 hours before departure?"
    )
    assert res["sufficient_evidence"] is True
    assert len(res["citations"]) > 0
    answer = res["answer"].lower()
    assert any(term in answer for term in ["cancel", "compensation", "refund", "inr"])


@pytest.mark.asyncio
async def test_domain_refund():
    """Domain 3: Mandatory Full Refund Timelines."""
    res = await policy_rag_service.answer_question(
        "How many days does an airline have to process a full refund for a cancelled ticket?"
    )
    assert res["sufficient_evidence"] is True
    assert len(res["citations"]) > 0
    answer = res["answer"].lower()
    assert any(term in answer for term in ["refund", "days", "credit card", "7"])


@pytest.mark.asyncio
async def test_domain_baggage():
    """Domain 4: Free Baggage Allowance & Montreal Convention Liability."""
    res = await policy_rag_service.answer_question(
        "What is the standard checked baggage allowance and what is the liability limit for lost luggage?"
    )
    assert res["sufficient_evidence"] is True
    assert len(res["citations"]) > 0
    answer = res["answer"].lower()
    assert any(term in answer for term in ["15 kg", "7 kg", "baggage", "montreal", "sdr"])


@pytest.mark.asyncio
async def test_domain_rebooking():
    """Domain 5: Rebooking & Alternate Transportation."""
    res = await policy_rag_service.answer_question(
        "Am I entitled to free rebooking on an alternate flight if my original flight is cancelled?"
    )
    assert res["sufficient_evidence"] is True
    assert len(res["citations"]) > 0
    answer = res["answer"].lower()
    assert any(term in answer for term in ["rebook", "alternate", "flight", "extra charge"])


@pytest.mark.asyncio
async def test_domain_passenger_eligibility_and_prm():
    """Domain 6: Passenger Eligibility, PRM Wheelchair & Denied Boarding."""
    res = await policy_rag_service.answer_question(
        "What compensation is mandated for involuntary denied boarding and what assistance is provided for wheelchair passengers?"
    )
    assert res["sufficient_evidence"] is True
    assert len(res["citations"]) > 0
    answer = res["answer"].lower()
    assert any(term in answer for term in ["denied boarding", "wheelchair", "volunteers", "reduced mobility", "inr"])


# =========================================================================
# 5. ANTI-HALLUCINATION & EVIDENCE SUFFICIENCY TESTS
# =========================================================================

@pytest.mark.asyncio
async def test_irrelevant_question_anti_hallucination():
    """Tests that completely off-topic questions are rejected with zero citations."""
    queries = [
        "How do I bake chocolate chip cookies?",
        "Who is the current Prime Minister of Australia?",
        "What is the chemical formula for photosynthesis?"
    ]
    for q in queries:
        res = await policy_rag_service.answer_question(q)
        assert res["sufficient_evidence"] is False, f"Expected refusal for: {q}"
        assert res["confidence"] == 0.0
        assert len(res["citations"]) == 0, f"Expected zero citations for irrelevant query: {q}"
        assert "do not have sufficient evidence" in res["answer"]


@pytest.mark.asyncio
async def test_missing_evidence_refusal():
    """Tests that queries containing subjects absent from policy documents are refused."""
    queries = [
        "What is the policy for transporting radioactive plutonium in passenger luggage?",
        "Can I bring my pet iguana on the airplane?",
        "Can I pay for flight tickets using Bitcoin cryptocurrency?"
    ]
    for q in queries:
        res = await policy_rag_service.answer_question(q)
        assert res["sufficient_evidence"] is False, f"Expected refusal for missing evidence: {q}"
        assert len(res["citations"]) == 0
        assert "do not have sufficient evidence" in res["answer"]


# =========================================================================
# 6. SOURCE ATTRIBUTION & CITATION COMPLETENESS TESTS
# =========================================================================

@pytest.mark.asyncio
async def test_source_attribution_completeness():
    """Verifies that citations include document, section, regulator, URL, and direct quote."""
    res = await policy_rag_service.answer_question(
        "What are the rules for flight delays under DGCA regulations in India?"
    )
    assert res["sufficient_evidence"] is True
    assert len(res["citations"]) > 0

    top_cite = res["citations"][0]
    assert "document_title" in top_cite and len(top_cite["document_title"]) > 5
    assert "section" in top_cite and len(top_cite["section"]) > 0
    assert "regulator" in top_cite
    assert "source_url" in top_cite and top_cite["source_url"].startswith("http")
    assert "quote" in top_cite
    assert top_cite["quote"] is not None and len(top_cite["quote"]) > 20


# =========================================================================
# 7. MULTI-TURN CONVERSATION MEMORY TESTS
# =========================================================================

@pytest.mark.asyncio
async def test_multi_turn_conversational_rewrite():
    """Verifies that follow-up turns inherit context entities from previous turns."""
    sid = "test-session-multi-turn-999"
    try:
        # Turn 1: Air India delay
        r1 = await policy_rag_service.answer_question(
            "What is the delay policy for Air India flights?",
            session_id=sid
        )
        assert r1["sufficient_evidence"] is True

        # Turn 2: Follow-up referencing "baggage"
        r2 = await policy_rag_service.answer_question(
            "What about baggage allowance?",
            session_id=sid
        )
        assert r2["sufficient_evidence"] is True
        assert len(r2["citations"]) > 0
        # Should cite baggage rules
        assert any("baggage" in c["section"].lower() or "baggage" in c["document_title"].lower() for c in r2["citations"])
    finally:
        policy_rag_service.clear_session(sid)


# =========================================================================
# 8. FASTAPI ENDPOINT TESTS
# =========================================================================

def test_api_chat_endpoint_relevant():
    """Tests POST /api/v1/chat with a valid policy query."""
    resp = client.post("/api/v1/chat", json={
        "message": "What compensation am I entitled to if my flight is delayed by 4 hours?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["sufficient_evidence"] is True
    assert len(data["citations"]) > 0
    assert "quote" in data["citations"][0]


def test_api_chat_endpoint_irrelevant():
    """Tests POST /api/v1/chat with an irrelevant query."""
    resp = client.post("/api/v1/chat", json={
        "message": "How do I bake chocolate chip cookies?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["sufficient_evidence"] is False
    assert len(data["citations"]) == 0
    assert "do not have sufficient evidence" in data["answer"]


def test_api_semantic_search_endpoint():
    """Tests POST /api/v1/chat/semantic-search for FAISS vector retrieval."""
    resp = client.post("/api/v1/chat/semantic-search", json={
        "query": "flight delay compensation",
        "top_k": 3
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["results_count"] == 3
    assert len(data["results"]) == 3
    for r in data["results"]:
        assert "faiss_similarity_score" in r
