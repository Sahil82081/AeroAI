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
 * Standardized Journey & Segment Status Indicators matching Stitch Reference Design:
 * - Safe
 * - At Risk
 * - Disrupted
 * - Recovery in Progress
 * - Recovered
 */
export const JOURNEY_STATUS_CONFIG = {
  SAFE: {
    key: 'SAFE',
    badgeText: 'Safe',
    classes: 'bg-surface-container-high border-primary/20 text-primary-fixed-dim shadow-sm',
    dotClass: 'bg-primary-container shadow-[0_0_8px_rgba(0,229,255,0.8)] animate-pulse',
  },
  AT_RISK: {
    key: 'AT_RISK',
    badgeText: 'At Risk',
    classes: 'bg-surface-container-high border-amber-500/30 text-amber-300 shadow-sm',
    dotClass: 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]',
  },
  DISRUPTED: {
    key: 'DISRUPTED',
    badgeText: 'Disrupted',
    classes: 'bg-surface-container-high border-error/30 text-error shadow-sm',
    dotClass: 'bg-error shadow-[0_0_8px_rgba(255,180,171,0.8)]',
  },
  RECOVERY_IN_PROGRESS: {
    key: 'RECOVERY_IN_PROGRESS',
    badgeText: 'Recovery in Progress',
    classes: 'bg-surface-container-high border-primary-container/30 text-primary-container shadow-sm',
    dotClass: 'bg-primary-container shadow-[0_0_8px_rgba(0,229,255,0.8)] animate-spin',
  },
  RECOVERED: {
    key: 'RECOVERED',
    badgeText: 'Recovered',
    classes: 'bg-surface-container-high border-primary/30 text-primary shadow-sm',
    dotClass: 'bg-primary shadow-[0_0_8px_rgba(195,245,255,0.8)]',
  },
};

export function JourneyStatusBadge({ status = 'SAFE', size = 'md' }) {
  const normalized = String(status).toUpperCase().replace(/\s+/g, '_');
  const cfg = JOURNEY_STATUS_CONFIG[normalized] || JOURNEY_STATUS_CONFIG.SAFE;
  const sizeClasses =
    size === 'sm'
      ? 'px-2 py-0.5 text-[10px] tracking-wider'
      : size === 'lg'
      ? 'px-3 py-1 text-xs tracking-wider'
      : 'px-2.5 py-0.5 text-[11px] tracking-wider';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-label-caps font-bold uppercase border backdrop-blur-md transition-all ${cfg.classes} ${sizeClasses}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dotClass}`} />
      <span>{cfg.badgeText}</span>
    </span>
  );
}

export function PulseBadge({ label = 'Live', color = 'sky', pulse = true }) {
  const colorMap = {
    sky: 'bg-surface-container-high text-primary-fixed-dim border-primary/20',
    indigo: 'bg-surface-container-high text-secondary border-secondary/30',
    violet: 'bg-surface-container-high text-secondary-fixed-dim border-secondary/30',
    emerald: 'bg-surface-container-high text-primary-container border-primary-container/30',
    amber: 'bg-surface-container-high text-amber-300 border-amber-500/30',
    rose: 'bg-surface-container-high text-error border-error/30',
  };

  const dotMap = {
    sky: 'bg-primary-container shadow-[0_0_8px_rgba(0,229,255,0.8)]',
    indigo: 'bg-secondary shadow-[0_0_8px_rgba(182,196,255,0.8)]',
    violet: 'bg-secondary-fixed shadow-[0_0_8px_rgba(220,225,255,0.8)]',
    emerald: 'bg-primary-container shadow-[0_0_8px_rgba(0,229,255,0.8)]',
    amber: 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]',
    rose: 'bg-error shadow-[0_0_8px_rgba(255,180,171,0.8)]',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-label-caps font-bold tracking-wider uppercase border backdrop-blur-md ${colorMap[color] || colorMap.sky}`}
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
  glowColor = 'cyan',
  onClick,
}) {
  return (
    <div
      onClick={onClick}
      className={`rounded-xl border border-surface-container-high bg-surface-container-low/90 backdrop-blur-md shadow-sm transition-all duration-200 relative overflow-hidden group ${
        hoverEffect ? 'hover:border-primary-container/40 hover:-translate-y-0.5 cursor-pointer' : ''
      } ${className}`}
    >
      <div className="absolute -right-6 -top-6 w-28 h-28 bg-primary-container/5 rounded-full blur-xl group-hover:bg-primary-container/10 transition-all pointer-events-none" />
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
  color = 'cyan',
  delay = 0,
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: [0.22, 1, 0.36, 1] }}
      className="p-4 sm:p-4.5 rounded-xl border border-surface-container-high bg-surface-container-low/90 backdrop-blur-md shadow-sm hover:border-primary-container/40 hover:-translate-y-0.5 transition-all duration-200 relative group overflow-hidden"
    >
      <div className="absolute -right-6 -top-6 w-28 h-28 bg-primary-container/5 rounded-full blur-xl group-hover:bg-primary-container/10 transition-all pointer-events-none" />
      
      <div className="flex items-start justify-between gap-3 relative z-10">
        <div className="space-y-0.5">
          <div className="text-[11px] font-label-caps uppercase tracking-wider text-outline font-semibold">
            {title}
          </div>
          <div className="text-2xl sm:text-3xl font-black tracking-tight font-headline-md mt-0.5 text-on-surface">
            {typeof value === 'number' ? <CountUpNumber value={value} /> : value}
          </div>
          {subtext && (
            <div className="text-xs text-on-surface-variant mt-0.5 leading-normal">
              {subtext}
            </div>
          )}
        </div>

        {Icon && (
          <div className="w-8 h-8 rounded-lg bg-surface-container-high border border-primary/20 flex items-center justify-center text-primary-container shadow-sm shrink-0 group-hover:scale-105 transition-transform duration-200">
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      {trend && (
        <div className="mt-2.5 pt-2 border-t border-surface-container-high/60 flex items-center gap-1.5 text-xs text-outline font-mono">
          <span className="text-primary-container font-bold flex items-center">
            {trend} <ArrowUpRight className="w-3 h-3 ml-0.5" />
          </span>
          <span className="text-outline/40">&bull;</span>
          <span>vs nominal schedule</span>
        </div>
      )}
    </motion.div>
  );
}

