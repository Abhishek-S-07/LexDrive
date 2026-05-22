"""DriveLegal AI Backend — FastAPI + LangChain + ChromaDB + Anthropic (Claude)."""

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

# ─── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="DriveLegal AI Backend", version="1.0")

cors_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── API key guard ─────────────────────────────────────────────────────────────
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
if not anthropic_api_key:
    print(
        "WARNING: ANTHROPIC_API_KEY is not set. "
        "The server will start, but /chat will return an error until you set it.\n"
        "  Windows PowerShell: setx ANTHROPIC_API_KEY sk-ant-...\n"
        "  Current session:      $env:ANTHROPIC_API_KEY = 'sk-ant-...'"
    )
    anthropic_api_key = None  # type: ignore[assignment]


# ─── Embeddings ────────────────────────────────────────────────────────────────
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# ─── ChromaDB (pre-populated by ingest.py) ─────────────────────────────────────
db_directory = "./chroma_db"
vector_store = Chroma(
    persist_directory=db_directory,
    embedding_function=embeddings,
)
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

# ─── LLM (Anthropic Claude) ───────────────────────────────────────────────────
llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    api_key=anthropic_api_key,
    temperature=0.2,
    max_tokens=512,
)

# ─── RAG prompt ────────────────────────────────────────────────────────────────
system_prompt = (
    "You are DriveLegal, an AI-powered chatbot helping Indian drivers understand "
    "traffic laws, challans, and police authority. Use the provided legal context to "
    "answer the user's question.\n"
    "If you don't know the answer based on the context, state that clearly.\n"
    "Always cite the exact Motor Vehicles Act section when providing fine amounts "
    "or rules.\n"
    "Keep answers concise and clear, as they may be read aloud via Voice TTS.\n\n"
    "Context:\n{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "User Location: {location}\nUser Query: {input}"),
])

# ─── RAG chain ────────────────────────────────────────────────────────────────
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

# ─── Request / Response schemas ───────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str
    location: str


class ChatResponse(BaseModel):
    answer: str


@app.post("/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest) -> ChatResponse:
    """Process a transcribed voice/text query and return a RAG-backed answer."""
    if not anthropic_api_key:
        raise HTTPException(
            status_code=500,
            detail=(
                "ANTHROPIC_API_KEY is not set. "
                "Set the environment variable and restart the server before calling /chat.\n"
                "  PowerShell (this session): $env:ANTHROPIC_API_KEY = 'sk-ant-...'\n"
                "  PowerShell (permanent):    setx ANTHROPIC_API_KEY 'sk-ant-...'"
            ),
        )
    response = rag_chain.invoke({
        "input": request.query,
        "location": request.location,
    })
    return ChatResponse(answer=response["answer"])
