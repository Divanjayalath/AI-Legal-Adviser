# testing/simple_data_viewer.py

import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

# Define constants
DB_PATH = 'chroma_db'
COLLECTION_NAME = 'sri_lanka_legal'

def main():
    """Simple ChromaDB data viewer"""
    print("🔍 Simple ChromaDB Data Viewer")
    print("=" * 40)
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"❌ ChromaDB directory not found at {DB_PATH}")
        print("Make sure you've run the data ingestion script first.")
        return
    
    if not CHROMADB_AVAILABLE:
        print("⚠️  ChromaDB not installed. Showing basic file info only.")
        print(f"\n📁 ChromaDB Directory Contents:")
        for item in os.listdir(DB_PATH):
            item_path = os.path.join(DB_PATH, item)
            if os.path.isfile(item_path):
                file_size = os.path.getsize(item_path)
                print(f"  📄 {item} ({file_size:,} bytes)")
            else:
                print(f"  📁 {item}/")
        return
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path=DB_PATH)
        
        # List all collections
        collections = client.list_collections()
        print(f"\n📊 Collections Found: {len(collections)}")
        
        if not collections:
            print("❌ No collections found in the database.")
            print("Make sure you've run the data ingestion script successfully.")
            return
        
        for collection in collections:
            print(f"  📁 Collection: {collection.name}")
            
            # Get collection stats
            try:
                coll = client.get_collection(name=collection.name)
                count = coll.count()
                print(f"     Total documents: {count}")
                
                if count > 0:
                    # Get a sample document (without searching)
                    sample = coll.get(limit=1, include=['documents', 'metadatas'])
                    if sample['documents']:
                        doc_preview = sample['documents'][0][:200] + "..." if len(sample['documents'][0]) > 200 else sample['documents'][0]
                        print(f"     Sample content: {doc_preview}")
                        if sample['metadatas'][0]:
                            print(f"     Sample metadata: {sample['metadatas'][0]}")
                else:
                    print("     ⚠️  Collection is empty")
                    
            except Exception as e:
                print(f"     ❌ Error accessing collection: {e}")
        
        # Interactive options for non-empty collections
        for collection in collections:
            coll = client.get_collection(name=collection.name)
            count = coll.count()
            
            if count > 0:
                print(f"\n📋 Would you like to export collection '{collection.name}' to a text file?")
                response = input("Enter 'y' for yes, any other key to skip: ").strip().lower()
                
                if response == 'y':
                    filename = f"{collection.name}_export.txt"
                    try:
                        results = coll.get(include=['documents', 'metadatas'])
                        
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(f"ChromaDB Export - Collection: {collection.name}\n")
                            f.write(f"Export Date: {import_datetime()}\n")
                            f.write(f"Total Documents: {len(results['ids'])}\n")
                            f.write("=" * 50 + "\n\n")
                            
                            for i, (doc_id, content, metadata) in enumerate(zip(
                                results['ids'],
                                results['documents'],
                                results['metadatas']
                            ), 1):
                                f.write(f"Document {i}\n")
                                f.write(f"ID: {doc_id}\n")
                                if metadata:
                                    f.write(f"Metadata: {metadata}\n")
                                f.write(f"Content:\n{content}\n")
                                f.write("-" * 50 + "\n\n")
                        
                        print(f"✅ Exported {len(results['ids'])} documents to {filename}")
                    
                    except Exception as e:
                        print(f"❌ Export error: {e}")
    
    except Exception as e:
        print(f"❌ Error connecting to ChromaDB: {e}")

def import_datetime():
    """Import datetime safely"""
    try:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "Unknown"

if __name__ == '__main__':
    main()