"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  Target,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  BarChart3,
  ArrowRight,
  Home,
  RotateCcw,
} from "lucide-react";
import Logo from "@/components/ui/Logo";
import Button from "@/components/ui/Button";
import type { InterviewReport } from "@/types";

export default function ReportPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [report, setReport] = useState<InterviewReport | null>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/auth");
      return;
    }
    const raw = sessionStorage.getItem("interviewReport");
    if (raw) {
      setReport(JSON.parse(raw));
    } else {
      router.replace("/setup");
    }
  }, [authLoading, user, router]);

  if (!report) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const scoreColor =
    report.overall_score >= 80
      ? "text-emerald-400"
      : report.overall_score >= 60
      ? "text-amber-400"
      : "text-red-400";

  const ringDash = 327;
  const ringOffset = ringDash - (ringDash * report.overall_score) / 100;

  const recommendationColor =
    report.hiring_recommendation?.toLowerCase().includes("strong")
      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
      : report.hiring_recommendation?.toLowerCase().includes("no")
      ? "bg-red-500/10 border-red-500/30 text-red-400"
      : "bg-amber-500/10 border-amber-500/30 text-amber-400";

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_20%_50%,rgba(99,102,241,0.1),transparent_60%),radial-gradient(ellipse_at_80%_80%,rgba(168,85,247,0.08),transparent_50%)]">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <Logo size="sm" />
          <span className="text-lg font-bold gradient-text">Interview Report</span>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => router.push("/setup")}>
            <RotateCcw className="w-3.5 h-3.5" />
            New Interview
          </Button>
          <Button variant="secondary" size="sm" onClick={() => router.push("/history")}>
            <Home className="w-3.5 h-3.5" />
            Dashboard
          </Button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-10 animate-fade-in">
        {/* Hero Score Section */}
        <div className="text-center mb-12">
          <h1 className="text-3xl font-extrabold text-white mb-2">Interview Complete!</h1>
          <p className="text-slate-400 text-sm">Here&apos;s how you performed</p>

          <div className="flex items-center justify-center gap-16 mt-10">
            {/* Score Ring */}
            <div className="relative">
              <svg viewBox="0 0 120 120" className="w-40 h-40">
                <circle cx="60" cy="60" r="52" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
                <circle
                  cx="60"
                  cy="60"
                  r="52"
                  fill="none"
                  stroke="url(#scoreGrad)"
                  strokeWidth="8"
                  strokeLinecap="round"
                  strokeDasharray={ringDash}
                  strokeDashoffset={ringOffset}
                  transform="rotate(-90 60 60)"
                  className="transition-all duration-1000"
                />
                <defs>
                  <linearGradient id="scoreGrad" x1="0" y1="0" x2="1" y2="1">
                    <stop stopColor="#6366f1" />
                    <stop offset="1" stopColor="#a855f7" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`text-4xl font-extrabold ${scoreColor}`}>{report.overall_score}</span>
                <span className="text-xs text-slate-500">out of 100</span>
              </div>
            </div>

            {/* Stats */}
            <div className="space-y-4 text-left">
              <div className="glass rounded-xl px-5 py-3 flex items-center gap-3">
                <Target className="w-5 h-5 text-primary-light" />
                <div>
                  <div className="text-xs text-slate-500">Cracking Probability</div>
                  <div className={`text-lg font-bold ${scoreColor}`}>{report.cracking_probability}%</div>
                </div>
              </div>
              <div className={`rounded-xl px-5 py-3 border ${recommendationColor}`}>
                <div className="text-xs opacity-70 mb-1">Hiring Recommendation</div>
                <div className="text-sm font-bold">{report.hiring_recommendation || "N/A"}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Summary */}
        {report.summary && (
          <div className="glass rounded-2xl p-6 mb-6">
            <p className="text-sm text-slate-300 leading-relaxed">{report.summary}</p>
          </div>
        )}

        {/* Topic Scores */}
        {Object.keys(report.topic_scores || {}).length > 0 && (
          <div className="glass rounded-2xl p-6 mb-6">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-white mb-5">
              <BarChart3 className="w-4 h-4 text-primary-light" />
              Topic Breakdown
            </h3>
            <div className="space-y-3">
              {Object.entries(report.topic_scores).map(([topic, score]) => (
                <div key={topic}>
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="text-slate-300 capitalize">{topic}</span>
                    <span className="text-slate-400 font-medium">{score}/100</span>
                  </div>
                  <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full bg-gradient-to-r ${
                        score >= 80
                          ? "from-emerald-500 to-emerald-400"
                          : score >= 60
                          ? "from-amber-500 to-orange-400"
                          : "from-red-500 to-rose-400"
                      } transition-all duration-700`}
                      style={{ width: `${score}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Three Column Grid */}
        <div className="grid md:grid-cols-3 gap-5">
          {/* Strengths */}
          <div className="glass rounded-2xl p-5">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-emerald-400 mb-4">
              <CheckCircle2 className="w-4 h-4" />
              Strengths
            </h3>
            <ul className="space-y-2.5">
              {(report.technical_strengths || []).map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                  <div className="w-1 h-1 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0" />
                  {s}
                </li>
              ))}
              {(!report.technical_strengths || report.technical_strengths.length === 0) && (
                <li className="text-xs text-slate-500">No data</li>
              )}
            </ul>
          </div>

          {/* Improvements */}
          <div className="glass rounded-2xl p-5">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-amber-400 mb-4">
              <AlertTriangle className="w-4 h-4" />
              Areas for Improvement
            </h3>
            <ul className="space-y-2.5">
              {(report.areas_for_improvement || []).map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                  <div className="w-1 h-1 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
                  {s}
                </li>
              ))}
              {(!report.areas_for_improvement || report.areas_for_improvement.length === 0) && (
                <li className="text-xs text-slate-500">No data</li>
              )}
            </ul>
          </div>

          {/* Recommendations */}
          <div className="glass rounded-2xl p-5">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-purple-400 mb-4">
              <Lightbulb className="w-4 h-4" />
              Recommendations
            </h3>
            <ul className="space-y-2.5">
              {(report.specific_recommendations || []).map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                  <div className="w-1 h-1 rounded-full bg-purple-400 mt-1.5 flex-shrink-0" />
                  {s}
                </li>
              ))}
              {(!report.specific_recommendations || report.specific_recommendations.length === 0) && (
                <li className="text-xs text-slate-500">No data</li>
              )}
            </ul>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-center gap-4 mt-12">
          <Button size="lg" onClick={() => router.push("/setup")}>
            <RotateCcw className="w-4 h-4" />
            Start New Interview
          </Button>
          <Button variant="secondary" size="lg" onClick={() => router.push("/history")}>
            View History
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      </main>
    </div>
  );
}
