import { useEffect, useState } from "react";
import Layout from "../components/Layout";
import { analyzeText, fetchLogs } from "../api/client";
import type { AnalyzeResult } from "../types/conversation";

export default function DebugPage() {
  const [sessionUuid, setSessionUuid] = useState("");
  const [inputText, setInputText] = useState("");
  const [analysis, setAnalysis] = useState<AnalyzeResult | null>(null);
  const [logs, setLogs] = useState<
    Array<{ step: string; level: string; message: string; payload?: string; created_at: string }>
  >([]);

  useEffect(() => {
    if (sessionUuid) {
      loadLogs(sessionUuid);
    }
  }, [sessionUuid]);

  const loadLogs = async (session?: string) => {
    try {
      const data = await fetchLogs(session);
      setLogs(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleAnalyze = async () => {
    if (!sessionUuid || !inputText) return;
    const data = await analyzeText(sessionUuid, inputText);
    setAnalysis(data);
    loadLogs(sessionUuid);
  };

  return (
    <Layout
      title="디버그 모드"
      content={`텍스트 입력 후 분류 결과와\n로그를 확인하세요`}
      headerImage="src/assets/duck1.png"
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "16px",
          width: "90%",
          maxWidth: "1200px",
        }}
      >
        <input
          type="text"
          placeholder="세션 UUID"
          value={sessionUuid}
          onChange={(e) => setSessionUuid(e.target.value)}
          style={{ fontSize: "24px", padding: "12px", borderRadius: "12px", border: "1px solid #ccc" }}
        />
        <textarea
          placeholder="디버그용 텍스트 입력"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          style={{ height: "160px", fontSize: "24px", padding: "12px", borderRadius: "12px", border: "1px solid #ccc" }}
        />
        <button
          type="button"
          onClick={handleAnalyze}
          style={{
            background: "#FBDA05",
            color: "#000",
            fontSize: "32px",
            fontWeight: 800,
            borderRadius: "18px",
            padding: "18px 24px",
            border: "none",
            alignSelf: "flex-start",
          }}
        >
          분석 및 로그 새로고침
        </button>

        {analysis && (
          <div
            style={{
              background: "#FFF5C4",
              borderRadius: "18px",
              padding: "18px",
              fontSize: "24px",
              fontWeight: 700,
            }}
          >
            <div>요약: {analysis.summary_text}</div>
            <div>
              분류: {analysis.category} · 긴급도: {analysis.severity} · 처리: {analysis.handling_type}
            </div>
            <div>비고: {analysis.handling_desc}</div>
          </div>
        )}

        <div
          style={{
            background: "#f7f7f7",
            borderRadius: "18px",
            padding: "18px",
            maxHeight: "260px",
            overflow: "auto",
            fontSize: "20px",
          }}
        >
          {logs.length === 0 && <div>로그가 없습니다.</div>}
          {logs.map((log, idx) => (
            <div key={`${log.created_at}-${idx}`} style={{ marginBottom: "12px" }}>
              <div style={{ fontWeight: 800 }}>
                [{log.step}] {log.level} - {log.created_at}
              </div>
              <div>{log.message}</div>
              {log.payload && (
                <div style={{ fontFamily: "monospace", whiteSpace: "pre-wrap" }}>{log.payload}</div>
              )}
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
