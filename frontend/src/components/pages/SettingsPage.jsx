import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Settings,
  Sliders,
  ShieldCheck,
  User,
  Bell,
  Save,
  RotateCcw,
  Server,
  Zap,
  Check
} from 'lucide-react';
import { ConfirmDialog } from '../ui/SaaSPrimitives';

export function SettingsPage({ health, onSaveSettings, onResetDemoEnvironment }) {
  const [travelerName, setTravelerName] = useState('Aarav Sharma');
  const [travelerEmail, setTravelerEmail] = useState('aarav.sharma@example.com');
  const [emergencyName, setEmergencyName] = useState('Priya Sharma');
  const [emergencyEmail, setEmergencyEmail] = useState('priya.sharma.family@example.com');
  const [maxAutoBudgetInr, setMaxAutoBudgetInr] = useState(1500);
  const [minConfidence, setMinConfidence] = useState(0.80);
  const [preferRailOverBus, setPreferRailOverBus] = useState(true);
  const [strictAntiHallucination, setStrictAntiHallucination] = useState(true);
  const [wsAutoToast, setWsAutoToast] = useState(true);
  const [confirmResetOpen, setConfirmResetOpen] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    if (onSaveSettings) {
      onSaveSettings({
        travelerName,
        travelerEmail,
        emergencyName,
        emergencyEmail,
        maxAutoBudgetInr,
        minConfidence,
        preferRailOverBus,
        strictAntiHallucination,
        wsAutoToast,
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 2500);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="rounded-3xl border border-white/[0.08] bg-[#070b16]/80 p-6 shadow-glass-card backdrop-blur-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-80 h-80 bg-sky-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
        <div className="relative z-10">
          <h2 className="text-xl font-bold text-white flex items-center gap-2.5 font-display">
            <Settings className="w-5 h-5 text-sky-400" />
            <span>Platform &amp; Autonomous Agent Settings</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1 font-sans">
            Configure traveler preferences, OR-Tools optimization thresholds, autonomous execution guardrails, and notification channels.
          </p>
        </div>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          type="button"
          onClick={() => setConfirmResetOpen(true)}
          className="px-4 py-2.5 rounded-2xl bg-rose-950/40 hover:bg-rose-900/50 text-rose-300 border border-rose-500/30 text-xs font-semibold flex items-center gap-2 cursor-pointer transition shadow-sm font-sans relative z-10"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset Demo State</span>
        </motion.button>
      </motion.div>

      <ConfirmDialog
        open={confirmResetOpen}
        variant="danger"
        title="Reset All Simulated Supplier, Kafka & Audit State?"
        description="This will restore all Mock Supplier seat inventories, clear the Stage 8 Idempotency & Audit Log, reset the Stage 9 Kafka topic offsets & DLQ, and re-seed the Stage 10 Notification Inbox."
        confirmLabel="Reset Environment"
        onCancel={() => setConfirmResetOpen(false)}
        onConfirm={() => {
          setConfirmResetOpen(false);
          if (onResetDemoEnvironment) onResetDemoEnvironment();
        }}
      />

      <form onSubmit={handleSave} className="grid grid-cols-1 lg:grid-cols-2 gap-6 text-xs">
        {/* Traveler & Emergency Contact Profile */}
        <motion.div
          initial={{ opacity: 0, x: -15 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.05 }}
          className="rounded-3xl border border-white/[0.08] bg-[#070b16]/80 p-6 shadow-glass-card space-y-4 backdrop-blur-2xl"
        >
          <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-white/[0.08] pb-3 font-display">
            <User className="w-4 h-4 text-sky-400" />
            <span>Traveler &amp; Emergency Contact Profile</span>
          </div>

          <div className="space-y-3 font-sans">
            <div>
              <label className="block text-slate-400 mb-1 font-semibold text-[11px]">Primary Traveler Name</label>
              <input
                type="text"
                value={travelerName}
                onChange={(e) => setTravelerName(e.target.value)}
                className="w-full rounded-xl bg-[#04060d] border border-white/[0.1] px-3.5 py-2 text-slate-200 text-xs focus:outline-none focus:border-sky-500/50 transition"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-semibold text-[11px]">Primary Traveler Email</label>
              <input
                type="email"
                value={travelerEmail}
                onChange={(e) => setTravelerEmail(e.target.value)}
                className="w-full rounded-xl bg-[#04060d] border border-white/[0.1] px-3.5 py-2 text-slate-200 font-mono text-xs focus:outline-none focus:border-sky-500/50 transition"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-semibold text-[11px]">Designated Emergency Contact</label>
              <input
                type="text"
                value={emergencyName}
                onChange={(e) => setEmergencyName(e.target.value)}
                className="w-full rounded-xl bg-[#04060d] border border-white/[0.1] px-3.5 py-2 text-slate-200 text-xs focus:outline-none focus:border-sky-500/50 transition"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-semibold text-[11px]">Emergency Contact Email</label>
              <input
                type="email"
                value={emergencyEmail}
                onChange={(e) => setEmergencyEmail(e.target.value)}
                className="w-full rounded-xl bg-[#04060d] border border-white/[0.1] px-3.5 py-2 text-slate-200 font-mono text-xs focus:outline-none focus:border-sky-500/50 transition"
              />
            </div>
          </div>
        </motion.div>

        {/* Autonomous Execution & Guardrail Thresholds */}
        <motion.div
          initial={{ opacity: 0, x: 15 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="rounded-3xl border border-white/[0.08] bg-[#070b16]/80 p-6 shadow-glass-card space-y-4 backdrop-blur-2xl"
        >
          <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-white/[0.08] pb-3 font-display">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Autonomous Approval &amp; Guardrail Rules</span>
          </div>

          <div className="space-y-4 font-sans">
            <div>
              <div className="flex justify-between items-center mb-1 text-[11px]">
                <span className="text-slate-400 font-semibold">Max Auto-Approved Net Cost Delta</span>
                <strong className="text-sky-300 font-mono">INR {maxAutoBudgetInr}</strong>
              </div>
              <input
                type="range"
                min={200}
                max={5000}
                step={100}
                value={maxAutoBudgetInr}
                onChange={(e) => setMaxAutoBudgetInr(Number(e.target.value))}
                className="w-full accent-sky-500 cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-1 text-[11px]">
                <span className="text-slate-400 font-semibold">Minimum Confidence Threshold</span>
                <strong className="text-emerald-300 font-mono">{Math.round(minConfidence * 100)}%</strong>
              </div>
              <input
                type="range"
                min={0.5}
                max={0.99}
                step={0.01}
                value={minConfidence}
                onChange={(e) => setMinConfidence(Number(e.target.value))}
                className="w-full accent-emerald-500 cursor-pointer"
              />
            </div>

            <label className="flex items-center justify-between p-3.5 rounded-2xl bg-[#04060d] border border-white/[0.08] hover:border-white/[0.15] transition cursor-pointer">
              <span className="text-slate-300 font-medium">Prefer Rail &amp; Flight over Bus when feasible</span>
              <input
                type="checkbox"
                checked={preferRailOverBus}
                onChange={(e) => setPreferRailOverBus(e.target.checked)}
                className="w-4 h-4 accent-sky-500 cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between p-3.5 rounded-2xl bg-[#04060d] border border-white/[0.08] hover:border-white/[0.15] transition cursor-pointer">
              <span className="text-slate-300 font-medium">Enforce Strict Anti-Hallucination Fact-Grounding</span>
              <input
                type="checkbox"
                checked={strictAntiHallucination}
                onChange={(e) => setStrictAntiHallucination(e.target.checked)}
                className="w-4 h-4 accent-emerald-500 cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between p-3.5 rounded-2xl bg-[#04060d] border border-white/[0.08] hover:border-white/[0.15] transition cursor-pointer">
              <span className="text-slate-300 font-medium">Show Real-Time Toast Alerts on WebSocket Kafka Events</span>
              <input
                type="checkbox"
                checked={wsAutoToast}
                onChange={(e) => setWsAutoToast(e.target.checked)}
                className="w-4 h-4 accent-indigo-500 cursor-pointer"
              />
            </label>
          </div>
        </motion.div>

        {/* Save Bar */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.15 }}
          className="lg:col-span-2 flex flex-col sm:flex-row items-center justify-between p-5 rounded-3xl border border-white/[0.08] bg-[#070b16]/80 backdrop-blur-2xl gap-4 shadow-glass-card"
        >
          <div className="text-slate-400 flex items-center gap-2.5 font-mono text-xs">
            <Server className="w-4 h-4 text-emerald-400" />
            <span>
              Backend: <strong className="text-emerald-400">{health?.status || 'ok'}</strong> &middot; Database:{' '}
              <strong className="text-sky-300">{health?.database || 'sqlite'}</strong>
            </span>
          </div>
          <div className="flex items-center gap-3">
            {savedSuccess && (
              <span className="text-xs text-emerald-400 font-mono flex items-center gap-1.5 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/30">
                <Check className="w-3.5 h-3.5" /> Preferences Saved!
              </span>
            )}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              className="px-6 py-2.5 rounded-2xl bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white font-bold flex items-center gap-2 shadow-[0_0_15px_rgba(56,189,248,0.25)] cursor-pointer font-display transition"
            >
              <Save className="w-4 h-4" />
              <span>Save Preferences</span>
            </motion.button>
          </div>
        </motion.div>
      </form>
    </div>
  );
}
