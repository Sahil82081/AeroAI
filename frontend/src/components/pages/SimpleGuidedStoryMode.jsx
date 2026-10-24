import React, { useState, useEffect, useCallback } from 'react';
import {
  Plane,
  Train,
  Hotel,
  Compass,
  Bus,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RotateCcw,
  Sliders,
  Eye,
  HelpCircle,
  Sparkles,
  Trash2,
  Plus,
  Bot,
} from 'lucide-react';
import { api } from '../../services/api';
import { RejectionDialog } from '../RejectionDialog';

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
  const [proposedPlan, setProposedPlan] = useState(null);
  const [executingPlan, setExecutingPlan] = useState(false);
  const [executionPhase, setExecutionPhase] = useState('IDLE');
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [revisingPlan, setRevisingPlan] = useState(false);
  const [showManualModal, setShowManualModal] = useState(false);
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
      if (data?.proposed_plan) {
        setProposedPlan(data.proposed_plan);
      }
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
      setProposedPlan(null);
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
      setProposedPlan(null);
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
      setProposedPlan(data.proposed_plan);
      setRecoveryResult(null);
    } catch (err) {
      setErrorMsg(err?.response?.data?.detail || err?.message || 'Failed to generate recovery plan');
    } finally {
      setBusy(false);
    }
  };

  const handleApproveAndExecute = async () => {
    setExecutingPlan(true);
    setExecutionPhase('APPROVED');
    setErrorMsg(null);
    try {
      setTimeout(() => setExecutionPhase('EXECUTING'), 350);
      const data = await api.approveAndExecuteLiveWorkspaceRecovery();
      setExecutionPhase('COMPLETED');
      setWorkspace(data);
      setProposedPlan(null);
      setRecoveryResult({
        optimization: data.optimization_result,
        execution: data.execution_summary,
        details: data.recovery_details,
      });
      if (onRunBackendE2E) onRunBackendE2E();
    } catch (err) {
      setErrorMsg(err?.response?.data?.detail || err?.message || 'Failed to execute approved recovery plan');
      setExecutionPhase('IDLE');
    } finally {
      setExecutingPlan(false);
    }
  };

  const handleOpenRejectDialog = () => {
    setShowRejectModal(true);
  };

  const handleConfirmRejectAndReplan = async ({ reasons, feedbackText }) => {
    setRevisingPlan(true);
    setErrorMsg(null);
    try {
      const data = await api.rejectAndReplanLiveWorkspaceRecovery({
        reasons,
        feedback_text: feedbackText,
      });
      setWorkspace(data);
      if (data?.proposed_plan) {
        setProposedPlan(data.proposed_plan);
        if (
          data.proposed_plan.status === 'REVISION_REQUIRED' ||
          data.proposed_plan.is_feasible === false
        ) {
          setErrorMsg(
            data.proposed_plan.summary ||
            'No suitable automated recovery plan could be found with the current requirements.'
          );
        }
      }
      setShowRejectModal(false);
    } catch (err) {
      setErrorMsg(err?.response?.data?.detail || err?.message || 'Failed to generate revised recovery plan');
    } finally {
      setRevisingPlan(false);
    }
  };

  const handleResetConstraintsAndReplan = async () => {
    setBusy(true);
    setErrorMsg(null);
    try {
      const data = await api.recoverLiveWorkspace();
      setWorkspace(data);
      setProposedPlan(data.proposed_plan);
      setRecoveryResult(null);
    } catch (err) {
      setErrorMsg(err?.response?.data?.detail || err?.message || 'Failed to restart recovery planning');
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
    <div className="max-w-4xl mx-auto space-y-3.5">
      {/* Clean Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-surface-container-low/90 backdrop-blur-2xl border border-surface-container-high rounded-xl p-3.5 sm:p-4 shadow-glass-card relative overflow-hidden">
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-sky-400/30 to-transparent pointer-events-none" />
        <div>
          <h1 className="text-lg sm:text-xl font-extrabold text-white font-display tracking-tight">
            My Connected Journey
          </h1>
          <p className="text-xs text-on-surface-variant mt-0.5 font-sans">
            Add real Indian flights, IRCTC trains, Volvo buses, and hotels — then test autonomous delay recovery.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setShowAddModal(!showAddModal)}
            className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-primary-container to-primary-fixed-dim text-on-primary hover:brightness-110 active:scale-[0.98] text-xs font-bold flex items-center gap-1.5 transition shadow-[0_0_12px_rgba(0,229,255,0.25)] cursor-pointer font-display h-8"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Booking</span>
          </button>

          <button
            type="button"
            onClick={handleLoadSampleTrip}
            disabled={busy}
            className="px-3 py-1.5 rounded-lg bg-surface-container-lowest hover:bg-white/[0.05] disabled:opacity-50 text-slate-200 border border-surface-container-high hover:border-white/20 text-xs font-semibold cursor-pointer transition font-display h-8"
          >
            {busy ? 'Working...' : 'Load Golden Triangle Trip'}
          </button>

          {onOpenAdvancedPage && (
            <button
              type="button"
              onClick={() => onOpenAdvancedPage('chatbot')}
              className="px-3 py-1.5 rounded-lg bg-indigo-500/15 hover:bg-indigo-500/25 text-indigo-200 border border-indigo-400/30 text-xs font-semibold flex items-center gap-1.5 cursor-pointer transition shadow-[0_0_10px_rgba(99,102,241,0.15)] font-display h-8"
              title="Open Passenger Rights & Airline Policy AI Chatbot"
            >
              <Bot className="w-3.5 h-3.5 text-indigo-400" />
              <span>Ask Policy AI</span>
            </button>
          )}

          {bookings.length > 0 && (
            <button
              type="button"
              onClick={handleClearTrip}
              disabled={busy}
              className="px-2.5 py-1.5 rounded-lg bg-surface-container-lowest hover:bg-rose-950/40 disabled:opacity-50 text-on-surface-variant hover:text-rose-300 border border-surface-container-high hover:border-rose-500/30 text-xs font-semibold flex items-center gap-1 cursor-pointer transition font-mono h-8"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear</span>
            </button>
          )}
        </div>
      </div>

      {/* Error Message Banner */}
      {errorMsg && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-950/30 px-4 py-2 text-xs text-rose-200 flex items-center justify-between backdrop-blur-xl shadow-[0_0_12px_rgba(244,63,94,0.12)]">
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
          className="bg-surface-container-low/90 border border-surface-container-high rounded-xl p-3.5 sm:p-4 space-y-3 shadow-glass-card backdrop-blur-2xl"
        >
          <div className="flex items-center justify-between">
            <h3 className="text-xs sm:text-sm font-bold text-white font-display">
              Add Booking (Select Real IRCTC / Airline / Bus / Hotel Timetable)
            </h3>
            <button
              type="button"
              onClick={() => setShowAddModal(false)}
              className="text-xs text-on-surface-variant hover:text-white cursor-pointer font-mono"
            >
              Cancel
            </button>
          </div>

          {/* 1-Click Real Timetable Selector */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 p-3 rounded-xl bg-surface-container-lowest border border-sky-400/30 shadow-[0_0_12px_rgba(56,189,248,0.08)]">
            <div>
              <label className="block text-[11px] font-semibold text-sky-400 mb-1 font-mono">
                1. Choose Mode
              </label>
              <select
                value={form.booking_type}
                onChange={(e) => handleSelectType(e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg bg-surface-container-low border border-surface-container-high text-xs text-white font-semibold focus:outline-none focus:border-sky-400 h-8"
              >
                <option value="FLIGHT">✈️ Flight (Air India / IndiGo)</option>
                <option value="TRAIN">🚆 Train (IRCTC Shatabdi / Vande Bharat / Rajdhani)</option>
                <option value="BUS">🚌 Bus (RSRTC / MSRTC Shivneri / Zingbus)</option>
                <option value="HOTEL">🏨 Hotel (Taj / ITC / Marriott / Pullman)</option>
                <option value="ACTIVITY">🧭 Tour / Activity (RTDC / MTDC)</option>
              </select>
            </div>

            <div className="sm:col-span-2">
              <label className="block text-[11px] font-semibold text-sky-400 mb-1 font-mono">
                2. Select Real Schedule to Auto-Fill
              </label>
              <select
                onChange={(e) => handleSelectRealSchedule(e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg bg-surface-container-low border border-surface-container-high text-xs text-white focus:outline-none focus:border-sky-400 font-sans h-8"
              >
                {activeCatalogOptions.map((item, idx) => (
                  <option key={item.reference_number + idx} value={idx}>
                    {item.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2.5">
            <div>
              <label className="block text-[10px] text-on-surface-variant mb-1">Operator / Provider</label>
              <input
                type="text"
                required
                value={form.provider_name}
                onChange={(e) => setForm({ ...form, provider_name: e.target.value })}
                className="w-full px-2.5 py-1.5 rounded-lg bg-surface-container-lowest border border-surface-container-high text-xs text-white focus:outline-none focus:border-sky-400 h-8"
              />
            </div>
            <div>
              <label className="block text-[10px] text-on-surface-variant mb-1">Train / Flight / PNR No.</label>
              <input
                type="text"
                required
                value={form.reference_number}
                onChange={(e) => setForm({ ...form, reference_number: e.target.value })}
                className="w-full px-2.5 py-1.5 rounded-lg bg-surface-container-lowest border border-surface-container-high text-xs text-white font-mono focus:outline-none focus:border-sky-400 h-8"
              />
            </div>
            <div>
              <label className="block text-[10px] text-on-surface-variant mb-1">From City</label>
              <input
                type="text"
                required
                value={form.origin}
                onChange={(e) => setForm({ ...form, origin: e.target.value })}
                className="w-full px-2.5 py-1.5 rounded-lg bg-surface-container-lowest border border-surface-container-high text-xs text-white focus:outline-none focus:border-sky-400 h-8"
              />
            </div>
            <div>
              <label className="block text-[10px] text-on-surface-variant mb-1">To City</label>
              <input
                type="text"
                required
                value={form.destination}
                onChange={(e) => setForm({ ...form, destination: e.target.value })}
                className="w-full px-2.5 py-1.5 rounded-lg bg-surface-container-lowest border border-surface-container-high text-xs text-white focus:outline-none focus:border-sky-400 h-8"
              />
            </div>
            <div>
              <label className="block text-[10px] text-on-surface-variant mb-1">Departure / Check-in</label>
              <input
                type="datetime-local"
                required
                value={form.start_time}
                onChange={(e) => setForm({ ...form, start_time: e.target.value })}
                className="w-full px-2.5 py-1.5 rounded-lg bg-surface-container-lowest border border-surface-container-high text-xs text-white font-mono focus:outline-none focus:border-sky-400 h-8"
              />
            </div>
            <div>
              <label className="block text-[10px] text-on-surface-variant mb-1">Arrival / Check-out</label>
              <input
                type="datetime-local"
                required
                value={form.end_time}
                onChange={(e) => setForm({ ...form, end_time: e.target.value })}
                className="w-full px-2.5 py-1.5 rounded-lg bg-surface-container-lowest border border-surface-container-high text-xs text-white font-mono focus:outline-none focus:border-sky-400 h-8"
              />
            </div>
            <div>
              <label className="block text-[10px] text-on-surface-variant mb-1">Fare (INR)</label>
              <input
                type="number"
                required
                value={form.price}
                onChange={(e) => setForm({ ...form, price: e.target.value })}
                className="w-full px-2.5 py-1.5 rounded-lg bg-surface-container-lowest border border-surface-container-high text-xs text-white font-mono focus:outline-none focus:border-sky-400 h-8"
              />
            </div>
            <div className="flex items-end justify-end">
              <button
                type="submit"
                disabled={busy}
                className="w-full px-3 py-1.5 rounded-lg bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 disabled:opacity-50 text-white text-xs font-bold cursor-pointer transition shadow-[0_0_12px_rgba(0,229,255,0.25)] font-display h-8"
              >
                {busy ? 'Saving...' : 'Save Booking'}
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Alert Banner When Disruption Breaks a Connection */}
      {hasBrokenConnection && !proposedPlan && !recoveryResult && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-950/25 p-3.5 sm:p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 backdrop-blur-xl shadow-[0_0_15px_rgba(244,63,94,0.12)]">
          <div className="space-y-0.5">
            <div className="text-xs sm:text-sm font-bold text-rose-200 flex items-center gap-2 font-display">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>Disruption Detected — Downstream Connection Missed!</span>
            </div>
            <p className="text-xs text-slate-200 leading-relaxed font-sans">
              {impactResult?.explanation ||
                'A delay caused an impossible connection in your itinerary. Click below to generate an optimized recovery plan for human review.'}
            </p>
          </div>

          <button
            type="button"
            onClick={handleAutoRecover}
            disabled={busy}
            className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50 text-white text-xs font-bold flex items-center gap-2 shadow-[0_0_12px_rgba(16,185,129,0.25)] shrink-0 cursor-pointer transition font-display h-8"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{busy ? 'Formulating Plan...' : 'Generate Recovery Plan'}</span>
          </button>
        </div>
      )}

      {/* Human Review & Approval Gate Card */}
      {proposedPlan && !recoveryResult && (
        <div className="rounded-xl border border-sky-500/40 bg-surface-container-low/95 p-4 sm:p-5 space-y-3.5 backdrop-blur-2xl shadow-glass-card relative overflow-hidden">
          <div className="absolute top-0 right-0 w-80 h-80 bg-sky-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
          
          {(() => {
            const revisionCount = proposedPlan.revision_count || 1;
            const maxRevisions = 3;
            const isInfeasible = proposedPlan.status === 'REVISION_REQUIRED' || proposedPlan.is_feasible === false;
            const isRejected = proposedPlan.status === 'REJECTED';
            const constraintDescs = proposedPlan.active_constraints?.descriptions || [];

            return (
              <>
                <div className="flex flex-wrap items-center justify-between gap-2.5 relative z-10">
                  <div className="flex items-center gap-2">
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold border ${
                      isInfeasible
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                        : isRejected
                        ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                        : 'bg-sky-500/20 text-sky-300 border-sky-500/40'
                    }`}>
                      {isInfeasible
                        ? 'REVISION_REQUIRED / INFEASIBLE'
                        : isRejected
                        ? 'REJECTED (Execution Blocked)'
                        : 'PLAN_GENERATED → HUMAN_REVIEW'}
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-mono font-bold uppercase bg-white/[0.06] text-slate-300 border border-surface-container-high">
                      Rev #{revisionCount} of {maxRevisions}
                    </span>
                    <h3 className="text-sm sm:text-base font-bold text-white font-display">
                      Human Review Gate — Plan #{revisionCount}
                    </h3>
                  </div>

                  <div className="flex items-center gap-2">
                    {isInfeasible ? (
                      <>
                        <button
                          type="button"
                          onClick={() => setShowManualModal(true)}
                          className="px-3 py-1.5 rounded-lg border border-sky-500/40 bg-sky-500/10 hover:bg-sky-500/20 text-sky-300 text-xs font-bold flex items-center gap-1.5 shadow-sm transition cursor-pointer font-display h-8"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>Review Alternatives Manually</span>
                        </button>
                        {revisionCount < maxRevisions && (
                          <button
                            type="button"
                            onClick={handleOpenRejectDialog}
                            className="px-3 py-1.5 rounded-lg border border-amber-500/40 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 text-xs font-bold flex items-center gap-1.5 shadow-sm transition cursor-pointer font-display h-8"
                          >
                            <Sliders className="w-3.5 h-3.5" />
                            <span>Adjust Constraints</span>
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={handleResetConstraintsAndReplan}
                          disabled={busy}
                          className="px-3 py-1.5 rounded-lg border border-surface-container-high bg-surface-container-lowest hover:bg-surface-container-high text-slate-300 hover:text-white text-xs font-bold flex items-center gap-1.5 transition cursor-pointer font-display h-8"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                          <span>Reset</span>
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          type="button"
                          onClick={handleOpenRejectDialog}
                          disabled={executingPlan || revisingPlan || isRejected}
                          className="px-3.5 py-1.5 rounded-lg border border-amber-500/40 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 text-xs font-bold flex items-center gap-1.5 shadow-sm transition cursor-pointer font-display h-8 disabled:opacity-50"
                          title="Reject plan and supply constraints for revision"
                        >
                          <XCircle className="w-3.5 h-3.5 text-amber-400" />
                          <span>{revisingPlan ? 'Formulating Revision...' : 'Reject & Revise'}</span>
                        </button>

                        <button
                          type="button"
                          onClick={handleApproveAndExecute}
                          disabled={executingPlan || revisingPlan || isRejected}
                          className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50 text-white text-xs font-bold flex items-center gap-1.5 shadow-[0_0_12px_rgba(16,185,129,0.25)] cursor-pointer transition font-display h-8"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>{executingPlan ? 'Marking APPROVED → EXECUTING...' : 'Approve & Execute'}</span>
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {/* Infeasible Callout Banner */}
                {isInfeasible && (
                  <div className="p-3.5 rounded-xl border border-amber-500/40 bg-amber-950/30 text-amber-200 space-y-2 font-display relative z-10">
                    <div className="flex items-center gap-2 font-bold text-amber-300 text-sm">
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                      <span>No suitable automated recovery plan could be found with the current requirements.</span>
                    </div>
                    <p className="text-xs text-amber-200/90 font-sans leading-relaxed">
                      OR-Tools solver evaluated all catalog alternatives against your active constraints. No automated combination satisfies the transfer buffer and budget limits. Human review of available alternatives is provided below. Automated execution is strictly blocked.
                    </p>
                  </div>
                )}

                {/* Rejected Warning Banner */}
                {isRejected && !isInfeasible && (
                  <div className="p-2.5 rounded-lg border border-rose-500/40 bg-rose-950/30 text-xs text-rose-200 flex items-center gap-2 font-display relative z-10">
                    <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                    <span>Plan has been REJECTED. The backend approval gate has strictly blocked execution of these actions.</span>
                  </div>
                )}

                {/* Retained Constraints Tags */}
                {constraintDescs.length > 0 && (
                  <div className="p-2 rounded-lg bg-surface-container-lowest/80 border border-surface-container-high/80 space-y-1 relative z-10">
                    <span className="text-[10px] font-mono uppercase font-bold text-sky-400 tracking-wider block">
                      Retained Cumulative Constraints (Active in Planner):
                    </span>
                    <div className="flex flex-wrap gap-1.5 pt-0.5">
                      {constraintDescs.map((desc, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 rounded-md bg-sky-500/15 border border-sky-500/30 text-[11px] text-sky-300 font-mono flex items-center gap-1"
                        >
                          <span className="text-sky-400 font-bold">✓</span> {desc}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Live Execution Progress Strip */}
                {executingPlan && (
                  <div className="p-3 rounded-xl border border-emerald-500/50 bg-emerald-950/40 text-emerald-200 text-xs flex flex-wrap items-center justify-between gap-2 font-display relative z-10 animate-pulse">
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                      <span className="font-bold">
                        {executionPhase === 'APPROVED' ? 'Status: APPROVED by Human Reviewer' : 'Status: EXECUTING Real Actions Against Supplier APIs...'}
                      </span>
                    </div>
                    <span className="font-mono text-[11px] uppercase tracking-wider font-bold text-emerald-300">
                      APPROVED → EXECUTING → COMPLETED
                    </span>
                  </div>
                )}

                {/* 4 Guided Human Decision Briefing Panels */}
                {!isInfeasible && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1 relative z-10">
                    {/* 1. What happened? */}
                    <div className="p-3 rounded-xl bg-surface-container-lowest/90 border border-surface-container-high space-y-1">
                      <div className="flex items-center gap-1.5 text-rose-300 font-display text-xs font-bold">
                        <AlertTriangle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                        <span>1. What happened?</span>
                      </div>
                      <p className="text-xs text-slate-300 font-sans leading-relaxed">
                        {proposedPlan.disruption_summary ||
                          impactResult?.explanation ||
                          'Flight delay caused an impossible connection buffer (-150m), resulting in a missed connection to downstream transport.'}
                      </p>
                    </div>

                    {/* 2. What does AeroAI recommend? */}
                    <div className="p-3 rounded-xl bg-surface-container-lowest/90 border border-surface-container-high space-y-1">
                      <div className="flex items-center gap-1.5 text-sky-300 font-display text-xs font-bold">
                        <Sparkles className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                        <span>2. What does AeroAI recommend?</span>
                      </div>
                      <p className="text-xs text-slate-300 font-sans leading-relaxed">
                        Rebook onto <strong className="text-white">{proposedPlan.selected_option?.name}</strong> (₹{proposedPlan.selected_option?.price}). Claim ₹{proposedPlan.refund_amount_inr ?? 600} involuntary waiver refund, and shift hotel check-in 30m.
                      </p>
                    </div>

                    {/* 3. What will happen if I approve? */}
                    <div className="p-3 rounded-xl bg-surface-container-lowest/90 border border-surface-container-high space-y-1">
                      <div className="flex items-center gap-1.5 text-emerald-300 font-display text-xs font-bold">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        <span>3. What will happen if I approve?</span>
                      </div>
                      <p className="text-xs text-slate-300 font-sans leading-relaxed">
                        Plan transitions <span className="font-mono text-emerald-300 text-[11px] font-bold">APPROVED → EXECUTING → COMPLETED</span>: cancels missed leg, confirms new booking, files waiver refund claim, and notifies hotel partner.
                      </p>
                    </div>

                    {/* 4. Why can I reject it? */}
                    <div className="p-3 rounded-xl bg-surface-container-lowest/90 border border-surface-container-high space-y-1">
                      <div className="flex items-center gap-1.5 text-amber-300 font-display text-xs font-bold">
                        <Sliders className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                        <span>4. Why can I reject it?</span>
                      </div>
                      <p className="text-xs text-slate-300 font-sans leading-relaxed">
                        Prefer a different airline, lower budget, or other timing? Click <strong className="text-amber-300">Reject & Revise</strong>. AeroAI retains all your feedback as constraints for Plan #{revisionCount + 1} without executing anything.
                      </p>
                    </div>
                  </div>
                )}

                {/* Plan Summary */}
                {!isInfeasible && (
                  <p className="text-xs text-slate-300 leading-relaxed font-sans relative z-10 pt-0.5">
                    {proposedPlan.summary || 'A proposed recovery plan was formulated by OR-Tools without executing actions. Review actions below and authorize execution.'}
                  </p>
                )}

                {/* Feasible Plan Columns */}
                {!isInfeasible && proposedPlan.selected_option && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 pt-1 text-xs relative z-10">
                    <div className="p-2.5 rounded-lg bg-surface-container-lowest border border-surface-container-high space-y-1">
                      <span className="text-[10px] text-sky-400 font-mono font-bold uppercase block">Proposed Transport</span>
                      <span className="text-white font-medium block truncate">
                        {proposedPlan.selected_option?.name || proposedPlan.selected_option?.transport_id || 'Alternative transport'}
                      </span>
                      <span className="text-slate-400 text-[11px] block">
                        Fare: ₹{proposedPlan.selected_option?.price || 0} (Diff: ₹{proposedPlan.net_additional_cost ?? 0})
                      </span>
                    </div>

                    <div className="p-2.5 rounded-lg bg-surface-container-lowest border border-surface-container-high space-y-1">
                      <span className="text-[10px] text-emerald-400 font-mono font-bold uppercase block">Refund Eligibility</span>
                      <span className="text-emerald-300 font-medium block">
                        ₹{proposedPlan.refund_amount_inr ?? 600} Involuntary Waiver
                      </span>
                      <span className="text-slate-400 text-[11px] block">
                        Policy IRCTC-INV-DELAY-75PCT
                      </span>
                    </div>

                    <div className="p-2.5 rounded-lg bg-surface-container-lowest border border-surface-container-high space-y-1">
                      <span className="text-[10px] text-amber-400 font-mono font-bold uppercase block">Downstream Adjustments</span>
                      <span className="text-white font-medium block">
                        Hotel Check-in shifted 30m
                      </span>
                      <span className="text-slate-400 text-[11px] block">
                        Preserves hotel arrival cutoff
                      </span>
                    </div>
                  </div>
                )}
              </>
            );
          })()}
        </div>
      )}

      {/* Success Banner After AI Recovery */}
      {recoveryResult && (
        <div className="rounded-xl border border-emerald-500/30 bg-surface-container-low/90 p-3.5 sm:p-4 space-y-3 backdrop-blur-2xl shadow-glass-card relative overflow-hidden">
          <div className="absolute top-0 right-0 w-72 h-72 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
          <div className="flex flex-wrap items-center justify-between gap-2 relative z-10">
            <div className="text-sm sm:text-base font-bold text-emerald-300 flex items-center gap-2 font-display">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Trip Recovered Automatically by AI!</span>
            </div>
            {recoveryResult.optimization?.selected_option && (
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-xs font-mono font-bold text-emerald-200 shadow-[0_0_8px_rgba(16,185,129,0.15)]">
                Selected: {recoveryResult.optimization.selected_option.name} (₹{recoveryResult.optimization.selected_option.price})
              </span>
            )}
          </div>

          <p className="text-xs text-slate-200 leading-relaxed font-sans relative z-10">
            {recoveryResult.optimization?.explanation}
          </p>

          {/* 3 Simple Columns to Explain in an Interview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5 pt-1 relative z-10">
            <div className="p-3 rounded-xl bg-surface-container-lowest border border-surface-container-high space-y-1.5">
              <div className="text-[10px] font-bold uppercase text-sky-400 font-mono">
                1. OR-Tools Math Decision
              </div>
              <div className="space-y-1 text-xs text-slate-300">
                {(recoveryResult.optimization?.evaluated_alternatives || []).map((alt) => (
                  <div key={alt.transport_id} className="flex items-center justify-between gap-2">
                    <span className="truncate font-sans text-xs">{alt.name}</span>
                    <span
                      className={`font-mono text-[10px] px-2 py-0.5 rounded-full shrink-0 border ${
                        alt.selected
                          ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30 font-bold shadow-[0_0_8px_rgba(16,185,129,0.15)]'
                          : alt.feasible
                          ? 'bg-white/[0.05] text-slate-300 border-surface-container-high'
                          : 'bg-rose-500/15 text-rose-300 border-rose-500/30'
                      }`}
                    >
                      {alt.selected ? '✓ WINNER' : alt.feasible ? `Score ${alt.Weighted_Score ?? ''}` : 'Pruned'}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-surface-container-lowest border border-surface-container-high space-y-1.5">
              <div className="text-[10px] font-bold uppercase text-emerald-400 font-mono">
                2. Real Actions Executed
              </div>
              <ul className="space-y-1 text-xs text-slate-300 font-sans">
                <li className="flex items-center gap-1.5">
                  <span className="text-emerald-400 font-bold font-mono">✓</span> Cancelled: {recoveryResult.details?.cancelled_booking || 'Missed connection'}
                </li>
                <li className="flex items-center gap-1.5">
                  <span className="text-emerald-400 font-bold font-mono">✓</span> Booked: {recoveryResult.details?.rebooked_booking || recoveryResult.optimization?.selected_option?.name}
                </li>
                <li className="flex items-center gap-1.5">
                  <span className="text-emerald-400 font-bold font-mono">✓</span> Refund Claimed: ₹{recoveryResult.details?.refund_amount_inr ?? 600} (75% waiver)
                </li>
                <li className="flex items-center gap-1.5">
                  <span className="text-emerald-400 font-bold font-mono">✓</span> Hotel: {recoveryResult.details?.hotel_updated || 'Check-in time updated'}
                </li>
              </ul>
            </div>

            <div className="p-3 rounded-xl bg-surface-container-lowest border border-surface-container-high space-y-1.5">
              <div className="text-[10px] font-bold uppercase text-amber-400 font-mono">
                3. Notifications Sent ({(workspace?.notifications || []).length})
              </div>
              <div className="space-y-1 text-xs text-slate-300">
                {(workspace?.notifications || []).slice(0, 4).map((n, i) => (
                  <div key={i} className="truncate text-[10px]">
                    &bull; <span className="text-on-surface-variant">{n.category}:</span> {n.recipient}
                  </div>
                ))}
                {(workspace?.notifications || []).length > 4 && (
                  <div className="text-[10px] text-on-surface-variant font-mono">
                    + {(workspace?.notifications || []).length - 4} more in &ldquo;Sent Emails&rdquo;
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bookings List */}
      {bookings.length === 0 ? (
        <div className="rounded-xl border border-dashed border-surface-container-high bg-surface-container-low/60 backdrop-blur-xl p-8 text-center space-y-3">
          <div className="text-sm sm:text-base font-bold text-white font-display">Your itinerary is empty</div>
          <p className="text-xs text-on-surface-variant max-w-md mx-auto font-sans leading-relaxed">
            Click <strong>+ Add Booking</strong> to select real Air India / IndiGo flights, IRCTC trains, Volvo buses, and hotels — or load the Golden Triangle trip below.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2.5">
            <button
              type="button"
              onClick={() => setShowAddModal(true)}
              className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-primary-container to-primary-fixed-dim text-on-primary hover:brightness-110 active:scale-[0.98] text-xs font-bold cursor-pointer transition shadow-[0_0_12px_rgba(0,229,255,0.25)] font-display h-8"
            >
              + Add Real Flight / Train / Bus / Hotel
            </button>
            <button
              type="button"
              onClick={handleLoadSampleTrip}
              disabled={busy}
              className="px-3.5 py-1.5 rounded-lg bg-surface-container-lowest hover:bg-white/[0.05] disabled:opacity-50 text-slate-200 border border-surface-container-high text-xs font-bold cursor-pointer transition font-display h-8"
            >
              {busy ? 'Loading...' : 'Load Golden Triangle Trip'}
            </button>
            {onOpenAdvancedPage && (
              <button
                type="button"
                onClick={() => onOpenAdvancedPage('chatbot')}
                className="px-3.5 py-1.5 rounded-lg bg-indigo-500/15 hover:bg-indigo-500/25 text-indigo-200 border border-indigo-400/30 text-xs font-bold flex items-center gap-1.5 cursor-pointer transition shadow-[0_0_10px_rgba(99,102,241,0.15)] font-display h-8"
              >
                <Bot className="w-3.5 h-3.5 text-indigo-400" />
                <span>Ask Policy Chatbot</span>
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-2.5">
          {bookings.map((b, idx) => {
            const edge = edges[idx] || null;
            return (
              <React.Fragment key={b.id}>
                <div
                  className={`p-3.5 rounded-xl border backdrop-blur-2xl transition-all shadow-glass-card flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                    b.status === 'DELAYED' || b.status === 'CANCELLED'
                      ? 'border-rose-500/40 bg-rose-950/20 shadow-[0_0_15px_rgba(244,63,94,0.08)]'
                      : 'border-surface-container-high bg-surface-container-low/90 hover:border-white/20'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="p-2.5 rounded-lg bg-surface-container-lowest border border-surface-container-high shadow-inner shrink-0">
                      {getIcon(b.booking_type)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
                        <span className="text-xs sm:text-sm font-bold text-white font-display break-words">{b.title}</span>
                        <span className="text-[11px] font-mono text-on-surface-variant">({b.reference_number})</span>
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold border shrink-0 ${
                            b.status === 'CONFIRMED'
                              ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30 shadow-[0_0_6px_rgba(16,185,129,0.15)]'
                              : 'bg-rose-500/20 text-rose-300 border-rose-500/30 shadow-[0_0_6px_rgba(244,63,94,0.15)]'
                          }`}
                        >
                          {b.status}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-300 mt-0.5 flex flex-wrap items-center gap-1.5">
                        <span className="font-sans">
                          {b.origin} &rarr; {b.destination}
                        </span>
                        <span className="text-slate-600">&bull;</span>
                        <span className="font-mono text-sky-300">
                          {formatDateTime(b.start_time)} &rarr; {formatDateTime(b.end_time)}
                        </span>
                        <span className="text-slate-600">&bull;</span>
                        <span className="font-mono text-slate-200">₹{b.price}</span>
                      </div>
                    </div>
                  </div>

                  {/* Action Controls on Transport Cards */}
                  <div className="flex flex-wrap items-center gap-1.5 shrink-0">
                    {idx === 0 && b.status === 'CONFIRMED' && (
                      <div className="flex items-center gap-1">
                        <select
                          value={delayMinutes}
                          onChange={(e) => setDelayMinutes(Number(e.target.value))}
                          className="px-2 py-1 rounded-lg bg-surface-container-lowest border border-surface-container-high text-xs text-slate-200 focus:outline-none focus:border-amber-400 font-mono h-7.5"
                        >
                          <option value={60}>+1 hr delay</option>
                          <option value={120}>+2 hr delay</option>
                          <option value={240}>+4 hr delay</option>
                        </select>
                        <button
                          type="button"
                          onClick={() => handleSimulateDelay(b.id)}
                          disabled={busy}
                          className="px-2.5 py-1 rounded-lg bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-xs font-bold cursor-pointer transition shadow-[0_0_8px_rgba(245,158,11,0.25)] font-display h-7.5"
                        >
                          Simulate Delay
                        </button>
                      </div>
                    )}

                    <button
                      type="button"
                      onClick={() => handleDeleteBooking(b.id)}
                      disabled={busy}
                      className="p-1.5 rounded-lg text-outline hover:text-rose-300 hover:bg-white/[0.05] cursor-pointer transition"
                      title="Remove booking"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Connection Indicator Between Bookings */}
                {edge && (
                  <div className="pl-6 flex items-center gap-2.5 py-0.5">
                    <div className="w-0.5 h-4 bg-white/[0.15]" />
                    <span
                      className={`text-[11px] font-mono px-2.5 py-0.5 rounded-full border ${
                        edge.risk_level === 'IMPOSSIBLE'
                          ? 'bg-rose-500/20 text-rose-300 border-rose-500/40 font-bold shadow-[0_0_8px_rgba(244,63,94,0.2)]'
                          : edge.risk_level === 'TIGHT'
                          ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-[0_0_8px_rgba(245,158,11,0.15)]'
                          : 'bg-surface-container-lowest text-on-surface-variant border-surface-container-high'
                      }`}
                    >
                      {edge.risk_level === 'IMPOSSIBLE'
                        ? `❌ Missed Connection (${edge.buffer_minutes}m buffer)`
                        : `✓ ${edge.buffer_minutes}m connection buffer`}
                    </span>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      )}

      {/* Rejection & Revision Dialog */}
      <RejectionDialog
        open={showRejectModal}
        onClose={() => setShowRejectModal(false)}
        onSubmit={handleConfirmRejectAndReplan}
        revisionCount={proposedPlan?.revision_count || 1}
        maxRevisions={3}
        previousConstraints={proposedPlan?.active_constraints}
        submitting={revisingPlan}
      />

      {/* Manual Alternatives Review Modal */}
      {showManualModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-md overflow-y-auto">
          <div className="w-full max-w-2xl rounded-2xl border border-sky-500/40 bg-surface-container-lowest/95 p-4 sm:p-6 shadow-[0_20px_50px_rgba(0,0,0,0.8)] backdrop-blur-2xl text-on-surface space-y-4 my-auto max-h-[92vh] flex flex-col justify-between">
            <div className="flex items-center justify-between border-b border-surface-container-high pb-3 shrink-0">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-sky-500/15 border border-sky-500/30 flex items-center justify-center text-sky-400 shrink-0">
                  <Eye className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white font-display">
                    Manual Review: Available Transport Alternatives
                  </h3>
                  <p className="text-xs text-slate-400">
                    Review alternative services from real catalog and mock supplier inventories.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowManualModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-surface-container-high transition"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <div className="max-h-80 overflow-y-auto space-y-2 pr-1 flex-1">
              {['FLIGHT', 'TRAIN', 'BUS'].map((cat) => {
                const items = catalog[cat] || [];
                return (
                  <div key={cat} className="space-y-1.5">
                    <span className="text-[10px] font-mono font-bold uppercase text-sky-400 tracking-wider">
                      {cat} Alternatives ({items.length})
                    </span>
                    <div className="grid grid-cols-1 gap-1.5">
                      {items.map((item, idx) => (
                        <div
                          key={idx}
                          className="p-2.5 rounded-xl border border-surface-container-high bg-surface-container-low/70 flex items-center justify-between gap-3 text-xs"
                        >
                          <div className="flex items-center gap-2.5 min-w-0">
                            {getIcon(item.booking_type)}
                            <div className="min-w-0">
                              <span className="font-semibold text-white truncate block">
                                {item.title || item.label}
                              </span>
                              <span className="text-slate-400 text-[11px] font-mono">
                                {formatDateTime(item.start_time)} → {formatDateTime(item.end_time)} · {item.provider_name}
                              </span>
                            </div>
                          </div>
                          <span className="font-mono font-bold text-emerald-300 shrink-0 text-sm">
                            ₹{item.price}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2.5 pt-2 border-t border-surface-container-high text-xs shrink-0">
              <span className="text-slate-400">
                To adjust automated recovery rules, click <strong className="text-amber-300">Adjust Constraints</strong>.
              </span>
              <button
                type="button"
                onClick={() => setShowManualModal(false)}
                className="w-full sm:w-auto px-4 py-1.5 rounded-lg bg-surface-container-high hover:bg-surface-container-highest text-white font-medium transition cursor-pointer font-display h-8 flex items-center justify-center"
              >
                Close Review
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
