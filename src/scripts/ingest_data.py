# src/scripts/ingest_data.py

import os
import sys
import dotenv
from tqdm import tqdm #for show prograss bar
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

def main():
    
    # Connects to cloud ChromaDB and uploads PDFs (embeddings).
    # Load and Validate ChromaDB Credentials
    dotenv.load_dotenv()
    
    chroma_tenant = os.getenv("CHROMA_TENANT")
    chroma_database = os.getenv("CHROMA_DATABASE")
    chroma_api_key = os.getenv("CHROMA_API_KEY")

    if not all([chroma_tenant, chroma_database, chroma_api_key]):
        print("Error: Missing ChromaDB credentials in .env file.")
        print("Please ensure your .env contains: CHROMA_TENANT, CHROMA_DATABASE, CHROMA_API_KEY")
        sys.exit(1)

    # --- Configuration ---
    DATA_PATH = 'data/raw'
    COLLECTION_NAME = 'sri_lanka_legal'

    # --- 1. LOAD DOCUMENTS ---
    documents = []
    print(f"Loading documents from {DATA_PATH}...")
    
    if not os.path.exists(DATA_PATH):
        print(f"Directory '{DATA_PATH}' not found!")
        return
    
    pdf_files = [f for f in os.listdir(DATA_PATH) if f.endswith('.pdf')]
    if not pdf_files:
        print(f"No PDF files found in '{DATA_PATH}'")
        return
    
    print(f"Found {len(pdf_files)} PDF files: {pdf_files}")
    
    for filename in pdf_files:
        file_path = os.path.join(DATA_PATH, filename)
        try:
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            documents.extend(docs)
            print(f"✅Loaded {filename} ({len(docs)} pages)")
        except Exception as e:
            print(f"❌Error loading {filename}: {e}")

    if not documents:
        print("❌ No documents were loaded successfully.")
        return

    print(f"Total loaded: {len(documents)} document pages.")



    # --- 2. SPLIT DOCUMENTS INTO CHUNKS ---
    print("-------------Splitting documents into chunks------------")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks.")




    # --- 3. CONNECT TO CHROMADB (NO GOOGLE API NEEDED!    python3 src/scripts/ingest_data.py) ---
    print("Connecting to ChromaDB Cloud......")
    try:
        client = chromadb.CloudClient(
            tenant=chroma_tenant,
            database=chroma_database,
            api_key=chroma_api_key
        )
        
        # Create collection with default embeddings
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
        )
        print("✅ Successfully connected to ChromaDB!")
        
    except Exception as e:
        print(f"❌ ChromaDB connection failed: {e}")
        return



    # --- 4. STORE CHUNKS (NO EMBEDDING API CALLS!) ---
    # Clear existing data first
    #reduse duplicates values 
    try:
        existing_count = collection.count()
        if existing_count > 0:#if have old exists in the data , delete all old data
            print(f"Clearing {existing_count} existing chunks......")
            existing_data = collection.get()
            if existing_data['ids']:
                collection.delete(ids=existing_data['ids'])
            print("✅ Cleared existing data.")
    except Exception as e:
        print(f"⚠️ Warning: Could not clear existing data: {e}")





    # Add new chunks in batches
    batch_size = 50  # Smaller batches for cloud
    success_count = 0
    
    for i in tqdm(range(0, len(chunks), batch_size), desc="Uploading..."):
        batch = chunks[i:i+batch_size]
        
        # Create unique IDs
        ids = [f"chunk_{i+j:04d}" for j, _ in enumerate(batch)]
        
        # Get document content
        documents_content = [doc.page_content for doc in batch]
        
        # Get metadata
        metadatas = []
        for doc in batch:
            metadata = doc.metadata.copy() if doc.metadata else {}
            # Add chunk info
            metadata.update({
                'chunk_index': i + len(metadatas),
                'chunk_size': len(doc.page_content)
            })
            metadatas.append(metadata)
        
        try:
            # ChromaDB will automatically create embeddings for free!
            collection.add(
                ids=ids,
                documents=documents_content,
                metadatas=metadatas
            )
            success_count += len(batch)
            
        except Exception as e:
            print(f"\n❌ Error uploading batch {i//batch_size + 1}: {e}")
            if "rate limit" in str(e).lower():
                print("⏳ Rate limited. Waiting 5 seconds...")
                import time
                time.sleep(5)
                # Retry once
                try:
                    collection.add(
                        ids=ids,
                        documents=documents_content,
                        metadatas=metadatas
                    )
                    success_count += len(batch)
                except Exception as e2:
                    print(f"❌ Retry failed: {e2}")
            else:
                print(f"❌ Batch {i//batch_size + 1} failed permanently.")





    # ------------VERIFY RESULTS ---------------------
    final_count = collection.count()
    print(f"\nProcess Finished.......!")
    print(f"Total chunks in collection: {final_count}")
    print(f"✅ Successfully uploaded: {success_count}/{len(chunks)} chunks")
    
    if final_count > 0:
        print("Success! Your data is now ready for the AI Legal Adviser app.")
        
        # Test a quick query
        try:
            test_results = collection.query(
                query_texts=["legal advice"],
                n_results=1
            )
            if test_results['documents'][0]:
                print("Quick test query successful - embeddings are working....!")
            else:
                print("⚠️ Test query returned no results.")
        except Exception as e:
            print(f"⚠️ Test query failed: {e}")
    else:
        print("❌ No data was uploaded. Check the errors above.")

if __name__ == '__main__':
    main()