from pydantic import BaseModel, Field


class CaptureRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10_000)


class CaptureResponse(BaseModel):
    saved: list[str]
    duplicates: list[str]
