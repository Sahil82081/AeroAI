import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  ShieldCheck,
  X,
  Inbox,
  Sparkles,
  ArrowUpRight
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
    classes: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30 shadow-[0_0_12px_rgba(16,185,129,0.2)]',
    dotClass: 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]',
  },
  AT_RISK: {
    key: 'AT_RISK',
    badgeText: '⚠ At Risk',
    classes: 'bg-amber-500/15 text-amber-300 border-amber-500/30 shadow-[0_0_12px_rgba(245,158,11,0.2)]',
    dotClass: 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]',
  },
  DISRUPTED: {
    key: 'DISRUPTED',
    badgeText: '❌ Disrupted',
    classes: 'bg-rose-500/15 text-rose-300 border-rose-500/30 shadow-[0_0_12px_rgba(244,63,94,0.2)]',
    dotClass: 'bg-rose-400 shadow-[0_0_8px_rgba(251,113,133,0.8)]',
  },
  RECOVERY_IN_PROGRESS: {
    key: 'RECOVERY_IN_PROGRESS',
    badgeText: '🔄 Recovery in Progress',
    classes: 'bg-sky-500/15 text-sky-300 border-sky-500/30 shadow-[0_0_12px_rgba(14,165,233,0.25)]',
    dotClass: 'bg-sky-400 shadow-[0_0_8px_rgba(56,189,248,0.8)] animate-spin',
  },
  RECOVERED: {
    key: 'RECOVERED',
    badgeText: '✓ Recovered',
    classes: 'bg-teal-500/20 text-teal-200 border-teal-400/40 shadow-[0_0_12px_rgba(20,184,166,0.25)]',
    dotClass: 'bg-teal-400 shadow-[0_0_8px_rgba(45,212,191,0.8)]',
  },
};

export function JourneyStatusBadge({ status = 'SAFE', size = 'md' }) {
  const normalized = String(status).toUpperCase().replace(/\s+/g, '_');
  const cfg = JOURNEY_STATUS_CONFIG[normalized] || JOURNEY_STATUS_CONFIG.SAFE;
  const sizeClasses =
    size === 'sm'
      ? 'px-2 py-0.5 text-[10px] tracking-wide'
      : size === 'lg'
      ? 'px-3.5 py-1.5 text-xs tracking-wide'
      : 'px-2.5 py-1 text-xs tracking-wide';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium font-mono border backdrop-blur-md transition-all ${cfg.classes} ${sizeClasses}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dotClass}`} />
      <span>{cfg.badgeText}</span>
    </span>
  );
}

export function PulseBadge({ label = 'Live', color = 'sky', pulse = true }) {
  const colorMap = {
    sky: 'bg-sky-500/15 text-sky-300 border-sky-500/30',
    indigo: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
    violet: 'bg-violet-500/15 text-violet-300 border-violet-500/30',
    emerald: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    amber: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    rose: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  };

  const dotMap = {
    sky: 'bg-sky-400 shadow-[0_0_8px_rgba(56,189,248,0.8)]',
    indigo: 'bg-indigo-400 shadow-[0_0_8px_rgba(129,140,248,0.8)]',
    violet: 'bg-violet-400 shadow-[0_0_8px_rgba(167,139,250,0.8)]',
    emerald: 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]',
    amber: 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]',
    rose: 'bg-rose-400 shadow-[0_0_8px_rgba(251,113,133,0.8)]',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold tracking-wider uppercase border backdrop-blur-md ${colorMap[color] || colorMap.sky}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dotMap[color] || dotMap.sky} ${pulse ? 'animate-pulse' : ''}`} />
      <span>{label}</span>
    </span>
  );
}

export function CountUpNumber({ value, duration = 1200, prefix = '', suffix = '' }) {
  const numericTarget = typeof value === 'number' ? value : parseFloat(String(value).replace(/[^0-9.-]+/g, '')) || 0;
  const isFloat = String(value).includes('.') && !Number.isInteger(numericTarget);
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let startTimestamp = null;
    let animationFrame;

    const step = (timestamp) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = eased * numericTarget;
      setDisplayValue(isFloat ? parseFloat(current.toFixed(1)) : Math.round(current));

      if (progress < 1) {
        animationFrame = requestAnimationFrame(step);
      } else {
        setDisplayValue(numericTarget);
      }
    };

    animationFrame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(animationFrame);
  }, [numericTarget, duration, isFloat]);

  return (
    <span className="tabular-nums font-mono">
      {prefix}{isFloat ? displayValue.toFixed(1) : displayValue}{suffix}
    </span>
  );
}

