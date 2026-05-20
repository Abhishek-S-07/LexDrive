import json
import os
from langchain_text_splitters import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

def main():
    # Read the law database
    json_path = r"C:\Users\abhis\Downloads\Roadsafety\law_database.json"
    print(f"Reading {json_path}...")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        sections = json.load(f)
    
    print(f"Loaded {len(sections)} sections")
    
    # Initialize text splitter
    text_splitter = CharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    
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
    
    # Process each section
    documents = []
    for i, section in enumerate(sections):
        section_num = section["section"]
        title = section["title"]
        chapter = section["chapter"]
        text = section["text"]
        
        print(f"Ingested section {section_num}")
        
        # Split the text into chunks
        chunks = text_splitter.split_text(text)
        
        # Create documents for each chunk
        for chunk in chunks:
            doc = Document(
                page_content=chunk,
                metadata={
                    "section": section_num,
                    "title": title,
                    "chapter": chapter
                }
            )
            documents.append(doc)
    
    # Add all documents to ChromaDB
    print(f"Adding {len(documents)} document chunks to ChromaDB...")
    if documents:
        vector_store.add_documents(documents)
        print("Successfully added all documents to ChromaDB")
    else:
        print("No documents to add")
    
    print("Ingestion complete!")

if __name__ == "__main__":
    main()