import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import Layout from "../components/Layout";
import {
  analyzeText,
  confirmSummary,
  finalizeComplaint,
  sendAudio,
} from "../api/client";
import type { AnalyzeResult, ConversationStep } from "../types/conversation";

export default function ConversationPage() {
  const [params] = useSearchParams();
  const sessionUuid = params.get("session") || "";
  const debugMode = params.get("debug") === "1";
  const navigate = useNavigate();

  const [step, setStep] = useState<ConversationStep>("RECORDING");
  const [rawText, setRawText] = useState("");
  const [analysis, setAnalysis] = useState<AnalyzeResult | null>(null);
  const [resultMessage, setResultMessage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    if (!sessionUuid) {
      navigate("/");
    }
  }, [sessionUuid, navigate]);

  const headerLabel = useMemo(() => {
    if (step === "RECORDING") return "녹음 중";
    if (step === "PROCESSING") return "처리 중";
    if (step === "CONFIRMING") return "결과 확인";
    if (step === "RESULT") return "완료";
    return "대화";
  }, [step]);

  const startRecording = async () => {
    setError(null);
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("마이크 접근을 지원하지 않는 브라우저입니다.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        await processAudio(blob);
      };
      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);
      setStep("RECORDING");
    } catch (err) {
      console.error(err);
      setError("마이크 권한을 허용해 주세요.");
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
    setStep("PROCESSING");
  };

  const processAudio = async (blob: Blob) => {
    setStep("PROCESSING");
    try {
      const stt = await sendAudio(sessionUuid, blob);
      setRawText(stt.raw_text);
      await runAnalysis(stt.raw_text);
    } catch (err) {
      console.error(err);
      setError("음성 인식 중 오류가 발생했습니다.");
      setStep("RECORDING");
    }
  };

  const runAnalysis = async (text: string) => {
    setStep("PROCESSING");
    try {
      const data = await analyzeText(sessionUuid, text);
      setAnalysis(data);
      setStep("CONFIRMING");
    } catch (err) {
      console.error(err);
      setError("요약/분류 중 오류가 발생했습니다.");
      setStep("RECORDING");
    }
  };

  const handleRetry = () => {
    setAnalysis(null);
    setRawText("");
    setStep("RECORDING");
  };

  const handleConfirm = async () => {
    if (!analysis) return;
    try {
      await confirmSummary(sessionUuid, true);
      const finalized = await finalizeComplaint(sessionUuid, {
        raw_text: rawText,
        summary_text: analysis.summary_text,
        category: analysis.category,
        severity: analysis.severity,
        handling_type: analysis.handling_type,
        handling_desc: analysis.handling_desc,
        is_confirmed: true,
      });
      setResultMessage(finalized.user_message);
      setStep("RESULT");
    } catch (err) {
      console.error(err);
      setError("최종 저장 중 오류가 발생했습니다.");
    }
  };

  const handleDebugSubmit = async () => {
    if (!rawText.trim()) {
      setError("텍스트를 입력해 주세요.");
      return;
    }
    await runAnalysis(rawText);
  };

  const renderBody = () => {
    if (step === "PROCESSING") {
      return "말씀하신 내용을 정리하는 중입니다…";
    }
    if (step === "CONFIRMING" && analysis) {
      return (
        <div style={{ fontSize: "48px", fontWeight: 800, lineHeight: 1.3 }}>
          <div style={{ marginBottom: "24px" }}>이렇게 이해했어요</div>
          <div
            style={{
              background: "#FFF5C4",
              borderRadius: "24px",
              padding: "32px",
              textAlign: "left",
            }}
          >
            <div style={{ marginBottom: "12px" }}>{analysis.summary_text}</div>
            <div style={{ fontSize: "32px", fontWeight: 700 }}>
              분류: {analysis.category} · 긴급도: {analysis.severity}
            </div>
            <div style={{ fontSize: "32px", fontWeight: 700 }}>
              처리: {analysis.handling_type}
            </div>
          </div>
        </div>
      );
    }
    if (step === "RESULT") {
      return (
        <div style={{ fontSize: "48px", fontWeight: 800, lineHeight: 1.4 }}>
          <div style={{ marginBottom: "12px" }}>처리 안내</div>
          <div
            style={{
              background: "#FFF5C4",
              borderRadius: "24px",
              padding: "32px",
              textAlign: "left",
            }}
          >
            {resultMessage}
          </div>
        </div>
      );
    }
    if (debugMode) {
      return (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "16px",
            width: "100%",
            alignItems: "center",
          }}
        >
          <textarea
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            placeholder="디버그 모드: 텍스트를 입력하세요"
            style={{ width: "80%", height: "200px", fontSize: "28px" }}
          />
          <button
            type="button"
            onClick={handleDebugSubmit}
            style={{
              background: "#FBDA05",
              color: "#000",
              fontSize: "40px",
              fontWeight: 800,
              borderRadius: "24px",
              padding: "24px 48px",
              border: "none",
            }}
          >
            분석하기
          </button>
        </div>
      );
    }
    return (
      <div style={{ fontSize: "56px", fontWeight: 800 }}>
        {isRecording ? "녹음 중입니다. 버튼을 눌러 종료하세요." : "버튼을 눌러 녹음을 시작하세요."}
      </div>
    );
  };

  return (
    <Layout
      title={headerLabel}
      content={
        step === "CONFIRMING"
          ? "이런 내용이 맞나요?"
          : step === "RESULT"
            ? "처리 내용 안내"
            : "민원을 말씀해주세요"
      }
      headerImage="src/assets/duck1.png"
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "20px",
          width: "100%",
        }}
      >
        {renderBody()}
        {error && (
          <div style={{ color: "#c62828", fontSize: "28px", fontWeight: 700 }}>
            {error}
          </div>
        )}

        {step === "RECORDING" && !debugMode && (
          <button
            type="button"
            onClick={isRecording ? stopRecording : startRecording}
            style={{
              background: isRecording ? "#FFB703" : "#FBDA05",
              color: "#000",
              fontSize: "56px",
              fontWeight: 800,
              borderRadius: "32px",
              padding: "28px 64px",
              border: "none",
              width: "80%",
              boxShadow: "0 12px 0 #d1b504",
            }}
          >
            {isRecording ? "녹음 종료" : "녹음 시작"}
          </button>
        )}

        {step === "CONFIRMING" && (
          <div style={{ display: "flex", gap: "24px" }}>
            <button
              type="button"
              onClick={handleConfirm}
              style={{
                background: "#43A047",
                color: "#fff",
                fontSize: "40px",
                fontWeight: 800,
                borderRadius: "24px",
                padding: "24px 48px",
                border: "none",
              }}
            >
              네, 맞아요
            </button>
            <button
              type="button"
              onClick={handleRetry}
              style={{
                background: "#E53935",
                color: "#fff",
                fontSize: "40px",
                fontWeight: 800,
                borderRadius: "24px",
                padding: "24px 48px",
                border: "none",
              }}
            >
              아니에요
            </button>
          </div>
        )}

        {step === "RESULT" && (
          <button
            type="button"
            onClick={() => navigate("/")}
            style={{
              background: "#FBDA05",
              color: "#000",
              fontSize: "48px",
              fontWeight: 800,
              borderRadius: "24px",
              padding: "24px 48px",
              border: "none",
            }}
          >
            처음으로 돌아가기
          </button>
        )}
      </div>
    </Layout>
  );
}
