import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../components/Layout";
import { startConversation } from "../api/client";

export default function MainPage() {
  const [debugMode, setDebugMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleStart = async () => {
    setLoading(true);
    try {
      const res = await startConversation(debugMode);
      navigate(`/conversation?session=${res.session_uuid}&debug=${debugMode ? 1 : 0}`);
    } catch (err) {
      console.error(err);
      alert("대화를 시작할 수 없습니다. 서버 상태를 확인해 주세요.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout
      title="대화 시작"
      content={`버튼을 눌러
말씀을 시작해 주세요`}
      headerImage="src/assets/duck1.png"
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "24px",
          alignItems: "center",
          width: "100%",
        }}
      >
        <button
          type="button"
          onClick={handleStart}
          disabled={loading}
          style={{
            background: "#FBDA05",
            color: "#000",
            fontSize: "64px",
            fontWeight: 800,
            borderRadius: "32px",
            padding: "32px 64px",
            border: "none",
            width: "80%",
            cursor: "pointer",
            boxShadow: "0 12px 0 #d1b504",
          }}
        >
          {loading ? "준비 중..." : "대화 시작"}
        </button>

        <label
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            fontSize: "32px",
            fontWeight: 700,
          }}
        >
          <input
            type="checkbox"
            checked={debugMode}
            onChange={(e) => setDebugMode(e.target.checked)}
            style={{ width: "32px", height: "32px" }}
          />
          디버그 모드로 진행
        </label>
      </div>
    </Layout>
  );
}
