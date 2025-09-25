# testing/advanced_chromadb_viewer.py

import os
import sys
from typing import Optional, List, Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import chromadb
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    import dotenv
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Missing dependencies: {e}")
    print("Install required packages: pip install chromadb langchain-google-genai python-dotenv")
    DEPENDENCIES_AVAILABLE = False

# Load environment variables
if DEPENDENCIES_AVAILABLE:
    dotenv.load_dotenv()

# Define constants
DB_PATH = 'chroma_db'
COLLECTION_NAME = 'sri_lanka_legal'

class ChromaDBViewer:
    def __init__(self):
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("Required dependencies not available")
        
        self.client = None
        self.collection = None
        self.embeddings = None
        
    def connect(self):
        """Connect to ChromaDB"""
        try:
            self.client = chromadb.PersistentClient(path=DB_PATH)
            self.collection = self.client.get_collection(name=COLLECTION_NAME)
            print("✅ Connected to ChromaDB successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to ChromaDB: {e}")
            return False
    
    def get_collection_stats(self):
        """Get basic collection statistics"""
        if not self.collection:
            return None
        
        count = self.collection.count()
        return {
            'name': COLLECTION_NAME,
            'total_documents': count
        }
    
    def preview_documents(self, limit: int = 5):
        """Preview first few documents"""
        if not self.collection:
            return None
        
        results = self.collection.get(limit=limit)
        
        documents = []
        for i, (doc_id, content, metadata) in enumerate(zip(
            results['ids'], 
            results['documents'], 
            results['metadatas']
        )):
            documents.append({
                'id': doc_id,
                'content_preview': content[:200] + "..." if len(content) > 200 else content,
                'full_content': content,
                'metadata': metadata,
                'content_length': len(content)
            })
        
        return documents
    
    def search_by_text(self, query: str, limit: int = 5):
        """Search documents by text similarity"""
        if not self.collection:
            return None
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            if not results['documents'][0]:
                return []
            
            search_results = []
            for doc_id, content, distance in zip(
                results['ids'][0],
                results['documents'][0],
                results['distances'][0]
            ):
                search_results.append({
                    'id': doc_id,
                    'content': content,
                    'similarity_score': 1 - distance,  # Convert distance to similarity
                    'distance': distance
                })
            
            return search_results
        
        except Exception as e:
            print(f"❌ Search error: {e}")
            return None
    
    def get_document_by_id(self, doc_id: str):
        """Get specific document by ID"""
        if not self.collection:
            return None
        
        try:
            results = self.collection.get(ids=[doc_id])
            
            if not results['documents']:
                return None
            
            return {
                'id': doc_id,
                'content': results['documents'][0],
                'metadata': results['metadatas'][0] if results['metadatas'] else {}
            }
        
        except Exception as e:
            print(f"❌ Error retrieving document: {e}")
            return None
    
    def get_all_ids(self, limit: int = 50):
        """Get all document IDs"""
        if not self.collection:
            return None
        
        try:
            results = self.collection.get(limit=limit)
            return results['ids']
        except Exception as e:
            print(f"❌ Error retrieving IDs: {e}")
            return None
    
    def export_to_text(self, output_file: str = "chromadb_export.txt"):
        """Export all documents to a text file"""
        if not self.collection:
            return False
        
        try:
            # Get all documents
            all_results = self.collection.get()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"ChromaDB Export - Collection: {COLLECTION_NAME}\n")
                f.write(f"Total Documents: {len(all_results['ids'])}\n")
                f.write("=" * 50 + "\n\n")
                
                for i, (doc_id, content, metadata) in enumerate(zip(
                    all_results['ids'],
                    all_results['documents'],
                    all_results['metadatas']
                ), 1):
                    f.write(f"Document {i}\n")
                    f.write(f"ID: {doc_id}\n")
                    f.write(f"Metadata: {metadata}\n")
                    f.write(f"Content:\n{content}\n")
                    f.write("-" * 50 + "\n\n")
            
            print(f"✅ Exported {len(all_results['ids'])} documents to {output_file}")
            return True
        
        except Exception as e:
            print(f"❌ Export error: {e}")
            return False

def main():
    """Main interactive function"""
    if not DEPENDENCIES_AVAILABLE:
        print("❌ Cannot run advanced viewer without dependencies.")
        print("Install: pip install chromadb langchain-google-genai python-dotenv")
        return
    
    print("🔍 Advanced ChromaDB Viewer")
    print("=" * 40)
    
    # Initialize viewer
    viewer = ChromaDBViewer()
    
    if not viewer.connect():
        return
    
    # Show collection stats
    stats = viewer.get_collection_stats()
    if stats:
        print(f"\n📊 Collection Statistics:")
        print(f"  Name: {stats['name']}")
        print(f"  Total Documents: {stats['total_documents']}")
    
    # Interactive menu
    while True:
        print(f"\n🔍 Options:")
        print("1. Preview documents")
        print("2. Search by text")
        print("3. Get document by ID")
        print("4. Show all document IDs")
        print("5. Export all data to text file")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            limit = input("How many documents to preview? (default: 5): ").strip()
            limit = int(limit) if limit.isdigit() else 5
            
            docs = viewer.preview_documents(limit)
            if docs:
                print(f"\n📄 Preview of {len(docs)} documents:")
                for i, doc in enumerate(docs, 1):
                    print(f"\n--- Document {i} ---")
                    print(f"ID: {doc['id']}")
                    print(f"Length: {doc['content_length']} characters")
                    print(f"Preview: {doc['content_preview']}")
                    if doc['metadata']:
                        print(f"Metadata: {doc['metadata']}")
        
        elif choice == '2':
            query = input("Enter search query: ").strip()
            if query:
                limit = input("How many results? (default: 5): ").strip()
                limit = int(limit) if limit.isdigit() else 5
                
                results = viewer.search_by_text(query, limit)
                if results:
                    print(f"\n🔍 Search Results for '{query}':")
                    for i, result in enumerate(results, 1):
                        print(f"\n--- Result {i} ---")
                        print(f"ID: {result['id']}")
                        print(f"Similarity Score: {result['similarity_score']:.4f}")
                        print(f"Content: {result['content'][:300]}...")
                elif results == []:
                    print("No results found.")
        
        elif choice == '3':
            doc_id = input("Enter document ID: ").strip()
            if doc_id:
                doc = viewer.get_document_by_id(doc_id)
                if doc:
                    print(f"\n📄 Document: {doc_id}")
                    print(f"Content: {doc['content']}")
                    print(f"Metadata: {doc['metadata']}")
                else:
                    print(f"❌ Document '{doc_id}' not found.")
        
        elif choice == '4':
            limit = input("How many IDs to show? (default: 20): ").strip()
            limit = int(limit) if limit.isdigit() else 20
            
            ids = viewer.get_all_ids(limit)
            if ids:
                print(f"\n📋 Document IDs (showing first {len(ids)}):")
                for i, doc_id in enumerate(ids, 1):
                    print(f"{i:3d}. {doc_id}")
        
        elif choice == '5':
            filename = input("Export filename (default: chromadb_export.txt): ").strip()
            filename = filename if filename else "chromadb_export.txt"
            
            if viewer.export_to_text(filename):
                print(f"✅ Data exported to {filename}")
        
        elif choice == '6':
            print("Goodbye! 👋")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()