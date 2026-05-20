modules = [
    "fastapi",
    "pydantic",
    "langchain_anthropic",
    "langchain_chroma",
    "langchain_community.embeddings",
    "langchain.chains",
    "langchain.chains.combine_documents",
    "langchain_core.prompts",
    "uvicorn",
    "chromadb",
    "sentence_transformers",
    "anthropic",
]

for m in modules:
    try:
        __import__(m)
        print(m+": OK")
    except Exception as e:
        print(m+": ERROR -> "+str(e))
