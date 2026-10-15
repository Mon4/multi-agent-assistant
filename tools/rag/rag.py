from functools import lru_cache

from dotenv import load_dotenv
from langfuse import observe
from tools.rag.vector_store_manager import load_faiss, search_faiss
import numpy as np
from typing import List, Dict, Optional
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

load_dotenv()


@lru_cache(maxsize=4)
def _get_retrieval_assets(pdf_path: str, embedding_model_name: str):
    """Load the FAISS index + texts once per (pdf, model) and pre-build the BM25 corpus."""
    faiss_store, pdf_texts = load_faiss(pdf_path, embedding_model_name)
    bm25 = BM25Okapi([doc.split(" ") for doc in pdf_texts])
    return faiss_store, pdf_texts, bm25


@lru_cache(maxsize=1)
def _get_reranker():
    """Load the cross-encoder reranking model once and reuse it."""
    return CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')


def reciprocal_rank_fusion(faiss_results: List[Dict], bm25_results: List[Dict], k: int=100) -> List[str]:
    """Combine rankings from two systems (FAISS i BM25) with RRF."""

    fused_scores: Dict[str, float] = {}
    
    faiss_docs = [res['text'] for res in faiss_results]
    bm25_docs = [res['text'] for res in bm25_results]

    # ranking FAISS (semantic)
    for rank, doc in enumerate(faiss_docs):
        # Użyj dokumentu jako klucza
        if doc not in fused_scores:
            fused_scores[doc] = 0
        fused_scores[doc] += 1 / (rank + 1 + k)

    # ranking BM25 (lexical)
    for rank, doc in enumerate(bm25_docs):
        if doc not in fused_scores:
            fused_scores[doc] = 0
        fused_scores[doc] += 1 / (rank + 1 + k)

    sorted_items = sorted(fused_scores.items(), key=lambda item: item[1], reverse=True)
    sorted_docs = [item[0] for item in sorted_items]

    return sorted_docs


@observe()
def search_with_rag(query: str, pdf_path: str, embedding_model_name: str='thenlper/gte-small', rerank: bool=False, top_k: int=100, 
                          final_context_k_rerank: int=5, hybrid_search: bool=False, metadata_filter: Optional[Dict[str, str]] =None) -> str:
    # 1. RETRIEVAL (FAISS load, embedding model and BM25 corpus come from the cache)
    faiss_store, pdf_texts, bm25 = _get_retrieval_assets(pdf_path, embedding_model_name)
    faiss_results = search_faiss(faiss_store, query, top_k=top_k, metadata_filter=metadata_filter)

    # 1A. SEMANTIC SEARCH - FAISS
    retrieved_docs = [res['text'] for res in faiss_results]
    final_context_docs = []

    if hybrid_search:
        # 1B. LEXICAL (BM25) — tokenized corpus is pre-built in _get_retrieval_assets
        tokenized_query = query.split(" ")
        bm25_scores = bm25.get_scores(tokenized_query)

        # bm25 ranking
        bm25_ranking_indices = np.argsort(bm25_scores)[::-1]
        bm25_results = [{'text': pdf_texts[i]} for i in bm25_ranking_indices[:top_k]]

        # 1C. CONECTING DATA
        retrieved_docs = reciprocal_rank_fusion(faiss_results, bm25_results)

    top_n_docs = retrieved_docs[:100]

    # 2. RERANKING
    if rerank:
        reranker = _get_reranker()
        query_doc_pairs = [[query, doc] for doc in top_n_docs]
        rerank_scores = reranker.predict(query_doc_pairs)
        scored_documents = list(zip(top_n_docs, rerank_scores))
        # sort
        reranked_documents_with_scores = sorted(
            scored_documents,
            key=lambda x: x[1],
            reverse=True)
        final_results = [doc for doc, score in reranked_documents_with_scores]
        # keep only the top N chunks as the final context
        final_context_docs = final_results[:final_context_k_rerank]
    else:
        final_context_docs = top_n_docs[:final_context_k_rerank]

    # 3. CONTEXT FOR LLM 
    context = "\n\n".join(final_context_docs)

    return context