import React, { useState, useEffect, useCallback } from 'react';
import {
  Plane,
  Train,
  Hotel,
  Compass,
  Bus,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  Trash2,
  Plus,
  Bot,
} from 'lucide-react';
import { api } from '../../services/api';

const FALLBACK_REAL_CATALOG = {
  FLIGHT: [
    {
      label: 'Air India AI-202 · Mumbai (BOM) → Delhi (DEL) · 10:00–12:00 · ₹5,400',
      booking_type: 'FLIGHT',
      provider_name: 'Air India',
      reference_number: 'AI-202',
      title: 'Air India AI-202 (BOM → DEL)',
      origin: 'Mumbai',
      destination: 'Delhi',
      start_time: '2026-10-20T10:00',
      end_time: '2026-10-20T12:00',
      price: 5400,
    },
    {
      label: 'IndiGo 6E-2142 · Mumbai (BOM) → Delhi (DEL) · 12:15–14:25 · ₹6,200',
      booking_type: 'FLIGHT',
      provider_name: 'IndiGo Airlines',
      reference_number: '6E-2142',
      title: 'IndiGo 6E-2142 (BOM → DEL)',
      origin: 'Mumbai',
      destination: 'Delhi',
      start_time: '2026-10-20T12:15',
      end_time: '2026-10-20T14:25',
      price: 6200,
    },
    {
      label: 'IndiGo 6E-5091 · Delhi (DEL) → Jaipur (JAI) · 17:45–18:45 · ₹3,850',
      booking_type: 'FLIGHT',
      provider_name: 'IndiGo Airlines',
      reference_number: '6E-5091',
      title: 'IndiGo 6E-5091 (DEL → JAI)',
      origin: 'Delhi',
      destination: 'Jaipur',
      start_time: '2026-10-20T17:45',
      end_time: '2026-10-20T18:45',
      price: 3850,
    },
    {
      label: 'IndiGo 6E-5318 · Mumbai (BOM) → Bengaluru (BLR) · 09:30–11:15 · ₹4,850',
      booking_type: 'FLIGHT',
      provider_name: 'IndiGo Airlines',
      reference_number: '6E-5318',
      title: 'IndiGo 6E-5318 (BOM → BLR)',
      origin: 'Mumbai',
      destination: 'Bangalore',
      start_time: '2026-10-20T09:30',
      end_time: '2026-10-20T11:15',
      price: 4850,
    },
  ],
  TRAIN: [
    {
      label: '12015 Ajmer Shatabdi Express · New Delhi (NDLS) → Jaipur (JP) · 13:30–17:30 · ₹800',
      booking_type: 'TRAIN',
      provider_name: 'Indian Railways (IRCTC)',
      reference_number: '12015-SHT',
      title: '12015 Ajmer Shatabdi Express (NDLS → JP)',
      origin: 'Delhi',
      destination: 'Jaipur',
      start_time: '2026-10-20T13:30',
      end_time: '2026-10-20T17:30',
      price: 800,
    },
    {
      label: '20978 Vande Bharat Express · Delhi Cantt (DEC) → Jaipur (JP) · 18:40–22:30 · ₹1,150',
      booking_type: 'TRAIN',
      provider_name: 'Indian Railways (IRCTC)',
      reference_number: '20978-VB',
      title: '20978 Vande Bharat Express (DEC → JP)',
      origin: 'Delhi',
      destination: 'Jaipur',
      start_time: '2026-10-20T18:40',
      end_time: '2026-10-20T22:30',
      price: 1150,
    },
    {
      label: '12986 Jaipur AC Double Decker · Delhi (DEE) → Jaipur (JP) · 17:35–22:05 · ₹680',
      booking_type: 'TRAIN',
      provider_name: 'Indian Railways (IRCTC)',
      reference_number: '12986-DD',
      title: '12986 Jaipur AC Double Decker (DEE → JP)',
      origin: 'Delhi',
      destination: 'Jaipur',
      start_time: '2026-10-20T17:35',
      end_time: '2026-10-20T22:05',
      price: 680,
    },
    {
      label: '12951 Mumbai–New Delhi Tejas Rajdhani · Mumbai (MMCT) → New Delhi (NDLS) · 17:00–08:32 · ₹3,420',
      booking_type: 'TRAIN',
      provider_name: 'Indian Railways (IRCTC)',
      reference_number: '12951-RAJ',
      title: '12951 Tejas Rajdhani Express (MMCT → NDLS)',
      origin: 'Mumbai',
      destination: 'Delhi',
      start_time: '2026-10-20T17:00',
      end_time: '2026-10-21T08:32',
      price: 3420,
    },
    {
      label: '12123 Deccan Queen · Mumbai (CSMT) → Pune (PUNE) · 17:10–20:25 · ₹495',
      booking_type: 'TRAIN',
      provider_name: 'Indian Railways (IRCTC)',
      reference_number: '12123-DQ',
      title: '12123 Deccan Queen Express (CSMT → PUNE)',
      origin: 'Mumbai',
      destination: 'Pune',
      start_time: '2026-10-20T17:10',
      end_time: '2026-10-20T20:25',
      price: 495,
    },
    {
      label: '12005 Kalka Shatabdi · New Delhi (NDLS) → Chandigarh (CDG) · 17:15–20:30 · ₹785',
      booking_type: 'TRAIN',
      provider_name: 'Indian Railways (IRCTC)',
      reference_number: '12005-SHT',
      title: '12005 Kalka Shatabdi Express (NDLS → CDG)',
      origin: 'Delhi',
      destination: 'Chandigarh',
      start_time: '2026-10-20T17:15',
      end_time: '2026-10-20T20:30',
      price: 785,
    },
  ],
  BUS: [
    {
      label: 'RSRTC Gold Line Volvo AC · Delhi ISBT → Jaipur Sindhi Camp · 17:00–22:15 · ₹750',
      booking_type: 'BUS',
      provider_name: 'RSRTC Gold Line Volvo',
      reference_number: 'RJ-14-PA-8821',
      title: 'RSRTC Gold Line Volvo AC (DEL → JAI)',
      origin: 'Delhi',
      destination: 'Jaipur',
      start_time: '2026-10-20T17:00',
      end_time: '2026-10-20T22:15',
      price: 750,
    },
    {
      label: 'Zingbus Electric AC Sleeper · Delhi Dhaula Kuan → Jaipur · 18:30–23:30 · ₹650',
      booking_type: 'BUS',
      provider_name: 'Zingbus Electric',
      reference_number: 'ZB-DL-JP-409',
      title: 'Zingbus Electric AC Sleeper (DEL → JAI)',
      origin: 'Delhi',
      destination: 'Jaipur',
      start_time: '2026-10-20T18:30',
      end_time: '2026-10-20T23:30',
      price: 650,
    },
    {
      label: 'MSRTC Shivneri Volvo AC · Mumbai Dadar → Pune Station · 14:00–17:30 · ₹560',
      booking_type: 'BUS',
      provider_name: 'MSRTC Shivneri Volvo',
      reference_number: 'MH-12-SH-402',
      title: 'MSRTC Shivneri Volvo AC (Mumbai → Pune)',
      origin: 'Mumbai',
      destination: 'Pune',
      start_time: '2026-10-20T14:00',
      end_time: '2026-10-20T17:30',
      price: 560,
    },
  ],
  HOTEL: [
    {
      label: 'Rambagh Palace, Jaipur (Taj) · Check-in 18:00 · ₹6,500/night',
      booking_type: 'HOTEL',
      provider_name: 'Rambagh Palace Jaipur',
      reference_number: 'HTL-JAI-101',
      title: 'Rambagh Palace Jaipur',
      origin: 'Jaipur',
      destination: 'Jaipur',
      start_time: '2026-10-20T18:00',
      end_time: '2026-10-21T11:00',
      price: 6500,
    },
    {
      label: 'ITC Rajputana, A Luxury Collection Hotel · Jaipur · Check-in 15:00 · ₹8,500/night',
      booking_type: 'HOTEL',
      provider_name: 'ITC Rajputana Jaipur',
      reference_number: 'ITC-JAI-204',
      title: 'ITC Rajputana Jaipur',
      origin: 'Jaipur',
      destination: 'Jaipur',
      start_time: '2026-10-20T15:00',
      end_time: '2026-10-21T12:00',
      price: 8500,
    },
    {
      label: 'Pullman New Delhi Aerocity · IGI Airport · Check-in 14:00 · ₹9,200/night',
      booking_type: 'HOTEL',
      provider_name: 'Pullman New Delhi Aerocity',
      reference_number: 'PUL-DEL-309',
      title: 'Pullman New Delhi Aerocity',
      origin: 'Delhi',
      destination: 'Delhi',
      start_time: '2026-10-20T14:00',
      end_time: '2026-10-21T12:00',
      price: 9200,
    },
    {
      label: 'JW Marriott Hotel Pune · Senapati Bapat Rd · Check-in 18:00 · ₹7,800/night',
      booking_type: 'HOTEL',
      provider_name: 'JW Marriott Pune',
      reference_number: 'JWM-PUN-112',
      title: 'JW Marriott Hotel Pune',
      origin: 'Pune',
      destination: 'Pune',
      start_time: '2026-10-20T18:00',
      end_time: '2026-10-21T11:00',
      price: 7800,
    },
  ],
  ACTIVITY: [
    {
      label: 'Amber Fort & Nahargarh Heritage Tour · Jaipur · Next Day 09:00–13:00 · ₹2,250',
      booking_type: 'ACTIVITY',
      provider_name: 'Rajasthan Tourism (RTDC)',
      reference_number: 'TOUR-JAI-01',
      title: 'Amber Fort Morning Tour',
      origin: 'Jaipur',
      destination: 'Jaipur',
      start_time: '2026-10-21T09:00',
      end_time: '2026-10-21T13:00',
      price: 2250,
    },
    {
      label: 'Shaniwar Wada & Old Pune Heritage Walk · Pune · Next Day 09:00–12:00 · ₹1,200',
      booking_type: 'ACTIVITY',
      provider_name: 'Maharashtra Tourism (MTDC)',
      reference_number: 'TOUR-PUN-02',
      title: 'Shaniwar Wada Heritage Walk',
      origin: 'Pune',
      destination: 'Pune',
      start_time: '2026-10-21T09:00',
      end_time: '2026-10-21T12:00',
      price: 1200,
    },
  ],
};

