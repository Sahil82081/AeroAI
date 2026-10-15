"""
Semantic Dense Embedding Model for AeroAI Travel Policy RAG.
Implements Latent Semantic Analysis (LSA) dense projection:
Subword/Word N-Gram TF-IDF -> TruncatedSVD -> L2 Normalized Dense Vector.

Provides:
- Fast sub-millisecond query embedding (< 1ms)
- Dense continuous semantic space capturing synonyms and domain concepts
- Zero external network dependencies (no HuggingFace/PyTorch hang risks)
- Exact cosine similarity via FAISS IndexFlatIP
"""

import re
from pathlib import Path
from typing import List, Union, Optional
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

from app.core.logger import logger

MODULE_DIR = Path(__file__).resolve().parent
REPO_ROOT = MODULE_DIR.parents[3]
DEFAULT_MODEL_PATH = REPO_ROOT / "data" / "policies" / "vector_store" / "embedding_model.joblib"


class SemanticEmbeddingModel:
    """Dense Latent Semantic embedding model for policy document search."""

    def __init__(self, n_components: int = 64):
        self.n_components = n_components
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.svd: Optional[TruncatedSVD] = None
        self.is_fitted = False

    def fit(self, texts: List[str]) -> "SemanticEmbeddingModel":
        """Fits TF-IDF and SVD latent semantic subspace on the policy text corpus."""
        if not texts:
            raise ValueError("Cannot fit SemanticEmbeddingModel on empty text corpus.")

        logger.info(f"Fitting SemanticEmbeddingModel on {len(texts)} document chunks...")
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1,
            max_df=0.95,
            stop_words="english",
            token_pattern=r"(?u)\b[a-zA-Z0-9_\-\.]{2,}\b"
        )
        tfidf_mat = self.vectorizer.fit_transform(texts)

        # Dimension bounded by vocabulary and chunk count
        max_components = min(self.n_components, len(texts) - 1, tfidf_mat.shape[1] - 1)
        actual_components = max(4, max_components)

        self.svd = TruncatedSVD(n_components=actual_components, random_state=42)
        self.svd.fit(tfidf_mat)
        self.is_fitted = True
        logger.info(f"Fitted SemanticEmbeddingModel with {actual_components} latent semantic components.")
        return self

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Encodes one or more texts into L2-normalized dense float32 vectors.
        Returns array of shape (N, dim).
        """
        if not self.is_fitted or self.vectorizer is None or self.svd is None:
            raise RuntimeError("SemanticEmbeddingModel must be fitted or loaded before calling encode().")

        if isinstance(texts, str):
            input_list = [texts]
        else:
            input_list = list(texts)

        if not input_list:
            return np.empty((0, self.svd.n_components), dtype=np.float32)

        tfidf = self.vectorizer.transform(input_list)
        dense = self.svd.transform(tfidf)
        dense_norm = normalize(dense, norm="l2", axis=1).astype(np.float32)
        return dense_norm

    def save(self, filepath: Optional[Union[str, Path]] = None):
        """Saves fitted vectorizer and SVD transform to disk."""
        target_path = Path(filepath) if filepath else DEFAULT_MODEL_PATH
        target_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "vectorizer": self.vectorizer,
            "svd": self.svd,
            "n_components": self.svd.n_components if self.svd else self.n_components,
            "is_fitted": self.is_fitted,
        }, target_path)
        logger.info(f"Saved SemanticEmbeddingModel to {target_path}")

    @classmethod
    def load(cls, filepath: Optional[Union[str, Path]] = None) -> "SemanticEmbeddingModel":
        """Loads fitted embedding model from disk."""
        target_path = Path(filepath) if filepath else DEFAULT_MODEL_PATH
        if not target_path.exists():
            raise FileNotFoundError(f"Embedding model file not found at {target_path}")

        data = joblib.load(target_path)
        instance = cls(n_components=data.get("n_components", 64))
        instance.vectorizer = data["vectorizer"]
        instance.svd = data["svd"]
        instance.is_fitted = data["is_fitted"]
        logger.info(f"Loaded SemanticEmbeddingModel from {target_path} (dim={instance.svd.n_components})")
        return instance
