import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  CheckSquare,
  Square,
  ShieldAlert,
  Sliders,
  DollarSign,
  Ban,
  Clock
} from 'lucide-react';

const REJECTION_REASONS = [
  "I don't want this airline",
  "Too expensive",
  "Arrival time is too late",
  "Departure time is inconvenient",
  "I don't want this booking changed",
  "Prefer another transport option",
  "Other"
];

export function RejectionDialog({
  open = false,
  onClose,
  onSubmit,
  revisionCount = 1,
  maxRevisions = 3,
  previousConstraints = null,
  submitting = false,
}) {
  const [selectedReasons, setSelectedReasons] = useState([]);
  const [customFeedback, setCustomFeedback] = useState('');

  if (!open) return null;

  const toggleReason = (reason) => {
    if (selectedReasons.includes(reason)) {
      setSelectedReasons(selectedReasons.filter((r) => r !== reason));
    } else {
      setSelectedReasons([...selectedReasons, reason]);
    }
  };

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (onSubmit) {
      onSubmit({
        reasons: selectedReasons,
        feedbackText: customFeedback.trim(),
      });
    }
  };

  // Extract descriptions from previousConstraints
  const retainedList = previousConstraints?.descriptions || (
    Array.isArray(previousConstraints) ? previousConstraints : []
  );

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: 10 }}
          transition={{ duration: 0.18 }}
          className="w-full max-w-lg rounded-2xl border border-amber-500/35 bg-surface-container-lowest/95 p-5 sm:p-6 shadow-[0_20px_50px_rgba(0,0,0,0.7)] backdrop-blur-2xl text-on-surface relative overflow-hidden"
        >
          {/* Ambient Glow */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />

          {/* Header */}
          <div className="flex items-start justify-between gap-3 relative z-10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 shrink-0">
                <Sliders className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base sm:text-lg font-bold text-white font-display">
                    Reject Recovery Plan &amp; Request Revision
                  </h3>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase bg-amber-500/20 text-amber-300 border border-amber-500/40">
                    Rev {revisionCount} of {maxRevisions}
                  </span>
                </div>
                <p className="text-xs text-amber-200/90 font-medium font-sans mt-0.5">
                  Why are you rejecting this recovery plan?
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-surface-container-high transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="mt-4 space-y-4 relative z-10">
            {/* Retained Constraints Callout */}
            {retainedList.length > 0 && (
              <div className="p-2.5 rounded-xl border border-sky-500/30 bg-sky-950/20 text-xs text-sky-200 space-y-1 font-sans">
                <span className="text-[10px] uppercase font-mono font-bold text-sky-400 block tracking-wider">
                  Previously rejected constraints (strictly retained):
                </span>
                <div className="flex flex-wrap gap-1.5 pt-0.5">
                  {retainedList.map((desc, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded-md bg-sky-500/15 border border-sky-500/30 text-[11px] text-sky-300 font-mono"
                    >
                      ✓ {desc}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Checkbox Options */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 font-display block">
                Select applicable reasons:
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                {REJECTION_REASONS.map((reason) => {
                  const isChecked = selectedReasons.includes(reason);
                  return (
                    <button
                      type="button"
                      key={reason}
                      onClick={() => toggleReason(reason)}
                      disabled={submitting}
                      className={`px-2.5 py-2 rounded-lg border text-left text-xs transition flex items-center gap-2 cursor-pointer ${
                        isChecked
                          ? 'border-amber-500/60 bg-amber-500/15 text-white font-medium'
                          : 'border-surface-container-high bg-surface-container-low/60 text-slate-300 hover:bg-surface-container-high hover:text-white'
                      }`}
                    >
                      {isChecked ? (
                        <CheckSquare className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                      ) : (
                        <Square className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                      )}
                      <span className="truncate">{reason}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Free-text Feedback */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-slate-300 font-display">
                  Additional constraints &amp; feedback:
                </label>
                <span className="text-[11px] text-slate-400 font-mono">
                  Translates to OR-Tools constraints
                </span>
              </div>
              <textarea
                value={customFeedback}
                onChange={(e) => setCustomFeedback(e.target.value)}
                disabled={submitting}
                rows={3}
                placeholder='e.g., "I don&#39;t want Airline A and I don&#39;t want to pay more than ₹5,000."'
                className="w-full px-3 py-2 rounded-xl bg-surface-container-lowest border border-surface-container-high text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400 font-sans leading-relaxed resize-none"
              />
            </div>

            {/* Quick preset suggestions */}
            <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-slate-400">
              <span className="text-outline text-[10px] font-mono uppercase">Quick Add:</span>
              <button
                type="button"
                onClick={() => setCustomFeedback((prev) => (prev ? `${prev} Exclude Airline A.` : "I don't want Airline A."))}
                className="px-2 py-0.5 rounded-md bg-surface-container-high hover:bg-surface-container-highest text-slate-300 hover:text-white border border-surface-container-high transition cursor-pointer"
              >
                + Exclude Airline A
              </button>
              <button
                type="button"
                onClick={() => setCustomFeedback((prev) => (prev ? `${prev} Maximum budget ₹5,000.` : "Maximum budget is ₹5,000."))}
                className="px-2 py-0.5 rounded-md bg-surface-container-high hover:bg-surface-container-highest text-slate-300 hover:text-white border border-surface-container-high transition cursor-pointer"
              >
                + Max Budget ₹5,000
              </button>
              <button
                type="button"
                onClick={() => setCustomFeedback((prev) => (prev ? `${prev} Train only.` : "Prefer train only."))}
                className="px-2 py-0.5 rounded-md bg-surface-container-high hover:bg-surface-container-highest text-slate-300 hover:text-white border border-surface-container-high transition cursor-pointer"
              >
                + Train Only
              </button>
            </div>

            {/* Footer Buttons */}
            <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-surface-container-high">
              <button
                type="button"
                onClick={onClose}
                disabled={submitting}
                className="px-3.5 py-1.5 rounded-lg border border-surface-container-high bg-surface-container-lowest hover:bg-surface-container-high text-xs text-slate-300 hover:text-white font-medium transition cursor-pointer font-display h-8"
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white text-xs font-bold flex items-center gap-2 shadow-[0_0_15px_rgba(245,158,11,0.25)] transition cursor-pointer font-display h-8 disabled:opacity-50"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>{submitting ? 'Formulating Revised Plan...' : 'Submit Rejection & Replan'}</span>
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

export default RejectionDialog;