export function GlassCard({
  children,
  className = '',
  hoverEffect = true,
  glowColor = 'sky',
  onClick,
}) {
  const glowBorder = {
    sky: 'hover:border-sky-500/40 hover:shadow-[0_16px_36px_-4px_rgba(0,0,0,0.6),0_0_24px_-4px_rgba(14,165,233,0.25)]',
    violet: 'hover:border-violet-500/40 hover:shadow-[0_16px_36px_-4px_rgba(0,0,0,0.6),0_0_24px_-4px_rgba(139,92,246,0.25)]',
    emerald: 'hover:border-emerald-500/40 hover:shadow-[0_16px_36px_-4px_rgba(0,0,0,0.6),0_0_24px_-4px_rgba(16,185,129,0.25)]',
    rose: 'hover:border-rose-500/40 hover:shadow-[0_16px_36px_-4px_rgba(0,0,0,0.6),0_0_24px_-4px_rgba(244,63,94,0.25)]',
  };

  return (
    <div
      onClick={onClick}
      className={`rounded-2xl border border-white/[0.08] bg-[#070b16]/75 backdrop-blur-xl shadow-glass-card transition-all duration-300 relative overflow-hidden ${
        hoverEffect ? `hover:-translate-y-1 ${glowBorder[glowColor] || glowBorder.sky} cursor-pointer` : ''
      } ${className}`}
    >
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/15 to-transparent pointer-events-none" />
      {children}
    </div>
  );
}

