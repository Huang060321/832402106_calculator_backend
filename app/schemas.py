"""Pydantic request and response schemas."""

from pydantic import BaseModel, Field


class CalculationRequest(BaseModel):
    expression: str = Field(min_length=1, max_length=200)


class CalculationResponse(BaseModel):
    success: bool = True
    expression: str
    result: int | float
    history_id: int
    created_at: str


class HistoryItem(BaseModel):
    id: int
    expression: str
    result: str
    created_at: str


class HistoryPage(BaseModel):
    items: list[HistoryItem]
    page: int
    page_size: int
    total: int
    pages: int


class DeleteResponse(BaseModel):
    success: bool = True
    deleted: int


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
