export type ConversationStep = "IDLE" | "RECORDING" | "PROCESSING" | "CONFIRMING" | "RESULT";

export interface AnalyzeResult {
  summary_text: string;
  category: string;
  severity: string;
  handling_type: string;
  handling_desc: string;
}