export function ToastViewport({ toasts = [], onDismiss }) {
  if (!toasts || toasts.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none">
      <AnimatePresence>
        {toasts.map((t) => {
          const toneStyles =
            t.type === 'error'
              ? 'border-error/40 bg-surface-container-low/95 text-error shadow-2xl'
              : t.type === 'warning'
              ? 'border-amber-500/40 bg-surface-container-low/95 text-amber-300 shadow-2xl'
              : t.type === 'websocket'
              ? 'border-primary-container/50 bg-surface-container-low/95 text-primary-container shadow-2xl'
              : 'border-primary/40 bg-surface-container-low/95 text-on-surface shadow-2xl';

          return (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, x: 50, scale: 0.9 }}
              transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
              className={`pointer-events-auto rounded-2xl border p-4 shadow-2xl backdrop-blur-2xl flex items-start justify-between gap-3 ${toneStyles}`}
            >
              <div className="flex items-start gap-3">
                {t.type === 'error' ? (
                  <div className="p-1.5 rounded-lg bg-surface-container-high text-error shrink-0 mt-0.5 border border-error/30">
                    <XCircle className="w-4 h-4" />
                  </div>
                ) : t.type === 'warning' ? (
                  <div className="p-1.5 rounded-lg bg-surface-container-high text-amber-300 shrink-0 mt-0.5 border border-amber-500/30">
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                ) : t.type === 'websocket' ? (
                  <div className="p-1.5 rounded-lg bg-surface-container-high text-primary-container shrink-0 mt-0.5 border border-primary-container/30 animate-spin">
                    <RefreshCw className="w-4 h-4" />
                  </div>
                ) : (
                  <div className="p-1.5 rounded-lg bg-surface-container-high text-primary-container shrink-0 mt-0.5 border border-primary/20">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                )}
                <div className="text-xs space-y-0.5">
                  <div className="font-bold text-on-surface font-title-sm tracking-tight">{t.title}</div>
                  {t.message && <div className="text-on-surface-variant leading-relaxed font-body-sm">{t.message}</div>}
                </div>
              </div>
              <button
                onClick={() => onDismiss(t.id)}
                className="text-outline hover:text-on-surface p-1 rounded-lg hover:bg-surface-container-high transition cursor-pointer"
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
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-surface-container-lowest/80 backdrop-blur-md">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
            className="max-w-md w-full rounded-xl border border-surface-container-high bg-surface-container-low p-4 sm:p-5 shadow-xl space-y-3 relative overflow-hidden"
          >
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary-container/40 to-transparent" />
            
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <div
                  className={`p-2 rounded-lg border ${
                    variant === 'danger'
                      ? 'bg-surface-container-high border-error/30 text-error'
                      : 'bg-surface-container-high border-primary/30 text-primary-container'
                  }`}
                >
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <h3 className="text-sm sm:text-base font-bold text-on-surface font-headline-md">{title}</h3>
              </div>
              <button
                onClick={onCancel}
                className="text-outline hover:text-on-surface p-1 rounded-lg hover:bg-surface-container-high transition cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            <p className="text-xs text-on-surface-variant leading-relaxed">{description}</p>

            <div className="flex items-center justify-end gap-2 pt-2.5 border-t border-surface-container-high">
              <button
                onClick={onCancel}
                className="px-3.5 py-1.5 rounded-lg bg-surface-container-high hover:bg-surface-container-highest text-on-surface text-xs font-semibold border border-surface-container-high transition cursor-pointer h-8"
              >
                {cancelLabel}
              </button>
              <button
                onClick={onConfirm}
                className={`px-4 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer h-8 ${
                  variant === 'danger'
                    ? 'bg-error-container text-on-error-container hover:brightness-110 shadow-sm'
                    : 'bg-gradient-to-r from-primary-container to-primary-fixed-dim text-on-primary shadow-sm hover:brightness-110'
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
    <div className="space-y-2.5">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-20 rounded-xl bg-surface-container-low/70 border border-surface-container-high/60 p-3 flex flex-col justify-between relative overflow-hidden"
        >
          <div className="absolute inset-0 shimmer-wave" />
          <div className="h-3.5 w-1/3 bg-surface-container-high rounded-md" />
          <div className="space-y-1">
            <div className="h-2.5 w-3/4 bg-surface-container-high/70 rounded-md" />
            <div className="h-2 w-1/2 bg-surface-container-high/50 rounded-md" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function EmptyStateBox({ title, description, actionLabel, onAction }) {
  return (
    <div className="rounded-xl border border-dashed border-surface-container-high bg-surface-container-low/40 p-6 text-center space-y-3 backdrop-blur-md relative overflow-hidden">
      <div className="w-10 h-10 rounded-xl bg-surface-container-high border border-primary/20 text-primary-container flex items-center justify-center mx-auto shadow-sm">
        <Inbox className="w-5 h-5" />
      </div>
      <div className="space-y-1 max-w-md mx-auto">
        <h4 className="text-xs sm:text-sm font-bold text-on-surface font-headline-md">{title}</h4>
        <p className="text-xs text-on-surface-variant leading-relaxed">{description}</p>
      </div>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 rounded-lg bg-gradient-to-r from-primary-container to-primary-fixed-dim text-on-primary text-xs font-bold shadow-sm transition cursor-pointer hover:brightness-110 h-8"
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
      className="rounded-xl border border-error/40 bg-surface-container-low p-4 sm:p-4.5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4 text-xs sm:text-sm backdrop-blur-md shadow-sm"
    >
      <div className="flex items-center gap-3 text-error">
        <XCircle className="w-5 h-5 text-error shrink-0" />
        <span className="font-medium leading-relaxed">{error}</span>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 rounded-lg bg-error-container text-on-error-container font-bold shrink-0 cursor-pointer transition shadow hover:brightness-110 text-xs h-9 flex items-center justify-center gap-2"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry Sync</span>
        </button>
      )}
    </motion.div>
  );
}
