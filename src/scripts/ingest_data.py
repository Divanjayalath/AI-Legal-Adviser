# src/scripts/ingest_data.py

import os
import dotenv
from tqdm import tqdm
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter # <-- CORRECTED LINE
from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Load environment variables
dotenv.load_dotenv()

# Define paths and constants
DATA_PATH = 'data/raw'
DB_PATH = 'chroma_db'
COLLECTION_NAME = 'sri_lanka_legal'

def main():
    """
    Main function to process PDFs, create embeddings, and store them in ChromaDB.
    """
    print("Starting data ingestion and embedding process...")

    # --- 1. LOAD DOCUMENTS ---
    documents = []
    for filename in os.listdir(DATA_PATH):
        if filename.endswith('.pdf'):
            file_path = os.path.join(DATA_PATH, filename)
            try:
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
                print(f"Loaded {filename}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    if not documents:
        print("No documents loaded. Exiting.")
        return

    # --- 2. SPLIT DOCUMENTS INTO CHUNKS ---
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200) # <-- CORRECTED USAGE
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    # --- 3. SETUP EMBEDDING MODEL AND DATABASE ---
    # Initialize the embedding model
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    # Initialize ChromaDB client and create/get collection
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    # --- 4. EMBED AND STORE CHUNKS ---
    print(f"Embedding and storing {len(chunks)} chunks in ChromaDB. This may take a while...")
    
    # Process chunks in batches to be efficient
    batch_size = 100
    for i in tqdm(range(0, len(chunks), batch_size), desc="Embedding Chunks"):
        batch = chunks[i:i+batch_size]
        
        # Create IDs for each chunk
        ids = [f"chunk_{i+j}" for j, _ in enumerate(batch)]
        
        # Get document content for embedding
        documents_content = [doc.page_content for doc in batch]

        # Embed the batch and add to the collection
        try:
            embedded_vectors = embeddings.embed_documents(documents_content)
            collection.add(
                ids=ids,
                embeddings=embedded_vectors,
                documents=documents_content,
                metadatas=[doc.metadata for doc in batch]
            )
        except Exception as e:
            print(f"Error embedding batch {i//batch_size}: {e}")

    print("--- Process Finished ---")
    print(f"Total chunks in collection: {collection.count()}")

if __name__ == '__main__':
    main()