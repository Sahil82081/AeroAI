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
      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <MailCheck className="w-5 h-5 text-emerald-400" />
            <span>Sent Recovery Emails ({messages.length})</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Emails sent automatically to the traveler, hotel, railway supplier, and emergency contact.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => handleGenerateAllSix(false)}
            disabled={loading}
            className="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-bold flex items-center gap-1.5 cursor-pointer"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{loading ? 'Working...' : 'Generate 6 Emails'}</span>
          </button>

          <button
            type="button"
            onClick={() => handleGenerateAllSix(true)}
            disabled={loading}
            className="px-3.5 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-xs font-bold flex items-center gap-1.5 cursor-pointer"
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Test Hallucination Guardrail</span>
          </button>

          {messages.length > 0 && (
            <button
              type="button"
              onClick={handleClearInbox}
              disabled={loading}
              className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-rose-950/60 disabled:opacity-50 text-slate-300 hover:text-rose-200 border border-slate-700 text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
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
          className={`rounded-xl px-4 py-3 text-xs font-medium flex items-center justify-between border ${
            statusBanner.type === 'success'
              ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-200'
              : statusBanner.type === 'warning'
              ? 'bg-amber-950/30 border-amber-500/40 text-amber-200'
              : statusBanner.type === 'error'
              ? 'bg-rose-950/30 border-rose-500/40 text-rose-200'
              : 'bg-slate-900 border-slate-800 text-slate-300'
          }`}
        >
          <span>{statusBanner.text}</span>
          <button
            type="button"
            onClick={() => setStatusBanner(null)}
            className="ml-4 text-slate-400 hover:text-white font-bold cursor-pointer"
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
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold cursor-pointer ${
              selectedCategory === cat.key
                ? 'bg-sky-600 text-white'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Empty State or Split Email Viewer */}
      {messages.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/40 p-12 text-center space-y-3">
          <div className="text-base font-bold text-slate-200">No emails in inbox</div>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
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
                  className={`p-3.5 rounded-xl border transition cursor-pointer text-xs space-y-1.5 ${
                    isSelected
                      ? 'border-sky-500 bg-sky-950/25'
                      : 'border-slate-800 bg-slate-900/70 hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-sky-300 font-semibold text-[10px]">
                      {msg.category_label}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold ${
                        hadFallback
                          ? 'bg-amber-500/20 text-amber-300'
                          : 'bg-emerald-500/15 text-emerald-300'
                      }`}
                    >
                      {hadFallback ? 'GUARDRAIL BLOCKED' : 'SENT'}
                    </span>
                  </div>
                  <div className="font-bold text-white line-clamp-1">{msg.subject}</div>
                  <div className="text-[11px] text-slate-400 truncate">To: {msg.recipient}</div>
                </div>
              );
            })}
          </div>

          {/* Right: Selected Email Content */}
          <div className="lg:col-span-7">
            {selectedMessage && (
              <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 space-y-4">
                <div className="border-b border-slate-800 pb-3">
                  <div className="text-xs text-sky-400 font-semibold">
                    {selectedMessage.category_label}
                  </div>
                  <h3 className="text-base font-bold text-white mt-0.5">
                    {selectedMessage.subject}
                  </h3>
                  <div className="text-xs text-slate-400 mt-1 flex flex-wrap gap-4 font-mono">
                    <span>To: {selectedMessage.recipient}</span>
                    <span>Booking: {selectedMessage.related_booking}</span>
                  </div>
                </div>

                {selectedMessage.validation?.fallback_applied && (
                  <div className="p-3.5 rounded-xl border border-amber-500/40 bg-amber-950/20 space-y-1.5 text-xs">
                    <div className="font-bold text-amber-300 flex items-center gap-1.5">
                      <ShieldAlert className="w-4 h-4 text-amber-400" />
                      <span>Hallucination Blocked by Fact Validator:</span>
                    </div>
                    <div className="text-[11px] font-mono text-rose-300 space-y-0.5">
                      {(selectedMessage.validation.hallucinations_detected || []).map((v, i) => (
                        <div key={i}>&bull; {v}</div>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <div className="text-[11px] text-emerald-400 font-semibold mb-1.5 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Verified Email Body</span>
                  </div>
                  <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs font-sans text-slate-200 whitespace-pre-wrap leading-relaxed">
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
