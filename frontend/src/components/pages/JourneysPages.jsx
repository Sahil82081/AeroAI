import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plane,
  Train,
  Hotel,
  Compass,
  ArrowDown,
  ArrowRight,
  Calendar,
  MapPin,
  Clock,
  ShieldCheck,
  AlertTriangle,
  Sparkles,
  FileText
} from 'lucide-react';
import { JourneyStatusBadge, EmptyStateBox } from '../ui/SaaSPrimitives';

export function MyJourneysPage({
  journeys = [],
  journeyStatusMode = 'RECOVERED',
  onChangeJourneyStatusMode,
  onNavigate,
}) {
  const [filterStatus, setFilterStatus] = useState('ALL');

  const portfolio = [
    {
      id: journeys[0]?.id || 1,
      title: journeys[0]?.title || 'Golden Triangle Business & Heritage Trip (Mumbai → Delhi → Jaipur)',
      dates: 'Oct 20, 2026 – Oct 23, 2026',
      origin: 'Mumbai (BOM)',
      destination: 'Jaipur (JAI)',
      legsCount: 4,
      status: journeyStatusMode,
      disruptionSummary:
        journeyStatusMode === 'SAFE'
          ? 'All 4 segments operating on schedule'
          : 'Air India AI-202 Delayed +240m → Train 12015-SHT Rebooked to TRN124',
      totalValueInr: 'INR 14,950',
      legs: ['Flight AI-202', 'Train TRN124 (Rebooked)', 'Rambagh Palace Hotel', 'Amber Fort Tour'],
    },
    {
      id: 2,
      title: 'Bengaluru Tech Summit & Mysuru Express Corridor',
      dates: 'Nov 12, 2026 – Nov 14, 2026',
      origin: 'Delhi (DEL)',
      destination: 'Mysuru (MYS)',
      legsCount: 3,
      status: 'SAFE',
      disruptionSummary: '95-minute transfer buffer at KSR Bengaluru — Safe connection',
      totalValueInr: 'INR 11,200',
      legs: ['IndiGo 6E-804', 'Vande Bharat 20608', 'Radisson Blu Mysuru'],
    },
    {
      id: 3,
      title: 'Western Coast Monsoon Corridor (Mumbai → Goa)',
      dates: 'Dec 04, 2026 – Dec 07, 2026',
      origin: 'Mumbai (CSMT)',
      destination: 'Panjim (GOI)',
      legsCount: 3,
      status: 'AT_RISK',
      disruptionSummary: 'Tight 42-minute inter-terminal transfer at Madgaon Junction',
      totalValueInr: 'INR 9,800',
      legs: ['Tejas Express 22119', 'Kadamba Shuttle Bus', 'Taj Cidade de Goa'],
    },
  ];

  const filtered =
    filterStatus === 'ALL' ? portfolio : portfolio.filter((j) => j.status === filterStatus);

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="rounded-3xl border border-white/[0.08] bg-[#070b16]/80 p-6 shadow-glass-card backdrop-blur-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-80 h-80 bg-sky-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
        <div className="relative z-10">
          <h2 className="text-xl font-bold text-white tracking-tight font-display">My Journeys Portfolio</h2>
          <p className="text-xs text-slate-400 mt-1 font-sans">
            Multi-modal itineraries monitored by the Autonomous Disruption Recovery Agent
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 relative z-10">
          {['ALL', 'SAFE', 'AT_RISK', 'DISRUPTED', 'RECOVERY_IN_PROGRESS', 'RECOVERED'].map((st) => (
            <motion.button
              whileTap={{ scale: 0.96 }}
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer font-display ${
                filterStatus === st
                  ? 'bg-sky-600 text-white shadow-[0_0_12px_rgba(56,189,248,0.3)] border border-sky-400/40'
                  : 'bg-[#04060d] text-slate-400 hover:text-slate-200 border border-white/[0.08] hover:border-white/[0.2]'
              }`}
            >
              {st === 'ALL' ? 'All Journeys' : <JourneyStatusBadge status={st} size="sm" />}
            </motion.button>
          ))}
        </div>
      </motion.div>

      {filtered.length === 0 ? (
        <EmptyStateBox
          title="No journeys match the selected status filter"
          description="Switch the filter to 'All Journeys' or forward a new booking confirmation email in the Inbox."
          actionLabel="Show All Journeys"
          onAction={() => setFilterStatus('ALL')}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filtered.map((j, idx) => (
            <motion.div
              key={j.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25, delay: idx * 0.05 }}
              className="rounded-3xl border border-white/[0.08] bg-[#070b16]/80 hover:bg-[#0c1324] hover:border-white/[0.18] p-6 shadow-glass-card hover:shadow-glow-sm transition flex flex-col lg:flex-row lg:items-center justify-between gap-5 group"
            >
              <div className="space-y-2.5">
                <div className="flex flex-wrap items-center gap-2.5">
                  <JourneyStatusBadge status={j.status} />
                  <span className="text-xs font-mono text-slate-400">{j.dates}</span>
                  <span className="text-xs font-mono text-sky-400 bg-sky-950/60 px-2.5 py-0.5 rounded-full border border-sky-500/30">
                    {j.legsCount} Segments
                  </span>
                  <span className="text-xs font-mono text-emerald-400 bg-emerald-950/40 px-2.5 py-0.5 rounded-full border border-emerald-500/30">
                    {j.totalValueInr}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-white font-display group-hover:text-sky-300 transition">{j.title}</h3>
                <p className="text-xs text-slate-300 font-sans">{j.disruptionSummary}</p>
                <div className="flex flex-wrap items-center gap-2 pt-1 font-sans">
                  {j.legs.map((leg, lIdx) => (
                    <React.Fragment key={lIdx}>
                      <span className="px-3 py-1 rounded-xl bg-[#04060d] border border-white/[0.08] text-[11px] text-slate-200 font-medium">
                        {leg}
                      </span>
                      {lIdx < j.legs.length - 1 && (
                        <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>

              <div className="flex sm:flex-row lg:flex-col items-end justify-between gap-2.5 shrink-0">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => onNavigate('journey-details')}
                  className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white text-xs font-bold flex items-center gap-2 cursor-pointer shadow-[0_0_15px_rgba(56,189,248,0.25)] transition font-display"
                >
                  <span>View Journey Details</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => onNavigate('journey-graph')}
                  className="px-4 py-2.5 rounded-xl bg-[#0d1527] hover:bg-[#131f38] text-slate-200 text-xs font-semibold cursor-pointer border border-white/[0.1] hover:border-sky-500/30 transition font-sans"
                >
                  Open NetworkX Graph
                </motion.button>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}

export function JourneyDetailsPage({
  journey,
  journeyStatusMode = 'RECOVERED',
  onChangeJourneyStatusMode,
  onNavigate,
}) {
  // Build the 4 canonical legs: Flight -> Train -> Hotel -> Tour
  const legs = [
    {
      step: 1,
      mode: 'Flight',
      icon: Plane,
      ref: 'AI-202',
      provider: 'Air India',
      route: 'Mumbai (BOM Terminal 2) → New Delhi (DEL Terminal 3)',
      originalSchedule: '10:00 IST → 12:00 IST',
      currentSchedule:
        journeyStatusMode === 'SAFE'
          ? '10:00 IST → 12:00 IST (On Time)'
          : '10:00 IST → 16:00 IST (Delayed +240 mins)',
      price: 'INR 5,400',
      status:
        journeyStatusMode === 'SAFE'
          ? 'SAFE'
          : journeyStatusMode === 'AT_RISK'
          ? 'AT_RISK'
          : 'DISRUPTED',
      connectionNote:
        journeyStatusMode === 'SAFE'
          ? '90 minutes connection time to New Delhi Railway Station (Safe)'
          : 'Arrival at 16:00 violates 13:30 train departure (-150m deficit)',
    },
    {
      step: 2,
      mode: 'Train',
      icon: Train,
      ref: journeyStatusMode === 'RECOVERED' ? 'PNR-TRN124-8821 (TRN124)' : '12015-SHT (TRN123)',
      provider: 'Indian Railways',
      route: 'New Delhi (NDLS) → Jaipur Junction (JP)',
      originalSchedule: '13:30 IST → 17:30 IST (Ajmer Shatabdi 12015)',
      currentSchedule:
        journeyStatusMode === 'RECOVERED'
          ? '17:30 IST → 21:00 IST (Rebooked: Ashram Express 12916 / TRN124)'
          : journeyStatusMode === 'RECOVERY_IN_PROGRESS'
          ? 'Rebooking onto TRN124 (17:30 → 21:00) via OR-Tools...'
          : '13:30 IST → 17:30 IST (Connection Missed)',
      price:
        journeyStatusMode === 'RECOVERED'
          ? 'INR 750 (Original INR 800 refunded INR 600)'
          : 'INR 800',
      status: journeyStatusMode,
      connectionNote:
        journeyStatusMode === 'RECOVERED'
          ? 'Arrives Jaipur at 21:00 — 60 minutes prior to 22:00 hotel check-in cutoff ✓'
          : 'Requires rebooking to arrive before hotel 22:00 latest check-in cutoff',
    },
    {
      step: 3,
      mode: 'Hotel',
      icon: Hotel,
      ref: 'HTL-JAI-101',
      provider: 'Rambagh Heritage Palace Jaipur',
      route: 'Bhawani Singh Rd, Jaipur, Rajasthan',
      originalSchedule: 'Check-In: 18:00 IST (Latest Cutoff: 22:00 IST)',
      currentSchedule:
        journeyStatusMode === 'RECOVERED'
          ? 'Updated Check-In: 21:30 IST (Guaranteed Late Hold Active)'
          : 'Scheduled Check-In: 18:00 IST (Cutoff 22:00 IST)',
      price: 'INR 6,500 / night',
      status:
        journeyStatusMode === 'DISRUPTED'
          ? 'AT_RISK'
          : journeyStatusMode === 'RECOVERED'
          ? 'RECOVERED'
          : journeyStatusMode,
      connectionNote:
        'Overnight stay before next-morning guided heritage tour at 09:00 IST',
    },
    {
      step: 4,
      mode: 'Tour',
      icon: Compass,
      ref: 'TOUR-JAI-AMBER',
      provider: 'Rajasthan Royal Experiences',
      route: 'Amber Fort, Hawa Mahal & City Palace Guided Tour',
      originalSchedule: 'Next Day 09:00 IST → 13:00 IST',
      currentSchedule: 'Next Day 09:00 IST → 13:00 IST (Protected by Overnight Buffer)',
      price: 'INR 2,250',
      status: 'SAFE',
      connectionNote: 'Final segment of journey — no downstream dependencies at risk',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header & Status State Switcher */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="rounded-3xl border border-white/[0.08] bg-[#070b16]/80 p-6 shadow-glass-card backdrop-blur-2xl flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-80 h-80 bg-sky-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
        <div className="space-y-1 relative z-10">
          <div className="flex items-center gap-2.5">
            <span className="text-xs font-mono uppercase text-sky-400 font-bold">
              Connected Multi-Modal Journey Chain
            </span>
            <JourneyStatusBadge status={journeyStatusMode} />
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight font-display">
            Flight &rarr; Train &rarr; Hotel &rarr; Tour
          </h2>
          <p className="text-xs text-slate-400 font-sans">
            End-to-end dependency chain with live status indicators: Safe, At Risk, Disrupted, Recovery in Progress, Recovered
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 relative z-10">
          {['SAFE', 'AT_RISK', 'DISRUPTED', 'RECOVERY_IN_PROGRESS', 'RECOVERED'].map((st) => (
            <motion.button
              whileTap={{ scale: 0.96 }}
              key={st}
              onClick={() => onChangeJourneyStatusMode(st)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer border ${
                journeyStatusMode === st
                  ? 'border-sky-400 bg-sky-950/60 shadow-[0_0_12px_rgba(56,189,248,0.3)]'
                  : 'border-white/[0.08] bg-[#04060d] opacity-75 hover:opacity-100 hover:border-white/[0.2]'
              }`}
            >
              <JourneyStatusBadge status={st} size="sm" />
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* Vertical Connected Journey Pipeline: Flight ↓ Train ↓ Hotel ↓ Tour */}
      <div className="max-w-4xl mx-auto space-y-3">
        {legs.map((leg, idx) => {
          const IconComponent = leg.icon;
          return (
            <React.Fragment key={leg.step}>
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: idx * 0.06 }}
                className="rounded-3xl border border-white/[0.08] bg-[#070b16]/80 p-6 shadow-glass-card hover:border-white/[0.18] transition"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/[0.08] pb-4">
                  <div className="flex items-center gap-3.5">
                    <div className="w-11 h-11 rounded-2xl bg-sky-500/15 border border-sky-500/30 text-sky-400 flex items-center justify-center shrink-0 shadow-[0_0_12px_rgba(56,189,248,0.2)]">
                      <IconComponent className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-extrabold uppercase tracking-wider text-sky-400 font-display">
                          {leg.mode}
                        </span>
                        <span className="text-xs font-mono text-slate-300 bg-[#04060d] px-2.5 py-0.5 rounded-md border border-white/[0.08]">
                          Ref: {leg.ref}
                        </span>
                      </div>
                      <h3 className="text-base font-bold text-white mt-0.5 font-display">
                        {leg.provider} &middot; {leg.route}
                      </h3>
                    </div>
                  </div>
                  <div className="shrink-0">
                    <JourneyStatusBadge status={leg.status} size="lg" />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-4 text-xs">
                  <div className="p-3.5 rounded-2xl bg-[#04060d] border border-white/[0.08]">
                    <span className="text-[10px] font-mono text-slate-500 block mb-1">
                      ORIGINAL SCHEDULE
                    </span>
                    <span className="text-slate-300 font-mono">{leg.originalSchedule}</span>
                  </div>
                  <div className="p-3.5 rounded-2xl bg-[#04060d] border border-white/[0.08]">
                    <span className="text-[10px] font-mono text-slate-500 block mb-1">
                      ACTIVE / RECOVERED SCHEDULE
                    </span>
                    <span className="text-white font-semibold font-mono">{leg.currentSchedule}</span>
                  </div>
                  <div className="p-3.5 rounded-2xl bg-[#04060d] border border-white/[0.08]">
                    <span className="text-[10px] font-mono text-slate-500 block mb-1">
                      FARE &amp; PROTECTION
                    </span>
                    <span className="text-emerald-300 font-mono font-semibold">{leg.price}</span>
                  </div>
                </div>

                <div className="mt-3.5 text-xs text-slate-400 flex items-center justify-between font-sans">
                  <span>{leg.connectionNote}</span>
                  {leg.mode === 'Train' && (
                    <button
                      onClick={() => onNavigate('recovery-plan')}
                      className="text-sky-400 hover:text-sky-300 font-semibold cursor-pointer transition inline-flex items-center gap-1 font-display"
                    >
                      <span>Inspect Recovery Plan</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </motion.div>

              {/* Downward Connector Arrow between Flight -> Train -> Hotel -> Tour */}
              {idx < legs.length - 1 && (
                <div className="flex flex-col items-center py-1">
                  <div className="w-0.5 h-4 bg-white/[0.1]" />
                  <div className="px-3.5 py-1 rounded-full bg-[#070b16] border border-white/[0.1] text-[11px] font-mono text-slate-300 flex items-center gap-2 shadow-sm">
                    <ArrowDown className="w-3.5 h-3.5 text-sky-400" />
                    <span>
                      Downstream Dependency: <strong className="text-white">{leg.mode}</strong> &rarr; <strong className="text-white">{legs[idx + 1].mode}</strong>
                    </span>
                  </div>
                  <div className="w-0.5 h-4 bg-white/[0.1]" />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
