import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Initialize FastAPI app
app = FastAPI(title="DriveLegal AI Backend", version="1.0")

# Allow CORS for the React frontend (Voice TTS frontend)
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup API Keys (Ensure these are set in your environment variables)
# os.environ["ANTHROPIC_API_KEY"] = "your-anthropic-key-here"

# 1. Initialize the Embedding Model
# Using sentence-transformers (all-MiniLM-L6-v2) as per the spec
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2. Connect to your existing ChromaDB Vector Store
# Ensure 'db_directory' points to where your ChromaDB is saved
db_directory = "./chroma_db" 
vector_store = Chroma(persist_directory=db_directory, embedding_function=embeddings)
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

# 3. Initialize the LLM (Claude API)
# Using the model version specified in the execution plan
llm = ChatAnthropic(
    model_name="claude-sonnet-4-20250514",
    temperature=0.2, # Low temperature for factual legal accuracy
    max_tokens_to_sample=512
)

# 4. Create the RAG Prompt Template
# This instructs Claude to act as DriveLegal and cite exact sections
system_prompt = (
    "You are DriveLegal, an AI-powered chatbot helping Indian drivers understand traffic laws, "
    "challans, and police authority. Use the provided legal context to answer the user's question.\n"
    "If you don't know the answer based on the context, state that clearly.\n"
    "Always cite the exact Motor Vehicles Act section when providing fine amounts or rules.\n"
    "Keep answers concise and clear, as they may be read aloud via Voice TTS.\n\n"
    "Context:\n{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "User Location: {location}\nUser Query: {input}"),
])

# 5. Build the LangChain RAG Pipeline
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

# Data Schema for the incoming request from the React frontend
class ChatRequest(BaseModel):
    query: str       # The text transcribed by the Web Speech API on the frontend
    location: str    # e.g., "Chennai, Tamil Nadu" (Passed from Google Maps API)

class ChatResponse(BaseModel):
    answer: str

@app.post("/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest):
    """
    Endpoint to process transcribed voice queries or text input.
    """
    try:
        # Invoke the RAG chain with the user's query and location context
        response = rag_chain.invoke({
            "input": request.query,
            "location": request.location
        })
        
        # Return the generated text answer to the frontend
        # The frontend will then use Google Text-to-Speech API to read this aloud
        return ChatResponse(answer=response["answer"])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run the server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)