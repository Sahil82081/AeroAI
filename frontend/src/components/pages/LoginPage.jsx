import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  Lock,
  Mail,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Radio,
  Workflow,
  Plane,
  Radar,
  Activity,
  CheckCircle2
} from 'lucide-react';

export function LoginPage({ onLogin, currentUser, onContinueAsCurrent }) {
  const [email, setEmail] = useState('traveler@example.com');
  const [password, setPassword] = useState('password123');
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState(null);
  const [focusedField, setFocusedField] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setErr(null);
    try {
      await onLogin(email, password);
    } catch (error) {
      setErr(error?.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center p-4 sm:p-6 lg:p-8 relative">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 -left-20 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-20 w-96 h-96 bg-violet-500/10 rounded-full blur-3xl pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 16 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="max-w-5xl w-full grid grid-cols-1 lg:grid-cols-12 rounded-3xl border border-white/[0.12] bg-[#070b16]/85 shadow-2xl backdrop-blur-2xl overflow-hidden relative"
      >
        {/* Top subtle border glow line */}
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-sky-400/40 to-transparent z-10" />

        {/* Left Column: Cinematic Mission Control & Flight Path Radar */}
        <div className="lg:col-span-7 p-8 sm:p-10 bg-gradient-to-br from-[#0c1427]/90 via-[#070b16] to-[#04060d] border-b lg:border-b-0 lg:border-r border-white/[0.08] flex flex-col justify-between space-y-8 relative overflow-hidden">
          
          {/* Subtle radar background grid */}
          <div className="absolute inset-0 aviation-grid-overlay opacity-40 pointer-events-none" />

          {/* Interactive animated SVG Flight Paths */}
          <div className="absolute -right-10 top-1/2 -translate-y-1/2 w-80 h-80 pointer-events-none opacity-30 sm:opacity-50">
            <svg viewBox="0 0 400 400" className="w-full h-full">
              <defs>
                <linearGradient id="flightGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#a855f7" stopOpacity="0.2" />
                </linearGradient>
              </defs>
              
              {/* Concentric radar rings */}
              <circle cx="200" cy="200" r="60" fill="none" stroke="rgba(56,189,248,0.15)" strokeWidth="1" strokeDasharray="4 4" />
              <circle cx="200" cy="200" r="120" fill="none" stroke="rgba(56,189,248,0.1)" strokeWidth="1" />
              <circle cx="200" cy="200" r="180" fill="none" stroke="rgba(56,189,248,0.06)" strokeWidth="1" />

              {/* Flight path geodesic arcs */}
              <path
                d="M 60 300 Q 200 80 340 180"
                fill="none"
                stroke="url(#flightGrad)"
                strokeWidth="2"
                strokeDasharray="6 4"
                className="animate-pulse"
              />
              <path
                d="M 80 120 Q 220 320 330 290"
                fill="none"
                stroke="rgba(168,85,247,0.4)"
                strokeWidth="1.5"
                strokeDasharray="3 3"
              />

              {/* Waypoints / Airport Nodes */}
              <circle cx="60" cy="300" r="4" fill="#38bdf8" />
              <circle cx="340" cy="180" r="4" fill="#a855f7" />
              <circle cx="80" cy="120" r="3" fill="#38bdf8" />
              <circle cx="330" cy="290" r="3" fill="#38bdf8" />
            </svg>
          </div>

          {/* Top Brand Header */}
          <div className="space-y-4 relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/15 border border-sky-400/30 text-sky-300 text-xs font-mono font-medium tracking-wide">
              <span className="w-2 h-2 rounded-full bg-sky-400 shadow-[0_0_8px_rgba(56,189,248,0.8)] animate-pulse" />
              <span>Aviation Operations Control Plane</span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight font-display">
              Autonomous Travel{' '}
              <span className="text-gradient-aurora">Disruption Recovery</span>
            </h1>

            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-lg font-sans">
              Real-time multi-modal flight intelligence orchestrating NetworkX Journey DAGs, Google OR-Tools CP-SAT Mathematical Optimization, and Apache Kafka Event Streams.
            </p>
          </div>

          {/* Technology Architecture Highlights */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 relative z-10">
            {[
              {
                icon: Workflow,
                title: '8-Node LangGraph Agent',
                desc: 'Guardrailed recovery scoring & confidence thresholds',
                color: 'sky',
              },
              {
                icon: Cpu,
                title: 'Google OR-Tools CP-SAT',
                desc: '0-1 integer programming for multi-modal alternatives',
                color: 'violet',
              },
              {
                icon: Radio,
                title: 'Apache Kafka Event Mesh',
                desc: '10 domain topics with real-time WebSocket telemetry',
                color: 'cyan',
              },
              {
                icon: ShieldCheck,
                title: 'DGCA / EU 261 Policy RAG',
                desc: 'Fact-grounded passenger rights legal compensation',
                color: 'emerald',
              },
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * i + 0.2 }}
                className="p-3.5 rounded-2xl bg-[#0b1120]/75 border border-white/[0.08] backdrop-blur-md hover:border-white/20 transition-all group"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400 shrink-0 group-hover:scale-105 transition-transform">
                    <item.icon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="font-bold text-xs text-white font-display">{item.title}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5 leading-snug">{item.desc}</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Bottom Telemetry Footer */}
          <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono pt-4 border-t border-white/[0.08] relative z-10">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
              <span>JWT Bearer Security Active</span>
            </div>
            <span>v2.4.0-MISSION-CONTROL</span>
          </div>
        </div>

        {/* Right Column: Floating Glass Login Card */}
        <div className="lg:col-span-5 p-8 sm:p-10 flex flex-col justify-center space-y-6 bg-[#070b16]/60 backdrop-blur-xl relative">
          <div>
            <h2 className="text-xl font-bold text-white font-display tracking-tight">
              Sign In to Recovery Console
            </h2>
            <p className="text-xs text-slate-400 mt-1.5 font-sans leading-relaxed">
              Access real-time journey state or select a pre-configured traveler profile below.
            </p>
          </div>

          {/* Error Message */}
          <AnimatePresence>
            {err && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                className="p-3.5 rounded-2xl bg-rose-950/40 border border-rose-500/40 text-xs text-rose-200 backdrop-blur-md"
              >
                {err}
              </motion.div>
            )}
          </AnimatePresence>

          <form onSubmit={handleSubmit} className="space-y-4 text-xs font-sans">
            <div>
              <label className="block text-slate-300 font-semibold mb-1.5">Traveler Email</label>
              <div className={`relative rounded-xl border transition-all duration-200 ${
                focusedField === 'email'
                  ? 'border-sky-400 shadow-[0_0_15px_rgba(56,189,248,0.25)] bg-[#04060d]'
                  : 'border-white/[0.1] bg-[#04060d]/70'
              }`}>
                <Mail className={`w-4 h-4 absolute left-3.5 top-3 transition-colors ${
                  focusedField === 'email' ? 'text-sky-400' : 'text-slate-500'
                }`} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onFocus={() => setFocusedField('email')}
                  onBlur={() => setFocusedField(null)}
                  className="w-full pl-10 pr-4 py-2.5 bg-transparent text-slate-100 placeholder-slate-500 focus:outline-none text-xs font-mono"
                  placeholder="traveler@example.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-300 font-semibold mb-1.5">Password</label>
              <div className={`relative rounded-xl border transition-all duration-200 ${
                focusedField === 'password'
                  ? 'border-sky-400 shadow-[0_0_15px_rgba(56,189,248,0.25)] bg-[#04060d]'
                  : 'border-white/[0.1] bg-[#04060d]/70'
              }`}>
                <Lock className={`w-4 h-4 absolute left-3.5 top-3 transition-colors ${
                  focusedField === 'password' ? 'text-sky-400' : 'text-slate-500'
                }`} />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onFocus={() => setFocusedField('password')}
                  onBlur={() => setFocusedField(null)}
                  className="w-full pl-10 pr-4 py-2.5 bg-transparent text-slate-100 placeholder-slate-500 focus:outline-none text-xs font-mono"
                  placeholder="••••••••••••"
                  required
                />
              </div>
            </div>

            <motion.button
              type="submit"
              disabled={submitting}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-sky-600 via-sky-500 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-[0_8px_25px_rgba(14,165,233,0.35)] transition-all cursor-pointer font-display tracking-wide"
            >
              <span>{submitting ? 'Authenticating Telemetry...' : 'Sign In & Launch Dashboard'}</span>
              <ArrowRight className="w-4 h-4" />
            </motion.button>
          </form>

          {/* Quick Demo Credentials */}
          <div className="pt-4 border-t border-white/[0.08] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-400 font-mono uppercase tracking-wider font-semibold">
                Quick Demo Profile
              </span>
              <span className="text-[10px] text-sky-400 font-mono">1-Click Fast Auth</span>
            </div>

            <div className="grid grid-cols-1 gap-2">
              <button
                type="button"
                onClick={() => {
                  setEmail('traveler@example.com');
                  setPassword('password123');
                  onLogin('traveler@example.com', 'password123');
                }}
                className="p-3 rounded-2xl bg-[#04060d]/90 hover:bg-slate-900 border border-white/[0.08] hover:border-sky-500/40 text-left transition-all cursor-pointer group flex items-center justify-between"
              >
                <div>
                  <div className="font-bold text-xs text-sky-300 font-display group-hover:text-sky-200">
                    Aarav Sharma (Executive Traveler)
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                    traveler@example.com
                  </div>
                </div>
                <div className="p-1.5 rounded-lg bg-sky-500/10 text-sky-400 group-hover:bg-sky-500/20 transition-colors">
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </button>

              {currentUser && (
                <button
                  type="button"
                  onClick={onContinueAsCurrent}
                  className="p-3 rounded-2xl bg-emerald-950/25 hover:bg-emerald-950/40 border border-emerald-500/30 text-left transition-all cursor-pointer flex items-center justify-between"
                >
                  <div>
                    <div className="font-bold text-xs text-emerald-300 font-display flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Active Session Valid</span>
                    </div>
                    <div className="text-[11px] text-slate-300 font-mono mt-0.5">
                      Return to Active Mission Control
                    </div>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-emerald-400" />
                </button>
              )}
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
