from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    request_id: str
    question: str
    answer: str
    tools_called: list[str]
    latency_ms: int
