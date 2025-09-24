# testing/simple_chromadb_viewer.py

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def view_chromadb_basic():
    """
    Simple ChromaDB viewer without dependencies
    """
    print("=== ChromaDB Basic Viewer ===")
    
    # Check if database directory exists
    db_path = 'chroma_db'
    if not os.path.exists(db_path):
        print(f"❌ ChromaDB directory not found at {db_path}")
        print("Make sure you've run the data ingestion script first.")
        return
    
    # List contents of ChromaDB directory
    print(f"\n📁 ChromaDB Directory Contents:")
    for item in os.listdir(db_path):
        item_path = os.path.join(db_path, item)
        if os.path.isdir(item_path):
            print(f"  📁 {item}/")
            # List subdirectory contents
            try:
                for subitem in os.listdir(item_path):
                    print(f"    📄 {subitem}")
            except PermissionError:
                print(f"    (Permission denied)")
        else:
            file_size = os.path.getsize(item_path)
            print(f"  📄 {item} ({file_size} bytes)")
    
    print(f"\n✅ ChromaDB appears to be set up!")
    print(f"Run the advanced viewer with dependencies installed to explore the data.")

if __name__ == '__main__':
    view_chromadb_basic()