export function StatCard({
  title,
  value,
  subtext,
  icon: Icon,
  trend,
  color = 'sky',
  delay = 0,
}) {
  const colorMap = {
    sky: {
      iconBg: 'bg-sky-500/15 border-sky-500/30 text-sky-400',
      valueColor: 'text-white',
      accentGlow: 'from-sky-500/10 via-transparent to-transparent',
    },
    violet: {
      iconBg: 'bg-violet-500/15 border-violet-500/30 text-violet-400',
      valueColor: 'text-white',
      accentGlow: 'from-violet-500/10 via-transparent to-transparent',
    },
    emerald: {
      iconBg: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400',
      valueColor: 'text-emerald-400',
      accentGlow: 'from-emerald-500/10 via-transparent to-transparent',
    },
    amber: {
      iconBg: 'bg-amber-500/15 border-amber-500/30 text-amber-400',
      valueColor: 'text-amber-300',
      accentGlow: 'from-amber-500/10 via-transparent to-transparent',
    },
    rose: {
      iconBg: 'bg-rose-500/15 border-rose-500/30 text-rose-400',
      valueColor: 'text-rose-400',
      accentGlow: 'from-rose-500/10 via-transparent to-transparent',
    },
  };

  const scheme = colorMap[color] || colorMap.sky;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: [0.22, 1, 0.36, 1] }}
      className="p-5 rounded-2xl border border-white/[0.08] bg-[#070b16]/75 backdrop-blur-xl shadow-glass-card hover:border-white/20 hover:-translate-y-1 transition-all duration-300 relative group overflow-hidden"
    >
      <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${scheme.accentGlow} rounded-full blur-2xl pointer-events-none group-hover:scale-125 transition-transform duration-500`} />
      
      <div className="flex items-start justify-between gap-3 relative z-10">
        <div className="space-y-1">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider font-mono">
            {title}
          </div>
          <div className={`text-2xl font-bold tracking-tight font-display mt-0.5 ${scheme.valueColor}`}>
            {typeof value === 'number' ? <CountUpNumber value={value} /> : value}
          </div>
          {subtext && (
            <div className="text-[11px] text-slate-400 mt-1 leading-snug">
              {subtext}
            </div>
          )}
        </div>

        {Icon && (
          <div className={`p-3 rounded-xl border ${scheme.iconBg} shadow-inner shrink-0 group-hover:rotate-6 transition-transform duration-300`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      {trend && (
        <div className="mt-3 pt-3 border-t border-white/[0.06] flex items-center gap-1.5 text-[11px] text-slate-400">
          <span className="text-emerald-400 font-semibold font-mono flex items-center">
            {trend} <ArrowUpRight className="w-3 h-3 ml-0.5" />
          </span>
          <span className="text-slate-500">&bull;</span>
          <span>vs nominal schedule</span>
        </div>
      )}
    </motion.div>
  );
}

export function ToastViewport({ toasts = [], onDismiss }) {
  if (!toasts || toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none">
      <AnimatePresence>
        {toasts.map((t) => {
          const toneStyles =
            t.type === 'error'
              ? 'border-rose-500/40 bg-[#0b0c16]/95 text-rose-200 shadow-[0_8px_32px_rgba(244,63,94,0.25)]'
              : t.type === 'warning'
              ? 'border-amber-500/40 bg-[#0f1118]/95 text-amber-200 shadow-[0_8px_32px_rgba(245,158,11,0.25)]'
              : t.type === 'websocket'
              ? 'border-indigo-500/50 bg-[#0a0d24]/95 text-indigo-100 shadow-[0_8px_32px_rgba(99,102,241,0.25)]'
              : 'border-emerald-500/40 bg-[#071318]/95 text-emerald-200 shadow-[0_8px_32px_rgba(16,185,129,0.25)]';

          return (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, x: 50, scale: 0.9 }}
              transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
              className={`pointer-events-auto rounded-2xl border p-4 shadow-2xl backdrop-blur-xl flex items-start justify-between gap-3 ${toneStyles}`}
            >
              <div className="flex items-start gap-3">
                {t.type === 'error' ? (
                  <div className="p-1.5 rounded-lg bg-rose-500/20 text-rose-400 shrink-0 mt-0.5">
                    <XCircle className="w-4 h-4" />
                  </div>
                ) : t.type === 'warning' ? (
                  <div className="p-1.5 rounded-lg bg-amber-500/20 text-amber-400 shrink-0 mt-0.5">
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                ) : t.type === 'websocket' ? (
                  <div className="p-1.5 rounded-lg bg-indigo-500/20 text-indigo-400 shrink-0 mt-0.5 animate-spin">
                    <RefreshCw className="w-4 h-4" />
                  </div>
                ) : (
                  <div className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400 shrink-0 mt-0.5">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                )}
                <div className="text-xs space-y-0.5">
                  <div className="font-bold text-white font-display tracking-tight">{t.title}</div>
                  {t.message && <div className="text-slate-300 leading-relaxed font-sans">{t.message}</div>}
                </div>
              </div>
              <button
                onClick={() => onDismiss(t.id)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/10 transition cursor-pointer"
                aria-label="Dismiss toast"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
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
  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#030712]/80 backdrop-blur-md">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
            className="max-w-md w-full rounded-2xl border border-white/[0.12] bg-[#070b16] p-6 shadow-2xl space-y-4 relative overflow-hidden"
          >
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-sky-400/30 to-transparent" />
            
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <div
                  className={`p-2.5 rounded-xl border ${
                    variant === 'danger'
                      ? 'bg-rose-500/15 border-rose-500/30 text-rose-400'
                      : 'bg-sky-500/15 border-sky-500/30 text-sky-400'
                  }`}
                >
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white font-display">{title}</h3>
              </div>
              <button
                onClick={onCancel}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/10 transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed font-sans">{description}</p>

            <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-white/[0.08]">
              <button
                onClick={onCancel}
                className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-semibold border border-white/[0.08] transition cursor-pointer"
              >
                {cancelLabel}
              </button>
              <button
                onClick={onConfirm}
                className={`px-4 py-2 rounded-xl text-xs font-bold shadow-lg transition cursor-pointer ${
                  variant === 'danger'
                    ? 'bg-rose-600 hover:bg-rose-500 text-white shadow-rose-600/30'
                    : 'bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white shadow-sky-600/30'
                }`}
              >
                {confirmLabel}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

export function SkeletonLoader({ rows = 3 }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-24 rounded-2xl bg-[#070b16]/70 border border-white/[0.06] p-4 flex flex-col justify-between relative overflow-hidden"
        >
          <div className="absolute inset-0 shimmer-wave" />
          <div className="h-4 w-1/3 bg-slate-800/80 rounded-md" />
          <div className="space-y-1.5">
            <div className="h-3 w-3/4 bg-slate-800/50 rounded-md" />
            <div className="h-2.5 w-1/2 bg-slate-800/40 rounded-md" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function EmptyStateBox({ title, description, actionLabel, onAction }) {
  return (
    <div className="rounded-2xl border border-dashed border-white/[0.12] bg-[#070b16]/40 p-10 text-center space-y-4 backdrop-blur-md relative overflow-hidden">
      <div className="w-12 h-12 rounded-2xl bg-sky-500/10 border border-sky-500/20 text-sky-400 flex items-center justify-center mx-auto shadow-inner">
        <Inbox className="w-6 h-6" />
      </div>
      <div className="space-y-1.5 max-w-md mx-auto">
        <h4 className="text-sm font-bold text-white font-display">{title}</h4>
        <p className="text-xs text-slate-400 leading-relaxed">{description}</p>
      </div>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white text-xs font-bold shadow-lg shadow-sky-600/25 transition cursor-pointer"
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
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-rose-500/40 bg-rose-950/25 p-4 flex items-center justify-between gap-4 text-xs backdrop-blur-xl shadow-lg shadow-rose-950/50"
    >
      <div className="flex items-center gap-2.5 text-rose-200">
        <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
        <span className="font-medium">{error}</span>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-3.5 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold shrink-0 cursor-pointer transition shadow"
        >
          Retry Sync
        </button>
      )}
    </motion.div>
  );
}

