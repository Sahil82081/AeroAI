import React, { useState } from 'react';
import {
  Sparkles,
  Lock,
  Mail,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Radio,
  Workflow
} from 'lucide-react';

export function LoginPage({ onLogin, currentUser, onContinueAsCurrent }) {
  const [email, setEmail] = useState('traveler@example.com');
  const [password, setPassword] = useState('password123');
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setErr(null);
    try {
      await onLogin(email, password);
    } catch (error) {
      setErr(error?.message || 'Authentication failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-[82vh] flex items-center justify-center p-4">
      <div className="max-w-4xl w-full grid grid-cols-1 lg:grid-cols-12 rounded-3xl border border-slate-800 bg-slate-900/80 shadow-2xl overflow-hidden">
        {/* Left Brand & Architecture Column */}
        <div className="lg:col-span-6 p-8 bg-gradient-to-br from-indigo-950/80 via-slate-900 to-slate-950 border-b lg:border-b-0 lg:border-r border-slate-800 flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/15 border border-sky-500/30 text-sky-300 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Autonomous Travel Operations Platform</span>
            </div>
            <h2 className="text-2xl font-bold text-white leading-tight">
              Autonomous Disruption Recovery Agent
            </h2>
            <p className="text-xs text-slate-300 leading-relaxed">
              Enterprise AI control plane combining NetworkX Journey Graphs, Google OR-Tools CP-SAT Mathematical Optimization, 8-Node LangGraph Workflows, and Apache Kafka Event Streaming.
            </p>
          </div>

          <div className="space-y-3 text-xs">
            {[
              { icon: Workflow, title: '8-Node LangGraph Recovery Agent', desc: 'Confidence scoring, validation & approval guardrails' },
              { icon: Cpu, title: 'Google OR-Tools CP-SAT Optimizer', desc: 'Mathematical 0-1 integer programming across multi-modal routes' },
              { icon: Radio, title: 'Apache Kafka + Real-Time WebSocket', desc: '10 domain topics, idempotent consumers & Dead-Letter Queue' },
              { icon: ShieldCheck, title: 'Fact-Grounded Communication Layer', desc: 'Zero-hallucination email dispatch across 6 stakeholder channels' },
            ].map((item, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-slate-900/70 border border-slate-800/80">
                <item.icon className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
                <div>
                  <div className="font-bold text-slate-100">{item.title}</div>
                  <div className="text-[11px] text-slate-400">{item.desc}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="text-[11px] text-slate-500 font-mono">
            JWT Bearer Session &middot; Simulated Mock Supplier Ecosystem
          </div>
        </div>

        {/* Right Sign-In Column */}
        <div className="lg:col-span-6 p-8 flex flex-col justify-center space-y-6">
          <div>
            <h3 className="text-lg font-bold text-white">Sign in to Recovery Console</h3>
            <p className="text-xs text-slate-400 mt-1">
              Use the pre-configured traveler credentials or one-click instant demo access.
            </p>
          </div>

          {err && (
            <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-xs text-rose-200">
              {err}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            <div>
              <label className="block text-slate-300 font-semibold mb-1.5">Traveler Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-2.5" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 focus:border-sky-500 focus:outline-none"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-300 font-semibold mb-1.5">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-2.5" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 focus:border-sky-500 focus:outline-none"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 px-4 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg transition cursor-pointer"
            >
              <span>{submitting ? 'Authenticating...' : 'Sign In & Open Dashboard'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="pt-4 border-t border-slate-800 space-y-2.5">
            <div className="text-[11px] text-slate-400 font-semibold uppercase tracking-wider">
              Quick Demo Profiles
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => {
                  setEmail('traveler@example.com');
                  setPassword('password123');
                  onLogin('traveler@example.com', 'password123');
                }}
                className="p-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-left text-xs transition cursor-pointer"
              >
                <div className="font-bold text-sky-300">Aarav Sharma</div>
                <div className="text-[10px] text-slate-400 font-mono">traveler@example.com</div>
              </button>
              {currentUser && (
                <button
                  type="button"
                  onClick={onContinueAsCurrent}
                  className="p-2.5 rounded-xl bg-emerald-950/30 hover:bg-emerald-950/50 border border-emerald-500/30 text-left text-xs transition cursor-pointer"
                >
                  <div className="font-bold text-emerald-300">Active Session ✓</div>
                  <div className="text-[10px] text-slate-300">Return to Dashboard</div>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
