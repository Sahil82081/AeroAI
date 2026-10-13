import React, { useState } from 'react';
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
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white">My Journeys Portfolio</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Multi-modal itineraries monitored by the Autonomous Disruption Recovery Agent
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {['ALL', 'SAFE', 'AT_RISK', 'DISRUPTED', 'RECOVERY_IN_PROGRESS', 'RECOVERED'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer ${
                filterStatus === st
                  ? 'bg-sky-600 text-white'
                  : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {st === 'ALL' ? 'All Journeys' : <JourneyStatusBadge status={st} size="sm" />}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyStateBox
          title="No journeys match the selected status filter"
          description="Switch the filter to 'All Journeys' or forward a new booking confirmation email in the Inbox."
          actionLabel="Show All Journeys"
          onAction={() => setFilterStatus('ALL')}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filtered.map((j) => (
            <div
              key={j.id}
              className="rounded-2xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 p-5 transition flex flex-col lg:flex-row lg:items-center justify-between gap-4"
            >
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2.5">
                  <JourneyStatusBadge status={j.status} />
                  <span className="text-xs font-mono text-slate-400">{j.dates}</span>
                  <span className="text-xs font-mono text-sky-400 bg-sky-950/60 px-2 py-0.5 rounded">
                    {j.legsCount} Segments
                  </span>
                </div>
                <h3 className="text-base font-bold text-white">{j.title}</h3>
                <p className="text-xs text-slate-300">{j.disruptionSummary}</p>
                <div className="flex flex-wrap items-center gap-2 pt-1">
                  {j.legs.map((leg, idx) => (
                    <React.Fragment key={idx}>
                      <span className="px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-200 font-medium">
                        {leg}
                      </span>
                      {idx < j.legs.length - 1 && (
                        <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>

              <div className="flex sm:flex-row lg:flex-col items-end justify-between gap-2 shrink-0">
                <button
                  onClick={() => onNavigate('journey-details')}
                  className="px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold flex items-center gap-1.5 cursor-pointer"
                >
                  <span>View Journey Details</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => onNavigate('journey-graph')}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold cursor-pointer"
                >
                  Open NetworkX Graph
                </button>
              </div>
            </div>
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
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <span className="text-xs font-mono uppercase text-sky-400 font-bold">
              Connected Multi-Modal Journey Chain
            </span>
            <JourneyStatusBadge status={journeyStatusMode} />
          </div>
          <h2 className="text-xl font-bold text-white">
            Flight &rarr; Train &rarr; Hotel &rarr; Tour
          </h2>
          <p className="text-xs text-slate-400">
            End-to-end dependency chain with live status indicators: ✓ Safe, ⚠ At Risk, ❌ Disrupted, 🔄 Recovery in Progress, ✓ Recovered
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {['SAFE', 'AT_RISK', 'DISRUPTED', 'RECOVERY_IN_PROGRESS', 'RECOVERED'].map((st) => (
            <button
              key={st}
              onClick={() => onChangeJourneyStatusMode(st)}
              className={`px-2.5 py-1 rounded-xl text-xs font-semibold transition cursor-pointer border ${
                journeyStatusMode === st
                  ? 'ring-2 ring-sky-400 border-sky-400 bg-slate-800'
                  : 'border-slate-800 bg-slate-950/60 opacity-75 hover:opacity-100'
              }`}
            >
              <JourneyStatusBadge status={st} size="sm" />
            </button>
          ))}
        </div>
      </div>

      {/* Vertical Connected Journey Pipeline: Flight ↓ Train ↓ Hotel ↓ Tour */}
      <div className="max-w-4xl mx-auto space-y-2">
        {legs.map((leg, idx) => {
          const IconComponent = leg.icon;
          return (
            <React.Fragment key={leg.step}>
              <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg hover:border-slate-700 transition">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-sky-500/10 border border-sky-500/30 text-sky-400 flex items-center justify-center shrink-0">
                      <IconComponent className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-extrabold uppercase tracking-wider text-sky-400">
                          {leg.mode}
                        </span>
                        <span className="text-xs font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                          Ref: {leg.ref}
                        </span>
                      </div>
                      <h3 className="text-base font-bold text-white mt-0.5">
                        {leg.provider} &middot; {leg.route}
                      </h3>
                    </div>
                  </div>
                  <div className="shrink-0">
                    <JourneyStatusBadge status={leg.status} size="lg" />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 text-xs">
                  <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/70">
                    <span className="text-[10px] font-mono text-slate-500 block">
                      ORIGINAL SCHEDULE
                    </span>
                    <span className="text-slate-300 font-mono">{leg.originalSchedule}</span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/70">
                    <span className="text-[10px] font-mono text-slate-500 block">
                      ACTIVE / RECOVERED SCHEDULE
                    </span>
                    <span className="text-white font-semibold font-mono">{leg.currentSchedule}</span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/70">
                    <span className="text-[10px] font-mono text-slate-500 block">
                      FARE &amp; PROTECTION
                    </span>
                    <span className="text-emerald-300 font-mono">{leg.price}</span>
                  </div>
                </div>

                <div className="mt-3 text-xs text-slate-400 flex items-center justify-between">
                  <span>{leg.connectionNote}</span>
                  {leg.mode === 'Train' && (
                    <button
                      onClick={() => onNavigate('recovery-plan')}
                      className="text-sky-400 hover:underline font-semibold cursor-pointer"
                    >
                      Inspect Recovery Plan &rarr;
                    </button>
                  )}
                </div>
              </div>

              {/* Downward Connector Arrow between Flight -> Train -> Hotel -> Tour */}
              {idx < legs.length - 1 && (
                <div className="flex flex-col items-center py-1">
                  <div className="w-0.5 h-4 bg-slate-700" />
                  <div className="px-3 py-1 rounded-full bg-slate-900 border border-slate-700 text-[11px] font-mono text-slate-300 flex items-center gap-1.5 shadow">
                    <ArrowDown className="w-3.5 h-3.5 text-sky-400" />
                    <span>
                      Downstream Dependency: {leg.mode} &rarr; {legs[idx + 1].mode}
                    </span>
                  </div>
                  <div className="w-0.5 h-4 bg-slate-700" />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
