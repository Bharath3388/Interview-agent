"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import {
  FileText,
  Briefcase,
  Clock,
  BarChart3,
  Upload,
  LogOut,
  Play,
  History,
  Sparkles,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Logo from "@/components/ui/Logo";
import { apiStartInterview } from "@/lib/api";
import type { Difficulty } from "@/types";

export default function SetupPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [duration, setDuration] = useState(15);
  const [difficulty, setDifficulty] = useState<Difficulty>("mid");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!loading && !user) router.replace("/auth");
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const handleStart = async () => {
    setError("");
    setBusy(true);
    try {
      const fd = new FormData();
      if (resumeFile) fd.append("resume", resumeFile);
      fd.append("job_description", jobDescription);
      fd.append("topic", jobDescription);
      fd.append("duration", String(duration));
      fd.append("difficulty", difficulty);

      const data = await apiStartInterview(fd);

      // Store session data for the interview page
      sessionStorage.setItem(
        "interviewSession",
        JSON.stringify({
          sessionId: data.session_id,
          firstQuestion: data.first_question,
          audio: data.audio,
          progress: data.progress,
        })
      );

      router.push("/interview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start interview");
    } finally {
      setBusy(false);
    }
  };

  const difficultyOptions = [
    { value: "easy" as Difficulty, label: "Easy", desc: "Entry Level", color: "from-emerald-500 to-emerald-600" },
    { value: "mid" as Difficulty, label: "Mid", desc: "Intermediate", color: "from-amber-500 to-orange-500" },
    { value: "hard" as Difficulty, label: "Hard", desc: "Senior / Staff", color: "from-red-500 to-rose-600" },
  ];

  const durationOptions = [
    { value: 10, label: "10 min", questions: "~5 questions" },
    { value: 15, label: "15 min", questions: "~7 questions" },
    { value: 20, label: "20 min", questions: "~10 questions" },
    { value: 30, label: "30 min", questions: "~15 questions" },
  ];

  return (
    <div className="h-screen flex flex-col bg-[radial-gradient(ellipse_at_20%_50%,rgba(99,102,241,0.15),transparent_60%),radial-gradient(ellipse_at_80%_20%,rgba(168,85,247,0.1),transparent_50%)] overflow-hidden">
      {/* Top bar */}
      <header className="flex items-center justify-between px-6 py-2.5 border-b border-white/5 flex-shrink-0">
        <div className="flex items-center gap-3">
          <Logo size="sm" />
          <span className="text-lg font-bold gradient-text">AI Interview Agent</span>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push("/history")}
            className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
          >
            <History className="w-4 h-4" />
            History
          </button>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-400">
              Hi, <span className="text-slate-200 font-medium">{user.username}</span> 👋
            </span>
            <button
              onClick={logout}
              className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-red-400 transition-colors border border-white/10 rounded-full px-3 py-1 hover:border-red-500/30"
            >
              <LogOut className="w-3 h-3" />
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Main Content — fills remaining viewport */}
      <main className="flex-1 flex flex-col justify-center max-w-4xl w-full mx-auto px-6 py-4 animate-fade-in">
        {/* Compact Header */}
        <div className="text-center mb-5">
          <div className="inline-flex items-center gap-2 bg-primary/10 border border-primary/20 text-primary-light text-xs font-medium px-3 py-1 rounded-full mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            AI-Powered Mock Interviews
          </div>
          <h1 className="text-2xl font-extrabold text-white">
            Start Your Interview
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            Practice with an AI interviewer that adapts to your skills and experience
          </p>
        </div>

        {/* Two-column form layout */}
        <div className="grid grid-cols-2 gap-4">
          {/* Left Column */}
          <div className="space-y-4">
            {/* Resume Upload — compact */}
            <div className="glass rounded-xl p-4">
              <label className="flex items-center gap-2 text-xs font-semibold text-slate-200 mb-2">
                <FileText className="w-3.5 h-3.5 text-slate-400" />
                Resume (PDF or DOCX)
              </label>
              <label
                className={`flex items-center gap-3 border-2 border-dashed rounded-lg px-4 py-3 cursor-pointer transition-all duration-200 ${
                  resumeFile
                    ? "border-primary/50 bg-primary/5"
                    : "border-white/10 hover:border-primary/30 hover:bg-white/[0.02]"
                }`}
              >
                <input
                  type="file"
                  accept=".pdf,.docx"
                  className="hidden"
                  onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
                />
                <Upload className={`w-5 h-5 flex-shrink-0 ${resumeFile ? "text-primary-light" : "text-slate-500"}`} />
                <span className={`text-xs truncate ${resumeFile ? "text-primary-light font-medium" : "text-slate-400"}`}>
                  {resumeFile ? resumeFile.name : "Drop resume here or click to browse"}
                </span>
              </label>
            </div>

            {/* Job Description — compact */}
            <div className="glass rounded-xl p-4">
              <label className="flex items-center gap-2 text-xs font-semibold text-slate-200 mb-2">
                <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                Job Description or Topic
              </label>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste JD, or type a topic like 'Senior React Developer'..."
                rows={4}
                className="w-full px-3 py-2.5 bg-white/[0.06] border border-white/10 rounded-lg text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all resize-none"
              />
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-4">
            {/* Duration — compact inline */}
            <div className="glass rounded-xl p-4">
              <label className="flex items-center gap-2 text-xs font-semibold text-slate-200 mb-2">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                Duration
              </label>
              <div className="grid grid-cols-4 gap-1.5">
                {durationOptions.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setDuration(opt.value)}
                    className={`flex flex-col items-center py-2 px-1 rounded-lg border transition-all duration-200 ${
                      duration === opt.value
                        ? "border-primary bg-primary/10 text-white"
                        : "border-white/10 text-slate-400 hover:border-white/20 hover:text-slate-300"
                    }`}
                  >
                    <span className="text-xs font-semibold">{opt.label}</span>
                    <span className="text-[9px] mt-0.5 opacity-60">{opt.questions}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Difficulty — compact */}
            <div className="glass rounded-xl p-4">
              <label className="flex items-center gap-2 text-xs font-semibold text-slate-200 mb-2">
                <BarChart3 className="w-3.5 h-3.5 text-slate-400" />
                Difficulty
              </label>
              <div className="grid grid-cols-3 gap-2">
                {difficultyOptions.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setDifficulty(opt.value)}
                    className={`flex items-center gap-2 px-3 py-2.5 rounded-lg border transition-all duration-200 ${
                      difficulty === opt.value
                        ? "border-primary bg-primary/10"
                        : "border-white/10 hover:border-white/20"
                    }`}
                  >
                    <div className={`w-2.5 h-2.5 rounded-full bg-gradient-to-r ${opt.color} flex-shrink-0`} />
                    <div className="text-left">
                      <span className={`text-xs font-semibold block leading-tight ${difficulty === opt.value ? "text-white" : "text-slate-300"}`}>
                        {opt.label}
                      </span>
                      <span className="text-[9px] text-slate-500 leading-tight">{opt.desc}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg px-3 py-2 text-xs">
                {error}
              </div>
            )}

            {/* Start Button */}
            <Button
              onClick={handleStart}
              loading={busy}
              size="lg"
              className="w-full"
            >
              <Play className="w-5 h-5" />
              Start Interview
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
