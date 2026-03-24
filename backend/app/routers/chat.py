"""Chat / Query API endpoints with conversation memory."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.llm.sql_generator import process_query

router = APIRouter(prefix="/api", tags=["chat"])

# In-memory conversation store (keyed by conversation_id)
_conversations: dict[str, list[dict]] = {}


class ChatRequest(BaseModel):
    message: str
    conversation_id: str = "default"


class ChatResponse(BaseModel):
    answer: str
    sql_query: str | None = None
    query_results: list | None = None
    referenced_entities: list[str] = []
    confidence: float = 0.5


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Process a natural language query and return data-backed answer."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Get conversation history
    history = _conversations.get(request.conversation_id, [])

    # Process the query
    result = process_query(request.message, conversation_history=history)

    # Store in conversation history
    if request.conversation_id not in _conversations:
        _conversations[request.conversation_id] = []
    _conversations[request.conversation_id].append({"role": "user", "content": request.message})
    _conversations[request.conversation_id].append({"role": "assistant", "content": result["answer"]})

    # Keep only last 10 messages (5 exchanges)
    if len(_conversations[request.conversation_id]) > 10:
        _conversations[request.conversation_id] = _conversations[request.conversation_id][-10:]

    return ChatResponse(**result)


@router.delete("/chat/{conversation_id}")
def clear_conversation(conversation_id: str):
    """Clear conversation history."""
    _conversations.pop(conversation_id, None)
    return {"status": "cleared"}
