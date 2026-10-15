from langchain_huggingface import HuggingFaceEmbeddings
import os
import pickle
from langchain_community.vectorstores import FAISS
from tools.rag.pdf_to_docs import get_pdf_as_document
from typing import Tuple, List
from langchain_core.documents import Document


def load_faiss(pdf_path: str, embedding_model_name: str='thenlper/gte-small', faiss_path: str="vector_stores/faiss_index") -> Tuple[FAISS, List[str]]:
    embedding_model = HuggingFaceEmbeddings(model_name=embedding_model_name)
    texts_path = faiss_path + "_texts.pkl"

    if os.path.exists(faiss_path):
        with open(texts_path, 'rb') as f:
            pdf_texts = pickle.load(f)
                
        vector_store = FAISS.load_local(faiss_path, embedding_model, allow_dangerous_deserialization=True)
        return vector_store, pdf_texts
    else:
        docs = get_pdf_as_document(pdf_path)
        vector_store = FAISS.from_documents(docs, embedding_model)
        vector_store.save_local(faiss_path)

        pdf_texts = [doc.page_content for doc in docs]
        with open(texts_path, 'wb') as f:
            pickle.dump(pdf_texts, f)
        return vector_store, pdf_texts
    

def search_faiss(vector_store, query: str, top_k=10, metadata_filter=None):
    results_with_score = vector_store.similarity_search_with_score(
        query=query, 
        k=top_k, 
        filter=metadata_filter
    )

    results = []
    for doc, score in results_with_score:
        results.append({
            "text": doc.page_content,
            "score": score,
            "metadata": doc.metadata
        })

    return results