import React, { useState } from 'react';
import {
  Settings,
  Sliders,
  ShieldCheck,
  User,
  Bell,
  Save,
  RotateCcw,
  Server
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
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Settings className="w-5 h-5 text-sky-400" />
            Platform &amp; Autonomous Agent Settings
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Configure traveler preferences, OR-Tools optimization thresholds, autonomous execution guardrails, and notification channels.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setConfirmResetOpen(true)}
          className="px-3.5 py-2 rounded-xl bg-rose-950/50 hover:bg-rose-900/60 text-rose-300 border border-rose-500/30 text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset Demo State</span>
        </button>
      </div>

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
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-slate-800 pb-2.5">
            <User className="w-4 h-4 text-sky-400" />
            <span>Traveler &amp; Emergency Contact Profile</span>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-slate-400 mb-1">Primary Traveler Name</label>
              <input
                type="text"
                value={travelerName}
                onChange={(e) => setTravelerName(e.target.value)}
                className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3 py-2 text-slate-200"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Primary Traveler Email</label>
              <input
                type="email"
                value={travelerEmail}
                onChange={(e) => setTravelerEmail(e.target.value)}
                className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3 py-2 text-slate-200 font-mono"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Designated Emergency Contact</label>
              <input
                type="text"
                value={emergencyName}
                onChange={(e) => setEmergencyName(e.target.value)}
                className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3 py-2 text-slate-200"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Emergency Contact Email</label>
              <input
                type="email"
                value={emergencyEmail}
                onChange={(e) => setEmergencyEmail(e.target.value)}
                className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3 py-2 text-slate-200 font-mono"
              />
            </div>
          </div>
        </div>

        {/* Autonomous Execution & Guardrail Thresholds */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-slate-800 pb-2.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Autonomous Approval &amp; Guardrail Rules</span>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-slate-400 mb-1">
                Max Auto-Approved Net Cost Delta (INR): <strong className="text-sky-300">INR {maxAutoBudgetInr}</strong>
              </label>
              <input
                type="range"
                min={200}
                max={5000}
                step={100}
                value={maxAutoBudgetInr}
                onChange={(e) => setMaxAutoBudgetInr(Number(e.target.value))}
                className="w-full accent-sky-500"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">
                Minimum Agent Confidence for Autonomous Execution: <strong className="text-emerald-300">{Math.round(minConfidence * 100)}%</strong>
              </label>
              <input
                type="range"
                min={0.5}
                max={0.99}
                step={0.01}
                value={minConfidence}
                onChange={(e) => setMinConfidence(Number(e.target.value))}
                className="w-full accent-emerald-500"
              />
            </div>

            <label className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800 cursor-pointer">
              <span>Prefer Rail &amp; Flight over Bus when feasible</span>
              <input
                type="checkbox"
                checked={preferRailOverBus}
                onChange={(e) => setPreferRailOverBus(e.target.checked)}
                className="accent-sky-500"
              />
            </label>

            <label className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800 cursor-pointer">
              <span>Enforce Strict Anti-Hallucination Fact-Grounding on Emails</span>
              <input
                type="checkbox"
                checked={strictAntiHallucination}
                onChange={(e) => setStrictAntiHallucination(e.target.checked)}
                className="accent-emerald-500"
              />
            </label>

            <label className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800 cursor-pointer">
              <span>Show Real-Time Toast Alerts on WebSocket Kafka Events</span>
              <input
                type="checkbox"
                checked={wsAutoToast}
                onChange={(e) => setWsAutoToast(e.target.checked)}
                className="accent-indigo-500"
              />
            </label>
          </div>
        </div>

        {/* Save Bar */}
        <div className="lg:col-span-2 flex items-center justify-between p-4 rounded-2xl border border-slate-800 bg-slate-900/70">
          <div className="text-slate-400 flex items-center gap-2">
            <Server className="w-4 h-4 text-emerald-400" />
            <span>
              Backend Status: <strong className="text-emerald-400">{health?.status || 'ok'}</strong> &middot; Database: <strong className="text-sky-300">{health?.database || 'sqlite'}</strong>
            </span>
          </div>
          <button
            type="submit"
            className="px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold flex items-center gap-2 shadow cursor-pointer"
          >
            <Save className="w-4 h-4" />
            <span>Save Preferences</span>
          </button>
        </div>
      </form>
    </div>
  );
}
