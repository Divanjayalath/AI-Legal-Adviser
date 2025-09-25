# src/tools/retrieval_tool.py

import os
import chromadb
from langchain_chroma import Chroma
from langchain.tools import tool

@tool
def search_legal_documents(query: str) -> str:
    """
    Searches and retrieves relevant sections from Sri Lankan legal documents.
    Use this tool to answer any questions about laws, acts, rights, regulations,
    or legal procedures. The input should be a specific question about a legal matter.
    """
    print(f"--- 📚 Executing Legal Retrieval Tool with query: '{query}' ---")
    try:
        client = chromadb.CloudClient(
            tenant=os.getenv("CHROMA_TENANT"),
            database=os.getenv("CHROMA_DATABASE"),
            api_key=os.getenv("CHROMA_API_KEY")
        )
        vector_store = Chroma(
            client=client,
            collection_name='sri_lanka_legal',
        )
        
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        docs = retriever.invoke(query)
        
        if not docs:
            return "No relevant legal documents were found for this query."
            
        context = "\n\n---\n\n".join([doc.page_content for doc in docs])
        return f"Retrieved the following context from legal documents:\n{context}"
    except Exception as e:
        return f"An error occurred while retrieving legal documents: {e}"