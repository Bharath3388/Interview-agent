"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  ArrowLeft,
  Calendar,
  Clock,
  BarChart3,
  Target,
  ChevronRight,
  Trophy,
} from "lucide-react";
import Logo from "@/components/ui/Logo";
import Button from "@/components/ui/Button";
import { apiGetHistory, apiGetSessionDetail } from "@/lib/api";
import type { HistorySession, HistoryQA } from "@/types";

export default function HistoryPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [sessions, setSessions] = useState<HistorySession[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [sessionQAs, setSessionQAs] = useState<HistoryQA[]>([]);
  const [qaLoading, setQaLoading] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/auth");
      return;
    }
    if (user) {
      apiGetHistory()
        .then(setSessions)
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [authLoading, user, router]);

  const viewSession = async (sessionId: string) => {
    setSelectedSession(sessionId);
    setQaLoading(true);
    try {
      const data = await apiGetSessionDetail(sessionId);
      setSessionQAs(data.qas);
    } catch {
      setSessionQAs([]);
    } finally {
      setQaLoading(false);
    }
  };

  const scoreColor = (score: number) =>
    score >= 80 ? "text-emerald-400" : score >= 60 ? "text-amber-400" : "text-red-400";

  const scoreBg = (score: number) =>
    score >= 80
      ? "bg-emerald-500/10 border-emerald-500/20"
      : score >= 60
      ? "bg-amber-500/10 border-amber-500/20"
      : "bg-red-500/10 border-red-500/20";

  if (authLoading || !user) return null;

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_20%_50%,rgba(99,102,241,0.1),transparent_60%)]">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <Logo size="sm" />
          <span className="text-lg font-bold gradient-text">Interview History</span>
        </div>
        <Button variant="secondary" size="sm" onClick={() => router.push("/setup")}>
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Setup
        </Button>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-10 animate-fade-in">
        {loading ? (
          <div className="flex justify-center py-20">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-20">
            <Trophy className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-slate-300 mb-2">No interviews yet</h2>
            <p className="text-sm text-slate-500 mb-6">Start your first mock interview to see results here</p>
            <Button onClick={() => router.push("/setup")}>Start Interview</Button>
          </div>
        ) : selectedSession ? (
          /* Session Detail View */
          <div>
            <button
              onClick={() => { setSelectedSession(null); setSessionQAs([]); }}
              className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors mb-6"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to all sessions
            </button>

            <h2 className="text-xl font-bold text-white mb-6">Session Detail</h2>

            {qaLoading ? (
              <div className="flex justify-center py-10">
                <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              </div>
            ) : sessionQAs.length === 0 ? (
              <p className="text-sm text-slate-500">No Q&A data available for this session.</p>
            ) : (
              <div className="space-y-4">
                {sessionQAs.map((qa, i) => (
                  <div key={i} className="glass rounded-2xl p-5 space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium bg-primary/10 text-primary-light px-2 py-0.5 rounded-full capitalize">
                        {qa.topic || "General"}
                      </span>
                      <span className="text-xs text-slate-500">Q{i + 1}</span>
                    </div>
                    <div>
                      <p className="text-sm text-slate-200 font-medium">{qa.question}</p>
                    </div>
                    <div className="bg-white/[0.03] rounded-xl p-3">
                      <p className="text-xs text-slate-400 mb-1 font-medium">Your Answer:</p>
                      <p className="text-sm text-slate-300">{qa.answer || "No answer provided"}</p>
                    </div>
                    {qa.evaluation?.brief_feedback && (
                      <div className="bg-primary/5 border border-primary/10 rounded-xl p-3">
                        <p className="text-xs text-primary-light font-medium mb-1">Feedback:</p>
                        <p className="text-xs text-slate-400">{qa.evaluation.brief_feedback}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          /* Sessions List */
          <div className="space-y-3">
            {sessions.map((s) => (
              <button
                key={s.session_id}
                onClick={() => viewSession(s.session_id)}
                className="w-full glass rounded-2xl p-5 flex items-center gap-5 hover:bg-white/[0.06] transition-all group text-left"
              >
                {/* Score badge */}
                <div className={`w-14 h-14 rounded-xl border flex flex-col items-center justify-center flex-shrink-0 ${scoreBg(s.overall_score)}`}>
                  <span className={`text-lg font-bold ${scoreColor(s.overall_score)}`}>{s.overall_score}</span>
                  <span className="text-[9px] text-slate-500">score</span>
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-200 truncate">
                    {s.jd_text || "General Interview"}
                  </p>
                  <div className="flex items-center gap-4 mt-1.5">
                    <span className="flex items-center gap-1 text-xs text-slate-500">
                      <Calendar className="w-3 h-3" />
                      {new Date(s.created_at).toLocaleDateString()}
                    </span>
                    <span className="flex items-center gap-1 text-xs text-slate-500">
                      <Clock className="w-3 h-3" />
                      {s.duration} min
                    </span>
                    <span className="flex items-center gap-1 text-xs text-slate-500 capitalize">
                      <BarChart3 className="w-3 h-3" />
                      {s.difficulty}
                    </span>
                    <span className="flex items-center gap-1 text-xs text-slate-500">
                      <Target className="w-3 h-3" />
                      {s.cracking_probability}% chance
                    </span>
                  </div>
                </div>

                {/* Arrow */}
                <ChevronRight className="w-5 h-5 text-slate-600 group-hover:text-slate-400 transition-colors flex-shrink-0" />
              </button>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
