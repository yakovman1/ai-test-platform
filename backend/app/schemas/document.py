from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    filename: str
    status: str
    error_message: str | None = None

    model_config = {"from_attributes": True}
