import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  ShieldCheck,
  Info,
  X,
  Inbox
} from 'lucide-react';

/**
 * Standardized Journey & Segment Status Indicators required in Stage 11:
 * - ✓ Safe
 * - ⚠ At Risk
 * - ❌ Disrupted
 * - 🔄 Recovery in Progress
 * - ✓ Recovered
 */
export const JOURNEY_STATUS_CONFIG = {
  SAFE: {
    key: 'SAFE',
    badgeText: '✓ Safe',
    classes: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    dotClass: 'bg-emerald-400',
  },
  AT_RISK: {
    key: 'AT_RISK',
    badgeText: '⚠ At Risk',
    classes: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    dotClass: 'bg-amber-400',
  },
  DISRUPTED: {
    key: 'DISRUPTED',
    badgeText: '❌ Disrupted',
    classes: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
    dotClass: 'bg-rose-400',
  },
  RECOVERY_IN_PROGRESS: {
    key: 'RECOVERY_IN_PROGRESS',
    badgeText: '🔄 Recovery in Progress',
    classes: 'bg-sky-500/15 text-sky-300 border-sky-500/30',
    dotClass: 'bg-sky-400 animate-spin',
  },
  RECOVERED: {
    key: 'RECOVERED',
    badgeText: '✓ Recovered',
    classes: 'bg-teal-500/20 text-teal-200 border-teal-400/40',
    dotClass: 'bg-teal-400',
  },
};

export function JourneyStatusBadge({ status = 'SAFE', size = 'md' }) {
  const normalized = String(status).toUpperCase().replace(/\s+/g, '_');
  const cfg = JOURNEY_STATUS_CONFIG[normalized] || JOURNEY_STATUS_CONFIG.SAFE;
  const sizeClasses =
    size === 'sm'
      ? 'px-2 py-0.5 text-[11px]'
      : size === 'lg'
      ? 'px-3.5 py-1.5 text-xs'
      : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-semibold border ${cfg.classes} ${sizeClasses}`}
    >
      <span>{cfg.badgeText}</span>
    </span>
  );
}

export function ToastViewport({ toasts = [], onDismiss }) {
  if (!toasts || toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none">
      {toasts.map((t) => {
        const toneStyles =
          t.type === 'error'
            ? 'border-rose-500/40 bg-slate-900/95 text-rose-200'
            : t.type === 'warning'
            ? 'border-amber-500/40 bg-slate-900/95 text-amber-200'
            : t.type === 'websocket'
            ? 'border-indigo-500/50 bg-indigo-950/95 text-indigo-100'
            : 'border-emerald-500/40 bg-slate-900/95 text-emerald-200';

        return (
          <div
            key={t.id}
            className={`pointer-events-auto rounded-2xl border p-3.5 shadow-2xl backdrop-blur flex items-start justify-between gap-3 transition-all ${toneStyles}`}
          >
            <div className="flex items-start gap-2.5">
              {t.type === 'error' ? (
                <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              ) : t.type === 'warning' ? (
                <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              ) : t.type === 'websocket' ? (
                <RefreshCw className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5 animate-spin" />
              ) : (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              )}
              <div className="text-xs space-y-0.5">
                <div className="font-bold text-white">{t.title}</div>
                {t.message && <div className="text-slate-300 leading-relaxed">{t.message}</div>}
              </div>
            </div>
            <button
              onClick={() => onDismiss(t.id)}
              className="text-slate-400 hover:text-white p-0.5 cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Confirm & Execute',
  cancelLabel = 'Cancel',
  variant = 'primary',
  onConfirm,
  onCancel,
}) {
  if (!open) return null;

  const btnStyle =
    variant === 'danger'
      ? 'bg-rose-600 hover:bg-rose-500 text-white'
      : 'bg-sky-600 hover:bg-sky-500 text-white';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
      <div className="max-w-md w-full rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div
              className={`p-2 rounded-xl border ${
                variant === 'danger'
                  ? 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                  : 'bg-sky-500/10 border-sky-500/30 text-sky-400'
              }`}
            >
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white">{title}</h3>
          </div>
          <button onClick={onCancel} className="text-slate-400 hover:text-white cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed">{description}</p>

        <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-800">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold cursor-pointer"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={`px-4 py-2 rounded-xl text-xs font-bold shadow cursor-pointer ${btnStyle}`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

export function SkeletonLoader({ rows = 3 }) {
  return (
    <div className="space-y-3 animate-pulse">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-20 rounded-2xl bg-slate-900/80 border border-slate-800/70 p-4 flex flex-col justify-between"
        >
          <div className="h-3 w-1/3 bg-slate-800 rounded" />
          <div className="h-2.5 w-2/3 bg-slate-800/70 rounded" />
        </div>
      ))}
    </div>
  );
}

export function EmptyStateBox({ title, description, actionLabel, onAction }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/40 p-10 text-center space-y-3">
      <div className="w-10 h-10 rounded-2xl bg-slate-800/80 border border-slate-700 text-slate-400 flex items-center justify-center mx-auto">
        <Inbox className="w-5 h-5" />
      </div>
      <div className="space-y-1 max-w-md mx-auto">
        <h4 className="text-sm font-bold text-slate-200">{title}</h4>
        <p className="text-xs text-slate-400">{description}</p>
      </div>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold shadow cursor-pointer"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}

export function ErrorAlertBanner({ error, onRetry }) {
  if (!error) return null;
  return (
    <div className="rounded-2xl border border-rose-500/40 bg-rose-950/30 p-4 flex items-center justify-between gap-4 text-xs">
      <div className="flex items-center gap-2.5 text-rose-200">
        <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
        <span>{error}</span>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-3 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold shrink-0 cursor-pointer"
        >
          Retry Sync
        </button>
      )}
    </div>
  );
}
