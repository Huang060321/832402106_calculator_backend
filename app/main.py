"""FastAPI entry point for the calculator back end."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import (
    clear_history,
    create_history,
    delete_history,
    history_statistics,
    initialize_database,
    list_history,
)
from app.schemas import (
    CalculationRequest,
    CalculationResponse,
    DeleteResponse,
    HistoryPage,
)
from app.services.calculator import CalculationError, calculate


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="分离式计算器 API",
    description="安全计算表达式并使用关系型数据库持久化计算历史。",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [
    origin.strip()
    for origin in os.getenv(
        "CALCULATOR_CORS_ORIGINS",
        "http://localhost:5500,http://127.0.0.1:5500",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(CalculationError)
async def calculation_error_handler(_, error: CalculationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"success": False, "message": str(error)},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_, error: RequestValidationError) -> JSONResponse:
    first_error = error.errors()[0] if error.errors() else {}
    message = first_error.get("msg", "请求参数无效")
    return JSONResponse(
        status_code=422,
        content={"success": False, "message": str(message)},
    )


@app.exception_handler(HTTPException)
async def http_error_handler(_, error: HTTPException) -> JSONResponse:
    detail = error.detail
    if isinstance(detail, dict):
        content = detail
    else:
        content = {"success": False, "message": str(detail)}
    return JSONResponse(status_code=error.status_code, content=content)


@app.get("/api/health")
def health() -> dict[str, object]:
    return {"success": True, "service": "calculator-api", "version": "1.0.0"}


@app.post("/api/calculate", response_model=CalculationResponse, status_code=201)
def calculate_expression(payload: CalculationRequest) -> dict[str, object]:
    expression = payload.expression.strip()
    result = calculate(expression)
    record = create_history(expression, result)
    return {
        "success": True,
        "expression": expression,
        "result": result,
        "history_id": record["id"],
        "created_at": record["created_at"],
    }


@app.get("/api/history", response_model=HistoryPage)
def get_history(
    q: str = Query(default="", max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=8, ge=1, le=50),
) -> dict[str, object]:
    return list_history(q.strip(), page, page_size)


@app.get("/api/history/stats")
def get_history_statistics() -> dict[str, object]:
    return history_statistics()


@app.delete("/api/history/{history_id}", response_model=DeleteResponse)
def remove_history(history_id: int) -> dict[str, object]:
    if not delete_history(history_id):
        raise HTTPException(
            status_code=404,
            detail={"success": False, "message": "未找到该历史记录"},
        )
    return {"success": True, "deleted": 1}


@app.delete("/api/history", response_model=DeleteResponse)
def remove_all_history() -> dict[str, object]:
    return {"success": True, "deleted": clear_history()}
