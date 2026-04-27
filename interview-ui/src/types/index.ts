// ---- Auth ----
export interface AuthResponse {
  access_token: string;
  token_type: string;
  username: string;
}

export interface UserInfo {
  id: number;
  username: string;
  email: string;
}

// ---- Interview Setup ----
export type Difficulty = "easy" | "mid" | "hard";

export interface InterviewStartPayload {
  resume?: File;
  job_description: string;
  topic: string;
  duration: number;
  difficulty: Difficulty;
}

// ---- Interview Session ----
export interface InterviewProgress {
  questions_asked: number;
  total_questions: number;
  current_topic: string;
  elapsed_seconds: number;
}

export interface Evaluation {
  technical_accuracy?: number;
  communication_clarity?: number;
  depth_of_knowledge?: number;
  relevance_to_role?: number;
  needs_follow_up?: boolean;
  brief_feedback?: string;
}

export interface QuestionPayload {
  question_text: string;
  question_number: number;
  total_questions: number;
  topic_phase: string;
  evaluation?: Evaluation;
  audio?: string;
  is_complete?: boolean;
  progress?: InterviewProgress;
}

export interface StartResponse {
  session_id: string;
  first_question: QuestionPayload;
  audio: string;
  progress: InterviewProgress;
}

// ---- WebSocket Messages ----
export interface WSQuestionMessage {
  type: "question";
  text: string;
  question_number: number;
  total_questions: number;
  topic_phase: string;
  evaluation: Evaluation;
  audio: string;
  is_complete: boolean;
  progress: InterviewProgress;
}

export interface WSReportMessage {
  type: "report";
  report: InterviewReport;
}

export interface WSErrorMessage {
  type: "error";
  message: string;
}

export type WSMessage = WSQuestionMessage | WSReportMessage | WSErrorMessage;

// ---- Report ----
export interface InterviewReport {
  overall_score: number;
  cracking_probability: number;
  technical_strengths: string[];
  areas_for_improvement: string[];
  specific_recommendations: string[];
  hiring_recommendation: string;
  summary: string;
  topic_scores: Record<string, number>;
}

// ---- History ----
export interface HistorySession {
  session_id: string;
  jd_text: string;
  difficulty: string;
  duration: number;
  overall_score: number;
  cracking_probability: number;
  hiring_recommendation: string;
  created_at: string;
}

export interface HistoryQA {
  question: string;
  answer: string;
  topic: string;
  evaluation: Evaluation;
}

// ---- Chat ----
export interface ChatMessage {
  id: string;
  sender: "ai" | "user";
  text: string;
  timestamp: number;
}