export function SimpleGuidedStoryMode({ onRunBackendE2E, onSync, onOpenAdvancedPage }) {
  const [workspace, setWorkspace] = useState(null);
  const [catalog, setCatalog] = useState(FALLBACK_REAL_CATALOG);
  const [busy, setBusy] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [impactResult, setImpactResult] = useState(null);
  const [recoveryResult, setRecoveryResult] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [delayMinutes, setDelayMinutes] = useState(240);

  const [form, setForm] = useState({
    booking_type: 'FLIGHT',
    provider_name: 'Air India',
    reference_number: 'AI-202',
    title: 'Air India AI-202 (BOM → DEL)',
    origin: 'Mumbai',
    destination: 'Delhi',
    start_time: '2026-10-20T10:00',
    end_time: '2026-10-20T12:00',
    price: 5400,
  });

  const fetchLiveWorkspace = useCallback(async () => {
    try {
      const data = await api.getLiveWorkspace();
      setWorkspace(data);
      setErrorMsg(null);
    } catch (err) {
      setErrorMsg(err?.response?.data?.detail || err?.message || 'Could not reach backend API on port 8000');
    }
  }, []);

  useEffect(() => {
    fetchLiveWorkspace();
    api
      .getRealTransportCatalog()
      .then((res) => {
        if (res?.catalog) setCatalog(res.catalog);
      })
      .catch(() => {
        // use built-in real Indian catalog fallback
      });
  }, [fetchLiveWorkspace]);

  const handleSelectType = (newType) => {
    const firstPreset = (catalog[newType] || FALLBACK_REAL_CATALOG[newType] || [])[0];
    if (firstPreset) {
      setForm({
        booking_type: newType,
        provider_name: firstPreset.provider_name,
        reference_number: firstPreset.reference_number,
        title: firstPreset.title,
        origin: firstPreset.origin,
        destination: firstPreset.destination,
        start_time: firstPreset.start_time.slice(0, 16),
        end_time: firstPreset.end_time.slice(0, 16),
        price: firstPreset.price,
      });
    } else {
      setForm({ ...form, booking_type: newType });
    }
  };

  const handleSelectRealSchedule = (idxStr) => {
    const list = catalog[form.booking_type] || FALLBACK_REAL_CATALOG[form.booking_type] || [];
    const preset = list[Number(idxStr)];
    if (!preset) return;
    setForm({
      booking_type: preset.booking_type,
      provider_name: preset.provider_name,
      reference_number: preset.reference_number,
      title: preset.title,
      origin: preset.origin,
      destination: preset.destination,
      start_time: preset.start_time.slice(0, 16),
      end_time: preset.end_time.slice(0, 16),
      price: preset.price,
    });
  };

  const handleClearTrip = async () => {
    setBusy(true);
    setErrorMsg(null);
    try {
      const data = await api.clearLiveWorkspace();
      setWorkspace(data);
      setImpactResult(null);
      setRecoveryResult(null);
      if (onSync) onSync();
    } catch (err) {
      setErrorMsg(err?.response?.data?.detail || err?.message || 'Failed to clear trip');
    } finally {
      setBusy(false);
    }
  };

  const handleLoadSampleTrip = async () => {
    setBusy(true);
    setErrorMsg(null);
    try {
      await api.clearLiveWorkspace();
      const legs = [
        {
          booking_type: 'FLIGHT',
          provider_name: 'Air India',
          reference_number: 'AI-202',
          title: 'Air India AI-202 (BOM → DEL)',
          origin: 'Mumbai',
          destination: 'Delhi',
          start_time: '2026-10-20T10:00:00',
          end_time: '2026-10-20T12:00:00',
          price: 5400,
        },
        {
          booking_type: 'TRAIN',
          provider_name: 'Indian Railways (IRCTC)',
          reference_number: '12015-SHT',
          title: '12015 Ajmer Shatabdi Express (NDLS → JP)',
          origin: 'Delhi',
          destination: 'Jaipur',
          start_time: '2026-10-20T13:30:00',
          end_time: '2026-10-20T17:30:00',
          price: 800,
        },
        {
          booking_type: 'HOTEL',
          provider_name: 'Rambagh Palace Jaipur',
          reference_number: 'HTL-JAI-101',
          title: 'Rambagh Palace Jaipur',
          origin: 'Jaipur',
          destination: 'Jaipur',
          start_time: '2026-10-20T18:00:00',
          end_time: '2026-10-21T11:00:00',
          price: 6500,
        },
        {
          booking_type: 'ACTIVITY',
          provider_name: 'Rajasthan Tourism (RTDC)',
          reference_number: 'TOUR-JAI-01',
          title: 'Amber Fort Morning Tour',
          origin: 'Jaipur',
          destination: 'Jaipur',
          start_time: '2026-10-21T09:00:00',
          end_time: '2026-10-21T13:00:00',
          price: 2250,
        },
      ];

      let latest = null;
      for (const leg of legs) {
        latest = await api.addLiveBooking(leg);
      }
      if (latest) {
        setWorkspace(latest);
        setImpactResult(null);
        setRecoveryResult(null);
        setShowAddModal(false);
        if (onSync) onSync();
      }
    } catch (err) {
      setErrorMsg(err?.response?.data?.detail || err?.message || 'Failed to load sample trip');
    } finally {
      setBusy(false);
    }
  };

  const handleAddBooking = async (e) => {
    e.preventDefault();
    setBusy(true);
    setErrorMsg(null);
    try {
      const payload = {
        ...form,
        title: form.title || `${form.provider_name} ${form.reference_number} (${form.origin} → ${form.destination})`,
        start_time: form.start_time.length === 16 ? `${form.start_time}:00` : form.start_time,
        end_time: form.end_time.length === 16 ? `${form.end_time}:00` : form.end_time,
        price: Number(form.price) || 0,
      };
      const data = await api.addLiveBooking(payload);
      setWorkspace(data);
      setShowAddModal(false);
      if (onSync) onSync();
    } catch (err) {
      setErrorMsg(err?.response?.data?.detail || err?.message || 'Failed to save booking');
    } finally {
      setBusy(false);
    }
  };

  const handleDeleteBooking = async (bookingId) => {
    setBusy(true);
    setErrorMsg(null);
    try {
      const data = await api.deleteLiveBooking(bookingId);
      setWorkspace(data);
      if (onSync) onSync();
    } catch (err) {
      setErrorMsg(err?.response?.data?.detail || err?.message || 'Failed to delete booking');
    } finally {
      setBusy(false);
    }
  };

  const handleSimulateDelay = async (bookingId) => {
    if (!bookingId) return;
    setBusy(true);
    setErrorMsg(null);
    try {
      const impact = await api.simulateDemoDisruption({
        booking_id: bookingId,
        type: 'flight_delay',
        delay_minutes: Number(delayMinutes) || 240,
      });
      setImpactResult(impact);
      setRecoveryResult(null);
      await fetchLiveWorkspace();
      if (onSync) onSync();
    } catch (err) {
      setErrorMsg(err?.response?.data?.detail || err?.message || 'Failed to simulate delay');
    } finally {
      setBusy(false);
    }
  };

  const handleAutoRecover = async () => {
    setBusy(true);
    setErrorMsg(null);
    try {
      const data = await api.recoverLiveWorkspace();
      setWorkspace(data);
      setImpactResult(null);
      setRecoveryResult({
        optimization: data.optimization_result,
        execution: data.execution_summary,
        details: data.recovery_details,
      });
      if (onRunBackendE2E) onRunBackendE2E();
    } catch (err) {
      setErrorMsg(err?.response?.data?.detail || err?.message || 'Failed to auto-recover trip');
    } finally {
      setBusy(false);
    }
  };

  const bookings = workspace?.bookings || [];
  const edges = workspace?.graph?.edges || [];
  const hasBrokenConnection =
    (workspace?.graph?.risk_summary?.impossible_connections || 0) > 0 || Boolean(impactResult);

  const getIcon = (type) => {
    switch ((type || '').toUpperCase()) {
      case 'FLIGHT':
        return <Plane className="w-5 h-5 text-sky-400" />;
      case 'TRAIN':
        return <Train className="w-5 h-5 text-indigo-400" />;
      case 'BUS':
        return <Bus className="w-5 h-5 text-emerald-400" />;
      case 'HOTEL':
        return <Hotel className="w-5 h-5 text-amber-400" />;
      default:
        return <Compass className="w-5 h-5 text-teal-400" />;
    }
  };

  const formatDateTime = (iso) => {
    if (!iso) return '';
    return iso.replace('T', ' ').slice(0, 16);
  };

  const activeCatalogOptions =
    catalog[form.booking_type] || FALLBACK_REAL_CATALOG[form.booking_type] || [];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Clean Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <div>
          <h1 className="text-xl font-bold text-white">My Connected Journey</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Add real Indian flights, IRCTC trains, Volvo buses, and hotels — then test delay recovery.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setShowAddModal(!showAddModal)}
            className="px-3.5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold flex items-center gap-1.5 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Add Booking</span>
          </button>

          <button
            type="button"
            onClick={handleLoadSampleTrip}
            disabled={busy}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 border border-slate-700 text-xs font-semibold cursor-pointer"
          >
            {busy ? 'Working...' : 'Load Mumbai → Delhi → Jaipur Trip'}
          </button>

          {onOpenAdvancedPage && (
            <button
              type="button"
              onClick={() => onOpenAdvancedPage('chatbot')}
              className="px-3.5 py-2 rounded-xl bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-200 border border-indigo-500/40 text-xs font-semibold flex items-center gap-1.5 cursor-pointer transition shadow-sm"
              title="Open Passenger Rights & Airline Policy AI Chatbot"
            >
              <Bot className="w-4 h-4 text-indigo-400" />
              <span>Ask Passenger Rights AI</span>
            </button>
          )}

          {bookings.length > 0 && (
            <button
              type="button"
              onClick={handleClearTrip}
              disabled={busy}
              className="px-3 py-2 rounded-xl bg-slate-900 hover:bg-rose-950/50 disabled:opacity-50 text-slate-400 hover:text-rose-300 border border-slate-800 text-xs font-semibold flex items-center gap-1 cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear</span>
            </button>
          )}
        </div>
      </div>

      {/* Error Message Banner */}
      {errorMsg && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-950/30 px-4 py-3 text-xs text-rose-200 flex items-center justify-between">
          <span>{errorMsg}</span>
          <button
            type="button"
            onClick={() => setErrorMsg(null)}
            className="text-rose-300 hover:text-white font-bold ml-4 cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Add Booking Form with Real Indian Transport Schedule Selector */}
      {showAddModal && (
        <form
          onSubmit={handleAddBooking}
          className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4"
        >
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white">
              Add Booking (Select Real IRCTC / Airline / Bus / Hotel Timetable)
            </h3>
            <button
              type="button"
              onClick={() => setShowAddModal(false)}
              className="text-xs text-slate-400 hover:text-white cursor-pointer"
            >
              Cancel
            </button>
          </div>

          {/* 1-Click Real Timetable Selector */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3.5 rounded-xl bg-slate-950/80 border border-sky-500/30">
            <div>
              <label className="block text-[11px] font-semibold text-sky-400 mb-1">
                1. Choose Mode
              </label>
              <select
                value={form.booking_type}
                onChange={(e) => handleSelectType(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white font-semibold"
              >
                <option value="FLIGHT">✈️ Flight (Air India / IndiGo)</option>
                <option value="TRAIN">🚆 Train (IRCTC Shatabdi / Vande Bharat / Rajdhani)</option>
                <option value="BUS">🚌 Bus (RSRTC / MSRTC Shivneri / Zingbus)</option>
                <option value="HOTEL">🏨 Hotel (Taj / ITC / Marriott / Pullman)</option>
                <option value="ACTIVITY">🧭 Tour / Activity (RTDC / MTDC)</option>
              </select>
            </div>

            <div className="sm:col-span-2">
              <label className="block text-[11px] font-semibold text-sky-400 mb-1">
                2. Select Real Schedule to Auto-Fill
              </label>
              <select
                onChange={(e) => handleSelectRealSchedule(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white"
              >
                {activeCatalogOptions.map((item, idx) => (
                  <option key={item.reference_number + idx} value={idx}>
                    {item.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <label className="block text-[11px] text-slate-400 mb-1">Operator / Provider</label>
              <input
                type="text"
                required
                value={form.provider_name}
                onChange={(e) => setForm({ ...form, provider_name: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
              />
            </div>
            <div>
              <label className="block text-[11px] text-slate-400 mb-1">Train / Flight / PNR No.</label>
              <input
                type="text"
                required
                value={form.reference_number}
                onChange={(e) => setForm({ ...form, reference_number: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white font-mono"
              />
            </div>
            <div>
              <label className="block text-[11px] text-slate-400 mb-1">From City</label>
              <input
                type="text"
                required
                value={form.origin}
                onChange={(e) => setForm({ ...form, origin: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
              />
            </div>
            <div>
              <label className="block text-[11px] text-slate-400 mb-1">To City</label>
              <input
                type="text"
                required
                value={form.destination}
                onChange={(e) => setForm({ ...form, destination: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
              />
            </div>
            <div>
              <label className="block text-[11px] text-slate-400 mb-1">Departure / Check-in</label>
              <input
                type="datetime-local"
                required
                value={form.start_time}
                onChange={(e) => setForm({ ...form, start_time: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white font-mono"
              />
            </div>
            <div>
              <label className="block text-[11px] text-slate-400 mb-1">Arrival / Check-out</label>
              <input
                type="datetime-local"
                required
                value={form.end_time}
                onChange={(e) => setForm({ ...form, end_time: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white font-mono"
              />
            </div>
            <div>
              <label className="block text-[11px] text-slate-400 mb-1">Fare (INR)</label>
              <input
                type="number"
                required
                value={form.price}
                onChange={(e) => setForm({ ...form, price: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
              />
            </div>
            <div className="flex items-end justify-end">
              <button
                type="submit"
                disabled={busy}
                className="w-full px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-xs font-bold cursor-pointer"
              >
                {busy ? 'Saving...' : 'Save Booking to Trip'}
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Alert Banner When Disruption Breaks a Connection */}
      {hasBrokenConnection && (
        <div className="rounded-2xl border border-rose-500/50 bg-rose-950/25 p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="text-sm font-bold text-rose-200 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>Disruption Detected — Downstream Connection Missed!</span>
            </div>
            <p className="text-xs text-slate-200 leading-relaxed">
              {impactResult?.explanation ||
                'A delay caused an impossible connection in your itinerary. Click below to find and book the best replacement automatically.'}
            </p>
          </div>

          <button
            type="button"
            onClick={handleAutoRecover}
            disabled={busy}
            className="px-5 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-bold flex items-center gap-2 shadow-lg shrink-0 cursor-pointer"
          >
            <Sparkles className="w-4 h-4" />
            <span>{busy ? 'Rebooking...' : 'Auto-Recover Trip with AI'}</span>
          </button>
        </div>
      )}

      {/* Success Banner After AI Recovery */}
      {recoveryResult && (
        <div className="rounded-2xl border border-emerald-500/40 bg-emerald-950/20 p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="text-sm font-bold text-emerald-300 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Trip Recovered Automatically by AI!</span>
            </div>
            {recoveryResult.optimization?.selected_option && (
              <span className="px-2.5 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-[11px] font-bold text-emerald-200">
                Selected: {recoveryResult.optimization.selected_option.name} (₹{recoveryResult.optimization.selected_option.price})
              </span>
            )}
          </div>

          <p className="text-xs text-slate-200 leading-relaxed">
            {recoveryResult.optimization?.explanation}
          </p>

          {/* 3 Simple Columns to Explain in an Interview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
            <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1.5">
              <div className="text-[11px] font-bold uppercase text-sky-400">
                1. OR-Tools Math Decision
              </div>
              <div className="space-y-1 text-xs text-slate-300">
                {(recoveryResult.optimization?.evaluated_alternatives || []).map((alt) => (
                  <div key={alt.transport_id} className="flex items-center justify-between gap-2">
                    <span className="truncate">{alt.name}</span>
                    <span
                      className={`font-mono text-[10px] px-1.5 py-0.5 rounded shrink-0 ${
                        alt.selected
                          ? 'bg-emerald-500/20 text-emerald-300 font-bold'
                          : alt.feasible
                          ? 'bg-slate-800 text-slate-300'
                          : 'bg-rose-500/15 text-rose-300'
                      }`}
                    >
                      {alt.selected ? '✓ WINNER' : alt.feasible ? `Score ${alt.Weighted_Score ?? ''}` : 'Pruned'}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1.5">
              <div className="text-[11px] font-bold uppercase text-emerald-400">
                2. Real Actions Executed
              </div>
              <ul className="space-y-1 text-xs text-slate-300">
                <li>
                  ✓ Cancelled: {recoveryResult.details?.cancelled_booking || 'Missed connection'}
                </li>
                <li>
                  ✓ Booked: {recoveryResult.details?.rebooked_booking || recoveryResult.optimization?.selected_option?.name}
                </li>
                <li>
                  ✓ Refund Claimed: ₹{recoveryResult.details?.refund_amount_inr ?? 600} (75% waiver)
                </li>
                <li>
                  ✓ Hotel: {recoveryResult.details?.hotel_updated || 'Check-in time updated'}
                </li>
              </ul>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1.5">
              <div className="text-[11px] font-bold uppercase text-amber-400">
                3. Notifications Sent ({(workspace?.notifications || []).length})
              </div>
              <div className="space-y-1 text-xs text-slate-300">
                {(workspace?.notifications || []).slice(0, 4).map((n, i) => (
                  <div key={i} className="truncate text-[11px]">
                    &bull; <span className="text-slate-400">{n.category}:</span> {n.recipient}
                  </div>
                ))}
                {(workspace?.notifications || []).length > 4 && (
                  <div className="text-[11px] text-slate-400">
                    + {(workspace?.notifications || []).length - 4} more in &ldquo;Sent Emails &amp; Logs&rdquo; tab
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bookings List */}
      {bookings.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/40 p-12 text-center space-y-4">
          <div className="text-base font-bold text-slate-200">Your itinerary is empty</div>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Click <strong>+ Add Booking</strong> to select real Air India / IndiGo flights, IRCTC trains (Shatabdi, Vande Bharat, Rajdhani, Deccan Queen), Volvo buses, and Taj/ITC/Marriott hotels — or load the Mumbai &rarr; Delhi &rarr; Jaipur trip below.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              onClick={() => setShowAddModal(true)}
              className="px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold cursor-pointer"
            >
              + Add Real Flight / Train / Bus / Hotel
            </button>
            <button
              type="button"
              onClick={handleLoadSampleTrip}
              disabled={busy}
              className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 border border-slate-700 text-xs font-bold cursor-pointer"
            >
              {busy ? 'Loading...' : 'Load Mumbai → Delhi → Jaipur Trip'}
            </button>
            {onOpenAdvancedPage && (
              <button
                type="button"
                onClick={() => onOpenAdvancedPage('chatbot')}
                className="px-5 py-2.5 rounded-xl bg-indigo-950/60 hover:bg-indigo-900/80 text-indigo-200 border border-indigo-700/60 text-xs font-bold flex items-center gap-2 cursor-pointer"
              >
                <Bot className="w-4 h-4 text-indigo-400" />
                <span>Ask Policy Chatbot</span>
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          {bookings.map((b, idx) => {
            const edge = edges[idx] || null;
            return (
              <React.Fragment key={b.id}>
                <div
                  className={`p-4 rounded-2xl border flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                    b.status === 'DELAYED' || b.status === 'CANCELLED'
                      ? 'border-rose-500/50 bg-rose-950/15'
                      : 'border-slate-800 bg-slate-900/80'
                  }`}
                >
                  <div className="flex items-center gap-3.5">
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                      {getIcon(b.booking_type)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-white">{b.title}</span>
                        <span className="text-xs font-mono text-slate-400">({b.reference_number})</span>
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            b.status === 'CONFIRMED'
                              ? 'bg-emerald-500/20 text-emerald-300'
                              : 'bg-rose-500/25 text-rose-300'
                          }`}
                        >
                          {b.status}
                        </span>
                      </div>
                      <div className="text-xs text-slate-300 mt-1 flex flex-wrap items-center gap-2">
                        <span>
                          {b.origin} &rarr; {b.destination}
                        </span>
                        <span className="text-slate-600">&bull;</span>
                        <span className="font-mono">
                          {formatDateTime(b.start_time)} &rarr; {formatDateTime(b.end_time)}
                        </span>
                        <span className="text-slate-600">&bull;</span>
                        <span className="font-mono">₹{b.price}</span>
                      </div>
                    </div>
                  </div>

                  {/* Action Controls on Transport Cards */}
                  <div className="flex items-center gap-2 shrink-0">
                    {idx === 0 && b.status === 'CONFIRMED' && (
                      <div className="flex items-center gap-1.5">
                        <select
                          value={delayMinutes}
                          onChange={(e) => setDelayMinutes(Number(e.target.value))}
                          className="px-2.5 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200"
                        >
                          <option value={60}>+1 hr delay</option>
                          <option value={120}>+2 hr delay</option>
                          <option value={240}>+4 hr delay</option>
                        </select>
                        <button
                          type="button"
                          onClick={() => handleSimulateDelay(b.id)}
                          disabled={busy}
                          className="px-3 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-xs font-bold cursor-pointer"
                        >
                          Simulate Delay
                        </button>
                      </div>
                    )}

                    <button
                      type="button"
                      onClick={() => handleDeleteBooking(b.id)}
                      disabled={busy}
                      className="p-2 rounded-xl text-slate-500 hover:text-rose-300 hover:bg-slate-800 cursor-pointer"
                      title="Remove booking"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Simple Connection Indicator Between Bookings */}
                {edge && (
                  <div className="pl-7 flex items-center gap-2.5 py-0.5">
                    <div className="w-0.5 h-5 bg-slate-700" />
                    <span
                      className={`text-xs font-medium px-2.5 py-0.5 rounded-lg ${
                        edge.risk_level === 'IMPOSSIBLE'
                          ? 'bg-rose-500/20 text-rose-300 font-bold'
                          : edge.risk_level === 'TIGHT'
                          ? 'bg-amber-500/20 text-amber-300'
                          : 'bg-slate-800/80 text-slate-400'
                      }`}
                    >
                      {edge.risk_level === 'IMPOSSIBLE'
                        ? `❌ Missed Connection (${edge.buffer_minutes}m gap)`
                        : `✓ ${edge.buffer_minutes}m connection time`}
                    </span>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      )}
    </div>
  );
}
