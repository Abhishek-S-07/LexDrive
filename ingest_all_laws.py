import json
import os
import glob
from langchain_text_splitters import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

def ingest_law_json(json_path, vector_store):
    """Ingest a single law JSON file into the vector store"""
    print(f"Reading {json_path}...")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        sections = json.load(f)
    
    print(f"Loaded {len(sections)} sections from {os.path.basename(json_path)}")
    
    # Initialize text splitter
    text_splitter = CharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    
    # Process each section
    documents = []
    for i, section in enumerate(sections):
        section_num = section["section"]
        title = section["title"]
        chapter = section["chapter"]
        text = section["text"]
        
        print(f"  Processing section {section_num}")
        
        # Split the text into chunks
        chunks = text_splitter.split_text(text)
        
        # Create documents for each chunk
        for chunk in chunks:
            doc = Document(
                page_content=chunk,
                metadata={
                    "section": section_num,
                    "title": title,
                    "chapter": chapter,
                    "source": os.path.basename(json_path)  # Track which state law this came from
                }
            )
            documents.append(doc)
    
    # Add all documents to ChromaDB
    print(f"  Adding {len(documents)} document chunks to ChromaDB...")
    if documents:
        vector_store.add_documents(documents)
        print(f"  Successfully added documents from {os.path.basename(json_path)}")
    else:
        print(f"  No documents to add from {os.path.basename(json_path)}")
    
    return len(documents)

def main():
    # Initialize embeddings
    print("Initializing embeddings model...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Initialize ChromaDB
    persist_directory = r"./chroma_db"
    print(f"Initializing ChromaDB with persist directory: {persist_directory}")
    vector_store = Chroma(
        embedding_function=embeddings,
        persist_directory=persist_directory
    )
    
    # Find all state law JSON files
    state_law_files = glob.glob("state_law_jsons/*_law.json")
    # Also include the original law database
    state_law_files.append("law_database.json")
    
    print(f"Found {len(state_law_files)} law files to process")
    
    total_documents = 0
    for json_file in state_law_files:
        if os.path.exists(json_file):
            doc_count = ingest_law_json(json_file, vector_store)
            total_documents += doc_count
        else:
            print(f"Warning: File not found: {json_file}")
    
    print(f"\nIngestion complete! Total document chunks added: {total_documents}")

if __name__ == "__main__":
    main()