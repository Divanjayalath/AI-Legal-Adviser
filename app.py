import streamlit as st
import os
import dotenv
import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain.prompts import PromptTemplate
from langchain.chains.retrieval_qa.base import RetrievalQA

# Load environment variables from .env file
dotenv.load_dotenv()

# --- CONFIGURATION ---
COLLECTION_NAME = 'sri_lanka_legal'
DB_PATH = 'chroma_db'  # Local database path

# --- RAG CHAIN SETUP ---

# app.py - NEW get_rag_chain function

@st.cache_resource
def get_rag_chain():
    # Connect to ChromaDB Cloud
    client = chromadb.CloudClient(
        tenant=os.getenv("CHROMA_TENANT"),
        database=os.getenv("CHROMA_DATABASE"),
        api_key=os.getenv("CHROMA_API_KEY")
    )
    
    # Get the collection directly from ChromaDB (bypassing LangChain)
    collection = client.get_collection(name='sri_lanka_legal')
    
    # Create a simple vector store wrapper
    class SimpleVectorStore:
        def __init__(self, collection):
            self.collection = collection
        
        def similarity_search(self, query, k=3):
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )
            # Convert to LangChain document format
            docs = []
            for i, (doc_id, content, metadata) in enumerate(zip(
                results['ids'][0],
                results['documents'][0], 
                results['metadatas'][0] if results['metadatas'][0] else [{}] * len(results['ids'][0])
            )):
                from langchain.schema import Document
                docs.append(Document(page_content=content, metadata=metadata or {}))
            return docs
    
    vector_store = SimpleVectorStore(collection)

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    
    # (The prompt template and chain creation are the same as before)
    prompt_template = """
    You are a helpful AI Legal Assistant for Sri Lankan law. Use the provided legal documents to answer questions accurately.
    
    Context from legal documents:
    {context}
    
    Question: {question}
    
    Instructions:
    - Provide accurate legal information based on the context
    - If the context doesn't contain relevant information, say so clearly
    - Always mention that this is general information and recommend consulting a qualified lawyer
    - Be helpful and professional
    
    Answer:
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, chain_type_kwargs={"prompt": prompt}, return_source_documents=True)
    
    return chain

# --- STREAMLIT UI ---

def main():
    """Main Streamlit app"""
    # Page configuration
    st.set_page_config(
        page_title="AI Legal Adviser",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Header
    st.title("⚖️ AI Legal Adviser")
    st.markdown("*Get legal guidance based on Sri Lankan law documents*")
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Information")
        st.markdown("""
        **How it works:**
        - Ask legal questions in natural language
        - AI searches through legal documents
        - Get relevant answers with source references
        
        **Important Notice:**
        This tool provides general legal information only. 
        Always consult with a qualified lawyer for specific legal advice.
        """)
        
        # Connection status
        st.header("🔗 Status")
        try:
            chain = get_rag_chain()
            st.success("✅ Connected to legal database")
            st.info("📚 Documents loaded and ready")
        except Exception as e:
            st.error(f"❌ Connection failed: {str(e)}")
            st.stop()

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        st.session_state.messages.append({
            "role": "assistant",
            "content": "👋 Hello! I'm your AI Legal Assistant. I can help you with questions about Sri Lankan law based on the legal documents in my database. What would you like to know?"
        })

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask a legal question..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🔍 Searching legal documents..."):
                try:
                    # Get the RAG chain
                    chain = get_rag_chain()
                    
                    # Query the chain using the new method
                    response = chain.invoke({"query": prompt})
                    
                    # Extract answer and sources
                    answer = response.get("result", "I apologize, but I couldn't generate a response.")
                    source_docs = response.get("source_documents", [])
                    
                    # Display answer
                    st.markdown(answer)
                    
                    # Display sources if available
                    if source_docs:
                        with st.expander("📖 Source Documents"):
                            for i, doc in enumerate(source_docs, 1):
                                st.markdown(f"**Source {i}:**")
                                st.markdown(f"```\n{doc.page_content[:300]}...\n```")
                                if hasattr(doc, 'metadata') and doc.metadata:
                                    st.markdown(f"*Metadata: {doc.metadata}*")
                                st.markdown("---")
                    
                    # Add assistant response to chat history
                    full_response = answer
                    if source_docs:
                        full_response += f"\n\n*Based on {len(source_docs)} source document(s)*"
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": full_response
                    })
                    
                except Exception as e:
                    error_msg = f"❌ Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.8em;'>
            ⚖️ AI Legal Adviser | Built with Streamlit & ChromaDB | 
            <strong>Disclaimer:</strong> This is not professional legal advice
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()