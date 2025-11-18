export const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api/v1";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API 요청 실패: ${response.status} ${text}`);
  }
  const data = await response.json();
  if (!data.success) {
    const message = data.error?.message || "알 수 없는 오류가 발생했습니다.";
    throw new Error(message);
  }
  return data.data as T;
}

export async function startConversation(debugMode: boolean) {
  const res = await fetch(`${API_BASE}/conversations/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ debug_mode: debugMode }),
  });
  return handleResponse<{ session_uuid: string; status: string }>(res);
}

export async function sendAudio(sessionUuid: string, blob: Blob) {
  const formData = new FormData();
  formData.append("audio_file", blob, "recording.webm");
  const res = await fetch(`${API_BASE}/conversations/${sessionUuid}/stt`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<{ raw_text: string }>(res);
}

export async function analyzeText(sessionUuid: string, rawText: string) {
  const res = await fetch(`${API_BASE}/conversations/${sessionUuid}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw_text: rawText }),
  });
  return handleResponse<{
    summary_text: string;
    category: string;
    severity: string;
    handling_type: string;
    handling_desc: string;
  }>(res);
}

export async function confirmSummary(sessionUuid: string, isConfirmed: boolean) {
  const res = await fetch(`${API_BASE}/conversations/${sessionUuid}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ is_confirmed: isConfirmed }),
  });
  return handleResponse<{ next_step: string }>(res);
}

export async function finalizeComplaint(
  sessionUuid: string,
  payload: {
    raw_text: string;
    summary_text: string;
    category: string;
    severity: string;
    handling_type: string;
    handling_desc?: string;
    is_confirmed: boolean;
  },
) {
  const res = await fetch(`${API_BASE}/conversations/${sessionUuid}/finalize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<{ user_message: string; redirect: string }>(res);
}

export async function fetchLogs(sessionUuid?: string) {
  const params = sessionUuid ? `?session_uuid=${sessionUuid}` : "";
  const res = await fetch(`${API_BASE}/logs${params}`);
  return handleResponse<
    Array<{
      step: string;
      level: string;
      message: string;
      payload?: string;
      created_at: string;
    }>
  >(res);
}
