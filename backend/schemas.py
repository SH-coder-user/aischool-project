from typing import Generic, Optional, TypeVar
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")


class ApiError(BaseModel):
    code: str
    message: str


class ApiResponse(GenericModel, Generic[T]):
    success: bool
    data: Optional[T]
    error: Optional[ApiError]


class StartRequest(BaseModel):
    debug_mode: bool = False


class StartResponse(BaseModel):
    session_uuid: str
    status: str


class SttResponse(BaseModel):
    raw_text: str


class AnalyzeRequest(BaseModel):
    raw_text: str


class AnalyzeResponse(BaseModel):
    summary_text: str
    category: str
    severity: str
    handling_type: str
    handling_desc: str


class ConfirmRequest(BaseModel):
    is_confirmed: bool


class ConfirmResponse(BaseModel):
    next_step: str


class FinalizeRequest(BaseModel):
    raw_text: str
    summary_text: str
    category: str
    severity: str
    handling_type: str
    handling_desc: Optional[str] = None
    is_confirmed: bool = True


class FinalizeResponse(BaseModel):
    user_message: str
    redirect: str = "MAIN"


class LogEntry(BaseModel):
    step: str
    level: str
    message: str
    payload: Optional[str] = None
    created_at: str
