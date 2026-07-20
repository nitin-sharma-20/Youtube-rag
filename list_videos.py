import os
import chromadb

# Point to your existing database
DB_PATH = os.path.join(os.getcwd(), "data", "chroma_db")
client = chromadb.PersistentClient(path=DB_PATH)

# Ask ChromaDB for all collections
collections = client.list_collections()

print("\n=== Videos Currently in Database ===")
if not collections:
    print("Database is empty!")
else:
    for c in collections:
        print(f"Video ID: {c.name}")
print("====================================\n")