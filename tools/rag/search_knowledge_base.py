from google.adk.tools.function_tool import FunctionTool
from tools.rag.rag import search_with_rag
import os

PDF_PATH = "data/romeo-and-juliet.pdf"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

def search_knowledge_base(query: str) -> str:
    """
    Searches the internal knowledge base (PDF documents) to answer user questions.
    Use this tool when the user asks specific questions about the uploaded documents.
    
    Args:
        query: The specific question or search term to look up.
    """
    try:
        answer = search_with_rag(
            query=query, 
            pdf_path=PDF_PATH,
            rerank=True,
            top_k=5
        )
        return str(answer)
    except Exception as e:
        return f"Error searching knowledge base: {e}"

    
rag_tool = FunctionTool(search_knowledge_base)