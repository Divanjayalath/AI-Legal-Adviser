# testing/view_chromadb.py

import chromadb
import os
from pprint import pprint

# Define constants (same as in ingest_data.py)
DB_PATH = 'chroma_db'
COLLECTION_NAME = 'sri_lanka_legal'

def view_chromadb_data():
    """
    View and explore ChromaDB data
    """
    print("=== ChromaDB Data Viewer ===")
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"❌ ChromaDB not found at {DB_PATH}")
        print("Make sure you've run the data ingestion script first.")
        return
    
    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path=DB_PATH)
        
        # List all collections
        collections = client.list_collections()
        print(f"\n📊 Found {len(collections)} collection(s):")
        for collection in collections:
            print(f"  - {collection.name}")
        
        # Get the specific collection
        if COLLECTION_NAME not in [c.name for c in collections]:
            print(f"❌ Collection '{COLLECTION_NAME}' not found!")
            return
            
        collection = client.get_collection(name=COLLECTION_NAME)
        
        # Get collection statistics
        count = collection.count()
        print(f"\n📈 Collection '{COLLECTION_NAME}' Statistics:")
        print(f"  - Total documents: {count}")
        
        if count == 0:
            print("  - No documents found in collection")
            return
        
        # Get first 5 documents as sample
        print(f"\n📄 Sample Documents (first 5):")
        results = collection.get(limit=5)
        
        for i, (doc_id, document, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            print(f"\n--- Document {i+1} ---")
            print(f"ID: {doc_id}")
            print(f"Content Preview: {document[:200]}...")
            print(f"Metadata: {metadata}")
            print("-" * 50)
        
        # Interactive exploration
        print(f"\n🔍 Interactive Exploration")
        while True:
            print("\nOptions:")
            print("1. Search by query")
            print("2. Get document by ID")
            print("3. Show all document IDs")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                query = input("Enter search query: ").strip()
                if query:
                    search_documents(collection, query)
            
            elif choice == '2':
                doc_id = input("Enter document ID: ").strip()
                if doc_id:
                    get_document_by_id(collection, doc_id)
            
            elif choice == '3':
                show_all_ids(collection)
            
            elif choice == '4':
                print("Goodbye! 👋")
                break
            
            else:
                print("Invalid choice. Please try again.")
    
    except Exception as e:
        print(f"❌ Error accessing ChromaDB: {e}")

def search_documents(collection, query, num_results=5):
    """
    Search documents using similarity search
    """
    try:
        print(f"\n🔍 Searching for: '{query}'")
        results = collection.query(
            query_texts=[query],
            n_results=num_results
        )
        
        if not results['documents'][0]:
            print("No results found.")
            return
        
        print(f"\n📋 Found {len(results['documents'][0])} results:")
        
        for i, (doc_id, document, distance) in enumerate(zip(
            results['ids'][0], 
            results['documents'][0], 
            results['distances'][0]
        )):
            print(f"\n--- Result {i+1} (Distance: {distance:.4f}) ---")
            print(f"ID: {doc_id}")
            print(f"Content: {document[:300]}...")
            print("-" * 50)
    
    except Exception as e:
        print(f"❌ Error searching: {e}")

def get_document_by_id(collection, doc_id):
    """
    Get a specific document by its ID
    """
    try:
        results = collection.get(ids=[doc_id])
        
        if not results['documents']:
            print(f"❌ Document with ID '{doc_id}' not found.")
            return
        
        print(f"\n📄 Document Details:")
        print(f"ID: {doc_id}")
        print(f"Content: {results['documents'][0]}")
        print(f"Metadata: {results['metadatas'][0]}")
    
    except Exception as e:
        print(f"❌ Error retrieving document: {e}")

def show_all_ids(collection, limit=20):
    """
    Show all document IDs (limited to avoid spam)
    """
    try:
        results = collection.get(limit=limit)
        print(f"\n📋 Document IDs (showing first {limit}):")
        
        for i, doc_id in enumerate(results['ids'], 1):
            print(f"{i:3d}. {doc_id}")
        
        total_count = collection.count()
        if total_count > limit:
            print(f"\n... and {total_count - limit} more documents")
    
    except Exception as e:
        print(f"❌ Error retrieving IDs: {e}")

if __name__ == '__main__':
    view_chromadb_data()