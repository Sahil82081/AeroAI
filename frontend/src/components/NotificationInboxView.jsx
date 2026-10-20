import React, { useState, useEffect } from 'react';
import {
  MailCheck,
  ShieldAlert,
  Send,
  CheckCircle2,
  Trash2,
} from 'lucide-react';
import { api } from '../services/api';

const CATEGORY_ORDER = [
  { key: 'ALL', label: 'All Emails' },
  { key: 'traveler_notification', label: 'Traveler' },
  { key: 'hotel_notification', label: 'Hotel' },
  { key: 'supplier_communication', label: 'Supplier' },
  { key: 'refund_request', label: 'Refund' },
  { key: 'cancellation_request', label: 'Cancellation' },
  { key: 'emergency_contact_notification', label: 'Emergency Contact' },
];

export function NotificationInboxView() {
  const [inboxData, setInboxData] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [statusBanner, setStatusBanner] = useState(null);

  const loadInbox = async (cat = selectedCategory) => {
    setLoading(true);
    try {
      const data = await api.getNotificationInbox(cat);
      setInboxData(data);
      if (data?.messages?.length > 0) {
        setSelectedMessage(data.messages[0]);
      } else {
        setSelectedMessage(null);
      }
    } catch (err) {
      setStatusBanner({
        type: 'error',
        text: err?.response?.data?.detail || err?.message || 'Failed to load inbox',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInbox(selectedCategory);
  }, [selectedCategory]);

  const handleGenerateAllSix = async (hallucinationTest = false) => {
    setLoading(true);
    setStatusBanner(null);
    try {
      await api.generateNotificationSuite({
        simulate_hallucination_test: hallucinationTest,
      });
      await loadInbox(selectedCategory);
      setStatusBanner({
        type: hallucinationTest ? 'warning' : 'success',
        text: hallucinationTest
          ? '🛡️ Simulated AI Hallucination Attack: Invented PNR & fake $350 EU261 refund were blocked and replaced with verified booking data!'
          : '✓ Generated all 6 recovery emails from your trip data.',
      });
    } catch (err) {
      setStatusBanner({
        type: 'error',
        text: err?.response?.data?.detail || err?.message || 'Failed to generate emails',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClearInbox = async () => {
    setLoading(true);
    setStatusBanner(null);
    try {
      await api.clearNotificationInbox();
      const emptyRes = await api.getNotificationInbox('ALL');
      setInboxData(emptyRes);
      setSelectedMessage(null);
      setStatusBanner({
        type: 'info',
        text: 'Inbox cleared (0 emails).',
      });
    } catch (err) {
      setStatusBanner({
        type: 'error',
        text: err?.response?.data?.detail || err?.message || 'Failed to clear inbox',
      });
    } finally {
      setLoading(false);
    }
  };

  const messages = inboxData?.messages || [];

  return (
    <div className="space-y-5">
      {/* Clean Header Bar */}
      <div className="rounded-3xl border border-white/[0.08] bg-[#070b16]/80 backdrop-blur-2xl p-6 shadow-glass-card flex flex-col sm:flex-row sm:items-center justify-between gap-4 relative overflow-hidden">
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-sky-400/30 to-transparent pointer-events-none" />
        <div>
          <h2 className="text-xl font-extrabold text-white flex items-center gap-2 font-display tracking-tight">
            <MailCheck className="w-5 h-5 text-emerald-400" />
            <span>Sent Recovery Emails ({messages.length})</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1 font-sans">
            Emails sent automatically to the traveler, hotel, railway supplier, and emergency contact.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => handleGenerateAllSix(false)}
            disabled={loading}
            className="px-4 py-2.5 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50 text-white text-xs font-bold flex items-center gap-1.5 cursor-pointer transition shadow-[0_0_15px_rgba(16,185,129,0.3)] font-display"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{loading ? 'Working...' : 'Generate 6 Emails'}</span>
          </button>

          <button
            type="button"
            onClick={() => handleGenerateAllSix(true)}
            disabled={loading}
            className="px-4 py-2.5 rounded-2xl bg-gradient-to-r from-amber-600 to-rose-600 hover:from-amber-500 hover:to-rose-500 disabled:opacity-50 text-white text-xs font-bold flex items-center gap-1.5 cursor-pointer transition shadow-[0_0_15px_rgba(245,158,11,0.25)] font-display"
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Test Hallucination Guardrail</span>
          </button>

          {messages.length > 0 && (
            <button
              type="button"
              onClick={handleClearInbox}
              disabled={loading}
              className="px-3.5 py-2.5 rounded-2xl bg-[#04060d] hover:bg-rose-950/40 disabled:opacity-50 text-slate-400 hover:text-rose-300 border border-white/[0.08] hover:border-rose-500/30 text-xs font-semibold flex items-center gap-1.5 cursor-pointer transition font-mono"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear Inbox</span>
            </button>
          )}
        </div>
      </div>

      {/* Feedback Banner */}
      {statusBanner && (
        <div
          className={`rounded-2xl px-5 py-3.5 text-xs font-medium flex items-center justify-between border backdrop-blur-xl ${
            statusBanner.type === 'success'
              ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-200 shadow-[0_0_15px_rgba(16,185,129,0.15)]'
              : statusBanner.type === 'warning'
              ? 'bg-amber-950/30 border-amber-500/40 text-amber-200 shadow-[0_0_15px_rgba(245,158,11,0.15)]'
              : statusBanner.type === 'error'
              ? 'bg-rose-950/30 border-rose-500/40 text-rose-200 shadow-[0_0_15px_rgba(244,63,94,0.15)]'
              : 'bg-[#070b16] border-white/[0.08] text-slate-300'
          }`}
        >
          <span className="font-sans leading-relaxed">{statusBanner.text}</span>
          <button
            type="button"
            onClick={() => setStatusBanner(null)}
            className="ml-4 text-slate-400 hover:text-white font-bold cursor-pointer font-mono"
          >
            ✕
          </button>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-1.5">
        {CATEGORY_ORDER.map((cat) => (
          <button
            type="button"
            key={cat.key}
            onClick={() => setSelectedCategory(cat.key)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold cursor-pointer transition font-mono ${
              selectedCategory === cat.key
                ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white shadow-[0_0_12px_rgba(14,165,233,0.3)]'
                : 'bg-[#070b16] text-slate-400 hover:text-white border border-white/[0.08] hover:border-white/20'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Empty State or Split Email Viewer */}
      {messages.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-white/[0.12] bg-[#070b16]/60 backdrop-blur-xl p-12 text-center space-y-3">
          <div className="text-base font-bold text-white font-display">No emails in inbox</div>
          <p className="text-xs text-slate-400 max-w-md mx-auto font-sans leading-relaxed">
            Emails are automatically created when you click <strong>Auto-Recover Trip with AI</strong> on your journey, or you can click <strong>Generate 6 Emails</strong> above.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* Left: Email List */}
          <div className="lg:col-span-5 space-y-2 max-h-[540px] overflow-y-auto pr-1">
            {messages.map((msg) => {
              const isSelected = selectedMessage?.notification_id === msg.notification_id;
              const hadFallback = msg.validation?.fallback_applied;
              return (
                <div
                  key={msg.notification_id}
                  onClick={() => setSelectedMessage(msg)}
                  className={`p-4 rounded-2xl border transition cursor-pointer text-xs space-y-2 backdrop-blur-xl ${
                    isSelected
                      ? 'border-sky-400/60 bg-sky-500/15 shadow-[0_0_15px_rgba(56,189,248,0.2)]'
                      : 'border-white/[0.08] bg-[#070b16]/80 hover:border-white/20 hover:bg-[#070b16]'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="px-2.5 py-0.5 rounded-full bg-white/[0.06] text-sky-300 font-mono font-semibold text-[10px] border border-white/[0.08]">
                      {msg.category_label}
                    </span>
                    <span
                      className={`px-2.5 py-0.5 rounded-full font-mono text-[10px] font-bold border ${
                        hadFallback
                          ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                          : 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                      }`}
                    >
                      {hadFallback ? 'GUARDRAIL BLOCKED' : 'SENT'}
                    </span>
                  </div>
                  <div className="font-bold text-white line-clamp-1 font-display">{msg.subject}</div>
                  <div className="text-[11px] text-slate-400 truncate font-mono">To: {msg.recipient}</div>
                </div>
              );
            })}
          </div>

          {/* Right: Selected Email Content */}
          <div className="lg:col-span-7">
            {selectedMessage && (
              <div className="rounded-3xl border border-white/[0.08] bg-[#070b16]/80 backdrop-blur-2xl p-6 space-y-4 shadow-glass-card">
                <div className="border-b border-white/[0.08] pb-4">
                  <div className="text-xs text-sky-400 font-semibold font-mono">
                    {selectedMessage.category_label}
                  </div>
                  <h3 className="text-base sm:text-lg font-bold text-white mt-1 font-display">
                    {selectedMessage.subject}
                  </h3>
                  <div className="text-xs text-slate-400 mt-1.5 flex flex-wrap gap-4 font-mono">
                    <span>To: <strong className="text-slate-200">{selectedMessage.recipient}</strong></span>
                    <span>Booking: {selectedMessage.related_booking}</span>
                  </div>
                </div>

                {selectedMessage.validation?.fallback_applied && (
                  <div className="p-4 rounded-2xl border border-amber-500/40 bg-amber-950/20 space-y-2 text-xs backdrop-blur-xl">
                    <div className="font-bold text-amber-300 flex items-center gap-2 font-display">
                      <ShieldAlert className="w-4 h-4 text-amber-400" />
                      <span>Hallucination Blocked by Fact Validator:</span>
                    </div>
                    <div className="text-[11px] font-mono text-rose-300 space-y-0.5 pl-6">
                      {(selectedMessage.validation.hallucinations_detected || []).map((v, i) => (
                        <div key={i}>&bull; {v}</div>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <div className="text-[11px] text-emerald-400 font-semibold mb-2 flex items-center gap-1.5 font-mono">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Verified Fact-Grounded Email Body</span>
                  </div>
                  <pre className="p-4 sm:p-5 rounded-2xl bg-[#04060d] border border-white/[0.08] text-xs font-sans text-slate-200 whitespace-pre-wrap leading-relaxed shadow-inner">
                    {selectedMessage.message}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
