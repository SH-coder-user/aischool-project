# -*- coding: utf-8 -*-
"""
diarization_pyannote.py

이 모듈은 pyannote.audio를 사용해서
'하나의 오디오 파일' 안에 있는 여러 화자를 구분하는 역할을 합니다.

🎯 역할 요약
--------------------------------------
1. .env 에서 HUGGINGFACE_TOKEN (pyannote용) 읽기
2. pyannote/speaker-diarization 파이프라인 로드
3. 오디오 파일 경로를 입력받아,
   시간 구간별 화자 라벨 목록을 반환
   [
     {"speaker": "SPEAKER_00", "start": 0.00, "end": 3.21},
     {"speaker": "SPEAKER_01", "start": 3.21, "end": 7.80},
     ...
   ]

👉 이 모듈은 '누가 언제 말했는지'만 담당합니다.
   - "무슨 말을 했는지" → stt_whisper.py (STT)
   - "그 말이 어떤 민원인지" → brain/minwon_engine.py
"""

import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from pyannote.audio import Pipeline

# pyannote.audio는 별도 설치가 필요합니다.
# pip install pyannote.audio torch --extra-index-url https://download.pytorch.org/whl/cu118
try:
    from pyannote.audio import Pipeline
except ImportError:
    Pipeline = None  # 타입만 맞춰두고, 실행 시 체크


# -------------------------------------------------------------------
# 환경 설정
# -------------------------------------------------------------------

load_dotenv()

# Hugging Face 토큰 (pyannote 모델 접근용)
# - https://huggingface.co/settings/tokens 에서 발급
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN") or os.getenv("PYANNOTE_TOKEN")


class PyannoteDiarizer:
    """
    pyannote.audio 기반 화자 분리 래퍼 클래스.

    한 번 인스턴스를 만들면 내부에서 파이프라인을 로드해두고,
    여러 오디오 파일에 대해 반복 사용 가능합니다.
    """

    def __init__(self,
                 hf_token: str | None = None,
                 model_name: str = "pyannote/speaker-diarization"):
        """
        :param hf_token: Hugging Face 토큰 (없으면 .env에서 HUGGINGFACE_TOKEN 사용)
        :param model_name: 사용할 diarization 모델 이름
        """
        if Pipeline is None:
            raise ImportError(
                "pyannote.audio가 설치되어 있지 않습니다. "
                "pip install pyannote.audio 로 설치해 주세요."
            )

        token = hf_token or HF_TOKEN
        if not token:
            raise RuntimeError(
                "HUGGINGFACE_TOKEN(또는 PYANNOTE_TOKEN)이 설정되어 있지 않습니다.\n"
                "Hugging Face 토큰을 발급받아 .env에 추가해 주세요."
            )

        # pyannote 파이프라인 로드
        # (처음 한 번 로드할 때 시간이 다소 걸릴 수 있음)
        self.pipeline = Pipeline.from_pretrained(
            model_name,
            use_auth_token=token,
        )

    # -------------------------------------------------------------
    # 공용 메인 함수
    # -------------------------------------------------------------

    def diarize_file(self, path: str) -> List[Dict[str, Any]]:
        """
        오디오 파일 경로를 받아서 화자별 시간 구간을 리스트로 반환합니다.

        :param path: 오디오 파일 경로 (.wav, .mp3, .m4a 등 지원 포맷)
        :return: [
            {"speaker": "SPEAKER_00", "start": 0.0, "end": 3.21},
            {"speaker": "SPEAKER_01", "start": 3.21, "end": 7.80},
            ...
        ]
        """
        if not os.path.exists(path):
            print(f"[WARN] diarize_file: 파일을 찾을 수 없습니다: {path}")
            return []

        # pyannote 파이프라인 실행
        try:
            diarization = self.pipeline(path)
        except Exception as e:
            print(f"[WARN] pyannote diarization 호출 중 오류 발생: {e}")
            return []

        segments: List[Dict[str, Any]] = []

        # diarization 결과는 "timeline" 형식으로 나옴
        # segment: 시간 구간, track: 화자 라벨
        # ex) segment.start, segment.end, track == "SPEAKER_00"
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            seg = {
                "speaker": speaker,
                "start": float(turn.start),
                "end": float(turn.end),
            }
            segments.append(seg)

        # 시작 시간 기준으로 정렬
        segments.sort(key=lambda s: s["start"])
        return segments


# -------------------------------------------------------------------
# 간단 CLI 테스트용 코드
# -------------------------------------------------------------------

if __name__ == "__main__":
    print("pyannote.audio 화자 분리 테스트 모드입니다.")
    print("오디오 파일 경로를 입력하면, 화자별 구간을 출력합니다. (종료: 빈 줄)")

    try:
        diarizer = PyannoteDiarizer()
    except Exception as e:
        print(f"[ERROR] PyannoteDiarizer 초기화 실패: {e}")
        raise SystemExit(1)

    while True:
        path = input("\n오디오 파일 경로 > ").strip()
        if not path:
            print("종료합니다.")
            break

        segments = diarizer.diarize_file(path)
        if not segments:
            print("(결과 없음 또는 오류)")
            continue

        print("\n[화자 분리 결과]")
        for seg in segments:
            speaker = seg["speaker"]
            start = seg["start"]
            end = seg["end"]
            print(f"- {speaker}: {start:.2f}s ~ {end:.2f}s")
