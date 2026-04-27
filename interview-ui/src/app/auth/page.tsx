"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { Mail, Lock, User, ArrowRight } from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Logo from "@/components/ui/Logo";

export default function AuthPage() {
  const { login, register, loading: authLoading } = useAuth();
  const router = useRouter();
  const [tab, setTab] = useState<"login" | "register">("login");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  // Form state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (tab === "login") {
        if (!email || !password) { setError("Please enter email and password."); return; }
        await login(email, password);
      } else {
        if (!username || !email || !password) { setError("Please fill all fields."); return; }
        await register(username, email, password);
      }
      router.push("/setup");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-[radial-gradient(ellipse_at_20%_50%,rgba(99,102,241,0.15),transparent_60%),radial-gradient(ellipse_at_80%_20%,rgba(168,85,247,0.1),transparent_50%)]">
      <div className="w-full max-w-md animate-fade-in">
        {/* Logo Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Logo size="lg" />
          </div>
          <h1 className="text-3xl font-extrabold gradient-text">AI Interview Agent</h1>
          <p className="text-slate-400 text-sm mt-2">
            Sign in to track your progress and interview history
          </p>
        </div>

        {/* Card */}
        <div className="glass rounded-2xl overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-white/10">
            <button
              onClick={() => { setTab("login"); setError(""); }}
              className={`flex-1 py-3.5 text-sm font-semibold transition-colors ${
                tab === "login"
                  ? "text-primary-light bg-primary/10 border-b-2 border-primary"
                  : "text-slate-400 hover:text-slate-300"
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => { setTab("register"); setError(""); }}
              className={`flex-1 py-3.5 text-sm font-semibold transition-colors ${
                tab === "register"
                  ? "text-primary-light bg-primary/10 border-b-2 border-primary"
                  : "text-slate-400 hover:text-slate-300"
              }`}
            >
              Create Account
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {tab === "register" && (
              <Input
                label="Username"
                icon={<User className="w-4 h-4" />}
                placeholder="johndoe"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            )}
            <Input
              label="Email"
              icon={<Mail className="w-4 h-4" />}
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <Input
              label={tab === "register" ? "Password (min 8 characters)" : "Password"}
              icon={<Lock className="w-4 h-4" />}
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl px-4 py-2.5 text-xs">
                {error}
              </div>
            )}

            <Button type="submit" loading={busy} className="w-full" size="lg">
              {tab === "login" ? "Sign In" : "Create Account"}
              <ArrowRight className="w-4 h-4" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
