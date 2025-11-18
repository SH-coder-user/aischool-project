from dataclasses import dataclass
from typing import Dict, Tuple

EMERGENCY_KEYWORDS = ["쓰러", "화재", "불이", "폭발", "위험", "위독", "사고", "피가", "폭행"]
FACILITY_KEYWORDS = ["가로등", "도로", "보도", "나무", "쓰러져", "전선", "쓰레기", "시설", "건물"]
PENSION_KEYWORDS = ["연금", "국민연금", "기초연금", "수급", "복지"]
MENTAL_KEYWORDS = ["우울", "불안", "상담", "심리", "괴로", "힘들", "죽고 싶"]


@dataclass
class AnalysisResult:
    summary_text: str
    category: str
    severity: str
    handling_type: str
    handling_desc: str


def summarize(raw_text: str) -> str:
    raw_text = raw_text.strip()
    if len(raw_text) <= 50:
        return raw_text
    return raw_text[:120].rstrip() + "…"


def detect_category(raw_text: str) -> str:
    lowered = raw_text.lower()
    if any(k in raw_text for k in MENTAL_KEYWORDS):
        return "MENTAL_HEALTH"
    if any(k in raw_text for k in PENSION_KEYWORDS):
        return "PENSION"
    if any(k in raw_text for k in FACILITY_KEYWORDS):
        return "FACILITY"
    return "OTHER"


def detect_severity(raw_text: str, category: str) -> str:
    normalized = raw_text.lower()
    if any(k in normalized for k in EMERGENCY_KEYWORDS):
        return "EMERGENCY"
    if category == "MENTAL_HEALTH" and "힘들" in normalized:
        return "NORMAL"
    return "NORMAL" if len(raw_text) > 0 else "LOW"


def decide_handling(category: str, severity: str) -> Tuple[str, str]:
    if category == "FACILITY":
        if severity == "EMERGENCY":
            return (
                "ON_SITE_VISIT",
                "담당자가 현장을 방문하여 쓰러진 나무나 위험 요소를 즉시 확인합니다.",
            )
        return (
            "ON_SITE_VISIT",
            "시설 담당자가 현장을 확인하고 필요한 조치를 진행합니다.",
        )
    if category == "PENSION":
        return (
            "INFO_GUIDE",
            "국민연금이나 복지 안내를 확인한 뒤 필요한 정보를 안내드립니다.",
        )
    if category == "MENTAL_HEALTH":
        if severity == "EMERGENCY":
            return (
                "COUNSELOR_CONNECT",
                "위기 징후가 감지되어 전문 상담 연결을 도와드립니다.",
            )
        return (
            "LISTENING_SUPPORT",
            "상담사를 연결하거나 가까운 지원 기관 연락처를 안내드립니다.",
        )
    return (
        "INFO_GUIDE",
        "민원 내용을 담당자에게 전달하고 추가 안내를 제공합니다.",
    )


def analyze_text(raw_text: str) -> AnalysisResult:
    category = detect_category(raw_text)
    severity = detect_severity(raw_text, category)
    handling_type, handling_desc = decide_handling(category, severity)
    return AnalysisResult(
        summary_text=summarize(raw_text),
        category=category,
        severity=severity,
        handling_type=handling_type,
        handling_desc=handling_desc,
    )


def format_user_message(result: AnalysisResult) -> str:
    return (
        f"말씀해 주신 내용은 '{result.summary_text}'로 정리되었어요. "
        f"카테고리: {result.category}, 긴급도: {result.severity} 기준으로 "
        f"처리 유형 '{result.handling_type}'을 안내합니다."
    )
