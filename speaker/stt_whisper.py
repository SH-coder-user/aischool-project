# -*- coding: utf-8 -*-
"""
stt_whisper.py

이 모듈은 음성 파일(또는 바이트)을 OpenAI Whisper(STT) API로 보내서
'한국어 텍스트'로 변환하는 역할을 합니다.

🎯 역할 요약
--------------------------------------
1. .env 에서 OPENAI_API_KEY, WHISPER_MODEL 읽기
2. 음성 파일 경로를 받아 텍스트로 변환 (transcribe_file)
3. 메모리 상의 바이트(녹음 버퍼 등)를 받아 텍스트로 변환 (transcribe_bytes)
4. 모든 예외는 잡아서 경고 로그를 남기고, 호출 측이 판단하도록 빈 문자열 반환

👉 이 모듈은 "오디오 → 텍스트"만 담당하며,
   텍스트를 민원 엔진(minwon_engine)에 넘기는 작업은 main.py/speaker.py 쪽에서 처리합니다.
"""

import os
import io
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

# -------------------------------------------------------------------
# 환경 설정
# -------------------------------------------------------------------

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError(".env에 OPENAI_API_KEY가 없습니다. 음성 인식을 위해 API 키를 설정해 주세요.")

# OpenAI 클라이언트
client = OpenAI(api_key=API_KEY)

# Whisper 모델 이름 (필요하면 .env에서 덮어쓰기)
# - 기본값은 최신 소형 STT 전용 모델(gpt-4o-mini-transcribe 등)을 가정
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "gpt-4o-mini-transcribe")

# -------------------------------------------------------------------
# 공통 STT 로직
# -------------------------------------------------------------------

def _call_whisper(file_obj, language: str = "ko") -> str:
    """
    실제로 OpenAI Whisper API를 호출하는 내부 함수.

    :param file_obj: 바이너리 모드로 연 열린 파일 객체 (또는 BytesIO)
    :param language: 음성 언어 코드 (기본값 'ko' = 한국어)
    :return: 변환된 텍스트 (실패 시 빈 문자열)
    """
    try:
        # OpenAI Audio Transcription API 호출
        resp = client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            file=file_obj,
            language=language,
            response_format="text",  # 순수 텍스트만 반환
        )
        # response_format="text" 이면 resp 자체가 문자열이거나,
        # 일부 버전에서는 resp.text 속성에 텍스트가 들어갈 수 있음
        if isinstance(resp, str):
            return resp.strip()
        # 안전하게 처리
        text = getattr(resp, "text", "") or str(resp)
        return text.strip()
    except Exception as e:
        print(f"[WARN] Whisper STT 호출 중 오류 발생: {e}")
        return ""


# -------------------------------------------------------------------
# 외부에서 사용할 공개 함수들
# -------------------------------------------------------------------

def transcribe_file(path: str,
                    language: str = "ko") -> str:
    """
    음성 파일 경로를 받아 텍스트로 변환합니다.

    지원 확장자 예시: .wav, .mp3, .m4a, .webm 등
    (실제 지원 여부는 OpenAI Whisper 스펙에 따름)

    :param path: 로컬 음성 파일 경로
    :param language: 음성 언어 코드 (예: "ko", "en")
    :return: 인식된 텍스트 (실패 시 빈 문자열)
    """
    if not os.path.exists(path):
        print(f"[WARN] STT 대상 파일을 찾을 수 없습니다: {path}")
        return ""

    try:
        with open(path, "rb") as f:
            return _call_whisper(f, language=language)
    except Exception as e:
        print(f"[WARN] 음성 파일 열기 실패: {e}")
        return ""


def transcribe_bytes(audio_bytes: bytes,
                     language: str = "ko",
                     file_name: Optional[str] = None) -> str:
    """
    메모리 상의 음성 바이트 데이터를 받아 텍스트로 변환합니다.

    - 마이크 녹음 버퍼, 웹소켓으로 받은 조각 등 사용 가능
    - file_name은 OpenAI API에 전달될 '가짜 파일 이름' 정도로만 사용됩니다.
      (확장자에 따라 포맷을 추측할 수 있으므로, 가능하면 지정하는 것이 좋습니다.)

    :param audio_bytes: 음성 데이터 (raw bytes)
    :param language: 음성 언어 코드
    :param file_name: 임시 파일명 (예: "recording.wav")
    :return: 인식된 텍스트 (실패 시 빈 문자열)
    """
    if not audio_bytes:
        print("[WARN] transcribe_bytes에 빈 바이트가 전달되었습니다.")
        return ""

    # BytesIO로 감싸서 파일처럼 사용
    bio = io.BytesIO(audio_bytes)
    # 일부 클라이언트 구현에서는 name 속성을 보고 포맷을 추측하기도 함
    if file_name:
        bio.name = file_name  # type: ignore[attr-defined]

    return _call_whisper(bio, language=language)


# -------------------------------------------------------------------
# 간단 CLI 테스트용
# -------------------------------------------------------------------

if __name__ == "__main__":
    print("Whisper STT 테스트 모드입니다.")
    print("음성 파일 경로를 입력하면 텍스트로 변환해 드립니다. (종료: 빈 줄)")

    while True:
        path = input("\n음성 파일 경로 > ").strip()
        if not path:
            print("종료합니다.")
            break

        text = transcribe_file(path)
        print("\n[인식 결과]")
        print(text if text else "(인식 실패 또는 빈 결과)")
