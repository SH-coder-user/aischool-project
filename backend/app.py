import os
import uuid
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.database import (
    create_session,
    fetch_logs,
    init_db,
    insert_complaint,
    insert_log,
    update_session_status,
)
from backend.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ApiError,
    ApiResponse,
    ConfirmRequest,
    ConfirmResponse,
    FinalizeRequest,
    FinalizeResponse,
    LogEntry,
    StartRequest,
    StartResponse,
    SttResponse,
)
from backend.services.nlp_service import AnalysisResult, analyze_text, format_user_message
from backend.services.whisper_service import transcribe_audio

init_db()

app = FastAPI(title="Elder Complaint Voice Bot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ok(data):
    return ApiResponse(success=True, data=data, error=None)


def fail(code: str, message: str):
    return ApiResponse(success=False, data=None, error=ApiError(code=code, message=message))


@app.post("/api/v1/conversations/start", response_model=ApiResponse[StartResponse])
async def start_conversation(payload: StartRequest):
    session_uuid = str(uuid.uuid4())
    create_session(session_uuid, payload.debug_mode)
    insert_log(
        session_uuid,
        step="SESSION",
        level="INFO",
        message="새로운 세션이 생성되었습니다.",
        payload={"debug_mode": payload.debug_mode},
    )
    return ok(StartResponse(session_uuid=session_uuid, status="IN_PROGRESS"))


@app.post("/api/v1/conversations/{session_uuid}/stt", response_model=ApiResponse[SttResponse])
async def stt_conversation(session_uuid: str, audio_file: UploadFile = File(...)):
    try:
        audio_bytes = await audio_file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    raw_text = transcribe_audio(audio_bytes, audio_file.filename, api_key=os.getenv("OPENAI_API_KEY"))
    insert_log(
        session_uuid,
        step="STT",
        level="INFO",
        message="음성 인식이 완료되었습니다.",
        payload={"raw_text": raw_text, "size": len(audio_bytes)},
    )
    return ok(SttResponse(raw_text=raw_text))


@app.post("/api/v1/conversations/{session_uuid}/analyze", response_model=ApiResponse[AnalyzeResponse])
async def analyze_conversation(session_uuid: str, payload: AnalyzeRequest):
    if not payload.raw_text:
        return fail("INVALID_TEXT", "분석할 텍스트가 없습니다.")

    result = analyze_text(payload.raw_text)
    insert_log(
        session_uuid,
        step="ANALYZE",
        level="INFO",
        message="요약 및 분류가 완료되었습니다.",
        payload=result.__dict__,
    )
    return ok(AnalyzeResponse(**result.__dict__))


@app.post("/api/v1/conversations/{session_uuid}/confirm", response_model=ApiResponse[ConfirmResponse])
async def confirm_conversation(session_uuid: str, payload: ConfirmRequest):
    insert_log(
        session_uuid,
        step="CONFIRM",
        level="INFO",
        message="사용자 확인 결과",
        payload={"is_confirmed": payload.is_confirmed},
    )
    return ok(ConfirmResponse(next_step="SAVE_AND_NOTIFY" if payload.is_confirmed else "RETRY"))


@app.post("/api/v1/conversations/{session_uuid}/finalize", response_model=ApiResponse[FinalizeResponse])
async def finalize_conversation(session_uuid: str, payload: FinalizeRequest):
    complaint_id = insert_complaint({"session_uuid": session_uuid, **payload.model_dump()})
    update_session_status(session_uuid, "COMPLETED")
    insert_log(
        session_uuid,
        step="DB_SAVE",
        level="INFO",
        message="민원이 저장되었습니다.",
        payload={"complaint_id": complaint_id},
    )
    user_message = format_user_message(
        AnalysisResult(
            summary_text=payload.summary_text,
            category=payload.category,
            severity=payload.severity,
            handling_type=payload.handling_type,
            handling_desc=payload.handling_desc or "",
        )
    )
    return ok(FinalizeResponse(user_message=user_message))


@app.get("/api/v1/logs", response_model=ApiResponse[list[LogEntry]])
async def list_logs(session_uuid: str | None = None):
    logs = fetch_logs(session_uuid)
    return ok([LogEntry(**row) for row in logs])

