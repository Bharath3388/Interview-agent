"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  Send,
  Mic,
  MicOff,
  Square,
  Bot,
  User as UserIcon,
  Clock,
} from "lucide-react";
import Logo from "@/components/ui/Logo";
import Button from "@/components/ui/Button";
import { createInterviewWS } from "@/lib/api";
import { formatTime, playBase64Audio } from "@/lib/utils";
import type {
  ChatMessage,
  InterviewProgress,
  WSMessage,
} from "@/types";

export default function InterviewPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [progress, setProgress] = useState<InterviewProgress | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [status, setStatus] = useState("Connecting...");

  const wsRef = useRef<WebSocket | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const inputRef = useRef(""); // always mirrors latest input for sync reads
  const messagesInitRef = useRef(false); // prevent duplicate first-question messages
  const sessionDataRef = useRef<string | null>(null);
  const sessionIdRef = useRef<string>("");
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Keep inputRef in sync with input state
  useEffect(() => {
    inputRef.current = input;
  }, [input]);

  // Scroll to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  // Auth guard
  useEffect(() => {
    if (!authLoading && !user) router.replace("/auth");
  }, [user, authLoading, router]);

  // Timer
  useEffect(() => {
    timerRef.current = setInterval(() => setElapsed((p) => p + 1), 1000);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  // Helper: send text via WS
  const sendViaWS = useCallback((text: string) => {
    if (!text) return;
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.warn("[Interview] WS not open, cannot send:", wsRef.current?.readyState);
      return;
    }
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), sender: "user", text, timestamp: Date.now() },
    ]);
    setInput("");
    inputRef.current = "";
    setIsThinking(true);
    setStatus("Thinking...");
    wsRef.current.send(JSON.stringify({ action: "text", text }));
  }, []);

  // Handle incoming WS messages
  const handleWSMessage = useCallback(
    (msg: WSMessage) => {
      setIsThinking(false);

      if (msg.type === "question") {
        setMessages((prev) => [
          ...prev,
          { id: crypto.randomUUID(), sender: "ai", text: msg.text, timestamp: Date.now() },
        ]);
        setProgress(msg.progress);
        setStatus("Ready");

        if (msg.audio) {
          playBase64Audio(
            msg.audio,
            () => { setIsSpeaking(true); setStatus("Speaking..."); },
            () => { setIsSpeaking(false); setStatus("Ready"); }
          );
        }

        if (msg.is_complete) {
          setStatus("Interview Complete");
        }
      } else if (msg.type === "report") {
        sessionStorage.setItem("interviewReport", JSON.stringify(msg.report));
        router.push("/report");
      } else if (msg.type === "error") {
        setMessages((prev) => [
          ...prev,
          { id: crypto.randomUUID(), sender: "ai", text: `Error: ${msg.message}`, timestamp: Date.now() },
        ]);
        setStatus("Error");
      }
    },
    [router]
  );

  // Initialize session + WebSocket
  // This effect runs twice in React 18 strict mode. The cleanup closes the WS,
  // and the second run recreates it. messagesInitRef prevents duplicate messages.
  useEffect(() => {
    if (!sessionDataRef.current) {
      sessionDataRef.current = sessionStorage.getItem("interviewSession");
    }
    const raw = sessionDataRef.current;
    if (!raw) {
      router.replace("/setup");
      return;
    }

    const session = JSON.parse(raw);
    const { sessionId, firstQuestion, audio, progress: initProgress } = session;
    sessionIdRef.current = sessionId;

    // Add first question + play audio only once
    if (!messagesInitRef.current) {
      messagesInitRef.current = true;
      setProgress(initProgress);
      setMessages([{
        id: crypto.randomUUID(),
        sender: "ai",
        text: firstQuestion.question_text,
        timestamp: Date.now(),
      }]);
      if (audio) {
        playBase64Audio(
          audio,
          () => setIsSpeaking(true),
          () => setIsSpeaking(false)
        );
      }
    }

    // ALWAYS create a fresh WebSocket (handles strict mode re-mount)
    const ws = createInterviewWS(sessionId);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("[Interview] WS connected");
      setStatus("Ready");
    };
    ws.onclose = () => {
      console.log("[Interview] WS closed");
      setStatus("Disconnected");
    };
    ws.onerror = (e) => {
      console.error("[Interview] WS error", e);
      setStatus("Connection error");
    };
    ws.onmessage = (evt) => {
      const msg: WSMessage = JSON.parse(evt.data);
      handleWSMessage(msg);
    };

    return () => {
      ws.close();
    };
  }, [router, handleWSMessage]);

  // ---- Send typed text ----
  const sendText = () => {
    const text = input.trim();
    if (text) sendViaWS(text);
  };

  // ---- End interview ----
  const endInterview = async () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      setIsThinking(true);
      setStatus("Generating report...");
      wsRef.current.send(JSON.stringify({ action: "end" }));
      return;
    }
    if (!sessionIdRef.current) {
      router.replace("/setup");
      return;
    }
    try {
      setIsThinking(true);
      setStatus("Generating report...");
      const token = localStorage.getItem("authToken");
      const res = await fetch(`/api/interview/${sessionIdRef.current}/end`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        if (data.report) {
          sessionStorage.setItem("interviewReport", JSON.stringify(data.report));
          router.push("/report");
        }
      } else {
        router.replace("/setup");
      }
    } catch {
      router.replace("/setup");
    }
  };

  // ---- Speech Recognition ----
  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const startRecording = () => {
    const SR =
      (window as unknown as { SpeechRecognition?: typeof window.SpeechRecognition }).SpeechRecognition ||
      (window as unknown as { webkitSpeechRecognition?: typeof window.SpeechRecognition }).webkitSpeechRecognition;
    if (!SR) {
      setStatus("Speech recognition not supported");
      return;
    }

    const recognition = new SR();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    const SILENCE_MS = 5000;

    const resetSilenceTimer = () => {
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = setTimeout(() => {
        // Auto-stop after silence — grab text and send
        doStopAndSend();
      }, SILENCE_MS);
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let full = "";
      for (let i = 0; i < event.results.length; i++) {
        full += event.results[i][0].transcript;
        if (event.results[i].isFinal) full += " ";
      }
      full = full.trim();
      setInput(full);
      inputRef.current = full;
      resetSilenceTimer();
    };

    recognition.onerror = () => {
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      setIsRecording(false);
      setStatus("Ready");
    };

    recognition.onend = () => {
      // Just update UI state — sending is handled by doStopAndSend
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      setIsRecording(false);
    };

    recognition.start();
    recognitionRef.current = recognition;
    setIsRecording(true);
    setStatus("Listening...");
    resetSilenceTimer();
  };

  // Grab whatever text is displayed and send it, then stop recognition
  const doStopAndSend = () => {
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);

    // Read the current input text synchronously from the ref
    const text = inputRef.current.trim();

    // Stop recognition (will trigger onend for UI cleanup)
    try { recognitionRef.current?.stop(); } catch { /* already stopped */ }

    if (text) {
      sendViaWS(text);
    } else {
      setStatus("Ready");
    }
  };

  const stopRecording = () => {
    doStopAndSend();
  };

  const progressPct = progress
    ? Math.min(((progress.questions_asked) / progress.total_questions) * 100, 100)
    : 0;

  if (authLoading || !user) return null;

  return (
    <div className="h-screen flex flex-col bg-[#0f0f23]">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-white/5 bg-white/[0.02] backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <Logo size="sm" />
          <span className="text-sm font-bold gradient-text hidden sm:block">AI Interview</span>
        </div>

        {/* Progress */}
        <div className="flex-1 max-w-sm mx-6">
          <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
            <span>
              Question {Math.min((progress?.questions_asked || 0) + 1, progress?.total_questions || 7)} of{" "}
              {progress?.total_questions || 7}
            </span>
            <span className="capitalize">{progress?.current_topic || "Interview"}</span>
          </div>
          <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary to-accent rounded-full transition-all duration-700"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Timer */}
          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-300 bg-white/5 px-3 py-1.5 rounded-lg">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            {formatTime(elapsed)}
          </div>

          {/* Status */}
          <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400 bg-white/5 px-3 py-1.5 rounded-lg">
            <div
              className={`w-1.5 h-1.5 rounded-full ${
                status === "Ready"
                  ? "bg-emerald-400"
                  : status.includes("error") || status === "Disconnected"
                  ? "bg-red-400"
                  : "bg-amber-400 animate-pulse"
              }`}
            />
            {status}
          </div>

          {/* End Button */}
          <Button variant="danger" size="sm" onClick={endInterview}>
            <Square className="w-3 h-3" />
            End
          </Button>
        </div>
      </header>

      {/* Chat Area */}
      <main className="flex-1 flex overflow-hidden">
        {/* Avatar Sidebar */}
        <aside className="hidden lg:flex flex-col items-center w-64 border-r border-white/5 bg-white/[0.01] py-8 px-4">
          <div className="relative mb-4">
            {/* Avatar */}
            <div
              className={`w-32 h-32 rounded-full bg-gradient-to-br from-primary/20 to-accent/20 border-2 ${
                isSpeaking ? "border-primary animate-pulse" : "border-white/10"
              } flex items-center justify-center transition-all duration-300`}
            >
              <Bot className="w-16 h-16 text-primary-light" />
            </div>
            {/* Speaking rings */}
            {isSpeaking && (
              <>
                <div className="absolute inset-0 rounded-full border-2 border-primary/30 speak-ring" />
                <div className="absolute inset-0 rounded-full border-2 border-primary/20 speak-ring" />
              </>
            )}
          </div>
          <h3 className="text-sm font-semibold text-white mb-1">AI Interviewer</h3>
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <div
              className={`w-1.5 h-1.5 rounded-full ${
                isSpeaking ? "bg-primary animate-pulse" : "bg-emerald-400"
              }`}
            />
            {isSpeaking ? "Speaking" : "Listening"}
          </div>

          {/* Topic Badge */}
          <div className="mt-6 w-full">
            <div className="glass rounded-xl px-4 py-3 text-center">
              <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Current Topic</div>
              <div className="text-sm font-medium text-slate-200 capitalize">
                {progress?.current_topic || "Introduction"}
              </div>
            </div>
          </div>
        </aside>

        {/* Chat Messages */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-4 space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex items-start gap-3 animate-slide-up ${
                  msg.sender === "user" ? "flex-row-reverse" : ""
                }`}
              >
                {/* Avatar */}
                <div
                  className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    msg.sender === "ai"
                      ? "bg-gradient-to-br from-primary to-accent"
                      : "bg-slate-700"
                  }`}
                >
                  {msg.sender === "ai" ? (
                    <Bot className="w-4 h-4 text-white" />
                  ) : (
                    <UserIcon className="w-4 h-4 text-slate-300" />
                  )}
                </div>

                {/* Bubble */}
                <div
                  className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                    msg.sender === "ai"
                      ? "bg-white/[0.06] border border-white/10 text-slate-200 rounded-tl-md"
                      : "bg-gradient-to-r from-primary to-primary-dark text-white rounded-tr-md"
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}

            {/* Typing Indicator */}
            {isThinking && (
              <div className="flex items-start gap-3 animate-slide-up">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-white/[0.06] border border-white/10 rounded-2xl rounded-tl-md px-5 py-3.5">
                  <div className="flex gap-1.5">
                    <div className="w-2 h-2 bg-slate-400 rounded-full typing-dot" />
                    <div className="w-2 h-2 bg-slate-400 rounded-full typing-dot" />
                    <div className="w-2 h-2 bg-slate-400 rounded-full typing-dot" />
                  </div>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-white/5 bg-white/[0.02] px-4 sm:px-6 py-4">
            <div className="max-w-3xl mx-auto">
              <div className="flex items-center gap-3">
                {/* Text Input */}
                <div className="flex-1 flex items-center gap-2 glass rounded-xl px-4 py-2 focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/20 transition-all">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && sendText()}
                    placeholder="Type your answer..."
                    className="flex-1 bg-transparent text-sm text-slate-100 placeholder:text-slate-500 outline-none"
                  />
                  <button
                    onClick={sendText}
                    disabled={!input.trim()}
                    className="text-slate-400 hover:text-primary-light disabled:opacity-30 transition-colors"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>

                {/* Mic Button */}
                <button
                  onClick={toggleRecording}
                  className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 ${
                    isRecording
                      ? "bg-red-500 text-white shadow-lg shadow-red-500/30 animate-pulse"
                      : "bg-white/5 border border-white/10 text-slate-400 hover:text-primary-light hover:border-primary/30"
                  }`}
                >
                  {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                </button>
              </div>
              <p className="text-center text-[11px] text-slate-600 mt-2">
                {isRecording ? "Listening... Click mic to stop & send" : "Press Enter to send or click the mic to speak"}
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
