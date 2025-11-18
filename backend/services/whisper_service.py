import hashlib
from typing import Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None


def transcribe_audio(audio_bytes: bytes, filename: str, api_key: Optional[str] = None) -> str:
    """Return a lightweight transcript placeholder.

    The function tries to use OpenAI Whisper when an API key and dependency
    are available. Otherwise it falls back to a deterministic stub so the
    endpoint can still behave in offline demos.
    """

    if OpenAI and api_key:
        try:
            client = OpenAI(api_key=api_key)
            transcript = client.audio.transcriptions.create(
                file=(filename, audio_bytes, "audio/wav"),
                model="whisper-1",
                language="ko",
            )
            text = getattr(transcript, "text", "").strip()
            if text:
                return text
        except Exception:
            # fall back to stub when external call fails
            pass

    # Offline fallback: use file hash to make deterministic placeholder text
    digest = hashlib.sha256(audio_bytes).hexdigest()[:8]
    return f"음성 메모를 인식했습니다({filename}, {digest})."
