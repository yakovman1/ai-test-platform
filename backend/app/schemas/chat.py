from pydantic import BaseModel


class ChatSessionResponse(BaseModel):
    id: int
    title: str

    model_config = {"from_attributes": True}


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    source_summary: str | None = None

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    message: str
    mode: str = "normal"
    style: str = "concise"


class ChatResponse(BaseModel):
    message: ChatMessageResponse
