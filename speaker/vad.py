# -*- coding: utf-8 -*-
"""
vad.py

이 모듈은 pydub를 활용해서
'무음(silence)' 구간을 기준으로 음성을 잘라내는
간단한 VAD(Voice Activity Detection) 유틸리티입니다.

🎯 역할 요약
--------------------------------------
1. 음성 파일에서 앞·뒤 무음 제거 (trim_silence)
2. 음성 파일을 여러 발화(chunk)로 나누기 (split_into_chunks)
3. 각 chunk의 시작/끝 시각(sec)을 함께 반환

👉 pyannote.audio의 고급 diarization과는 별도로,
   단순히 "무음 기준으로 발화 단위 나누기"가 필요할 때 사용합니다.
"""

import os
from typing import List, Dict, Any

from pydub import AudioSegment
from pydub.silence import split_on_silence


# -------------------------------------------------------------------
# 공통 유틸
# -------------------------------------------------------------------

def load_audio(path: str) -> AudioSegment:
    """
    주어진 파일 경로에서 AudioSegment로 로드합니다.

    :param path: 오디오 파일 경로
    :return: AudioSegment 객체 (실패 시 Exception)
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {path}")
    return AudioSegment.from_file(path)


def trim_silence(audio: AudioSegment,
                 silence_thresh: int = -40,
                 padding_ms: int = 200) -> AudioSegment:
    """
    오디오 앞/뒤의 무음을 제거합니다.

    :param audio: AudioSegment 객체
    :param silence_thresh: 이 dBFS 이하를 '무음'으로 간주 (예: -40dBFS)
    :param padding_ms: 잘라낸 후 앞/뒤에 남길 여유(ms)
    :return: 앞/뒤 무음이 제거된 AudioSegment
    """
    # AudioSegment.dBFS 기준으로 상대값 사용
    # 너무 조용한 녹음의 경우 전체 dBFS가 작을 수 있으므로
    # 필요하면 호출 측에서 값을 조정해야 합니다.
    # 여기서는 간단히 split_on_silence 기준을 재사용하지 않고,
    # 앞/뒤만 간단히 잘라주는 버전이므로 정밀 VAD는 아닙니다.
    # (실제 프로덕션에서는 webrtcvad 등 고려 가능)
    # 일단은 "앞/뒤 긴 무음 제거" 용도로 충분.

    # 전체 길이가 너무 짧으면 그냥 반환
    if len(audio) < 2 * padding_ms:
        return audio

    # 앞쪽 무음 찾기: 처음 non-silence 샘플 위치
    start = 0
    for ms in range(0, len(audio), 10):
        if audio[ms:ms + 10].dBFS > silence_thresh:
            start = max(ms - padding_ms, 0)
            break

    # 뒤쪽 무음 찾기: 끝에서부터 non-silence
    end = len(audio)
    for ms in range(len(audio) - 10, 0, -10):
        if audio[ms:ms + 10].dBFS > silence_thresh:
            end = min(ms + padding_ms, len(audio))
            break

    return audio[start:end]


def split_into_chunks(path: str,
                      min_silence_len: int = 700,
                      silence_thresh: int = -40,
                      keep_silence: int = 300) -> List[Dict[str, Any]]:
    """
    음성 파일을 무음 기준으로 여러 chunk로 나눕니다.

    내부적으로 pydub.silence.split_on_silence를 사용하며,
    각 chunk의 시작/끝 시각(sec)과 AudioSegment를 함께 반환합니다.

    :param path: 오디오 파일 경로
    :param min_silence_len: 이 길이(ms) 이상이면서
                            silence_thresh보다 조용하면 '무음'으로 간주
    :param silence_thresh: 이 dBFS 이하를 무음으로 간주
    :param keep_silence: 분리된 chunk 양 끝에 남겨둘 무음(ms)
    :return: [
        {"index": 0, "start": 0.0, "end": 2.34, "audio": AudioSegment(...)},
        {"index": 1, "start": 2.34, "end": 5.80, "audio": AudioSegment(...)},
        ...
    ]
    """
    audio = load_audio(path)
    chunks = split_on_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=keep_silence,
    )

    results: List[Dict[str, Any]] = []

    # split_on_silence는 chunk의 절대 시간 정보를 주지 않기 때문에
    # 단순히 chunk 길이를 누적하면서 start/end를 계산합니다.
    cursor_ms = 0
    for idx, chunk in enumerate(chunks):
        duration_ms = len(chunk)
        start_sec = cursor_ms / 1000.0
        end_sec = (cursor_ms + duration_ms) / 1000.0

        results.append({
            "index": idx,
            "start": start_sec,
            "end": end_sec,
            "audio": chunk,
        })

        cursor_ms += duration_ms

    return results


# -------------------------------------------------------------------
# CLI 테스트용
# -------------------------------------------------------------------

if __name__ == "__main__":
    print("VAD(split_on_silence) 테스트 모드입니다.")
    print("음성 파일 경로를 입력하면, 무음 기준으로 chunk를 나눕니다. (종료: 빈 줄)")

    while True:
        path = input("\n음성 파일 경로 > ").strip()
        if not path:
            print("종료합니다.")
            break

        try:
            chunks = split_into_chunks(path)
        except Exception as e:
            print(f"[ERROR] 처리 중 오류: {e}")
            continue

        if not chunks:
            print("(chunk 없음 또는 전부 무음)")
            continue

        print(f"\n[총 {len(chunks)}개 chunk]")
        for ch in chunks:
            print(f"- index {ch['index']}: {ch['start']:.2f}s ~ {ch['end']:.2f}s, 길이={len(ch['audio'])/1000:.2f}s")
