import React, { useState, useEffect } from 'react';
import {
  Plane,
  CloudRain,
  ShieldCheck,
  Bot,
  Search,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Compass,
  ArrowRight,
  Sparkles,
  RefreshCw,
  FileText,
  ExternalLink,
  Layers,
  BarChart3,
  Send,
  Info,
  Target,
  TrendingUp,
  Sliders,
  Database,
  Activity,
  Award
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../services/api';
import { CountUpNumber } from './ui/SaaSPrimitives';

const SAMPLE_FLIGHTS = [
  { code: 'AI202', label: 'AI202 (DEL -> BOM)', carrier: 'Air India', desc: 'Domestic Trunk Route' },
  { code: 'UK981', label: 'UK981 (DEL -> BOM)', carrier: 'Vistara', desc: 'Airborne Telemetry' },
  { code: '6E205', label: '6E205 (DEL -> JAI)', carrier: 'IndiGo', desc: 'Golden Triangle' },
  { code: 'BA142', label: 'BA142 (DEL -> LHR)', carrier: 'British Airways', desc: 'Transatlantic Long-Haul' },
  { code: 'DL450', label: 'DL450 (JFK -> LAX)', carrier: 'Delta', desc: 'U.S. Transcontinental' },
];

const SUGGESTED_AGENT_PROMPTS = [
  'Will flight AI202 be delayed?',
  'If my flight is delayed by 4 hours, can I get a refund under DGCA rules?',
  'My flight tomorrow AI202 has high delay risk. What should I do and what are my rights?',
  'Find alternative flights from DEL to BOM',
  'What is the checked baggage allowance on Air India?'
];

export function AeroAIFlightIntelligenceView() {
  const [activeTab, setActiveTab] = useState('intelligence'); // 'intelligence' | 'agent'
  
  // Flight Intelligence State
  const [flightNumberInput, setFlightNumberInput] = useState('AI202');
  const [flightStatusData, setFlightStatusData] = useState(null);
  const [flightLoading, setFlightLoading] = useState(false);
  const [flightError, setFlightError] = useState(null);
  
  // Alternative Search State
  const [searchOrigin, setSearchOrigin] = useState('DEL');
  const [searchDest, setSearchDest] = useState('BOM');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);

  // Unified Agent Chat State
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I am the AeroAI Unified Flight Intelligence Agent. I connect live transponder radar, BTS machine learning delay models, surface weather intelligence, and authoritative airline regulatory policies. How can I assist your journey today?',
      selected_tools: ['policy_rag', 'flight_status', 'delay_prediction', 'weather', 'flight_search'],
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [agentLoading, setAgentLoading] = useState(false);
  const [agentError, setAgentError] = useState(null);
  const [selectedCitationDoc, setSelectedCitationDoc] = useState(null);

  // Stage 4 Model Evaluation Benchmark State
  const [evalMetrics, setEvalMetrics] = useState(null);
  const [evalLoading, setEvalLoading] = useState(false);
  const [evalThreshold, setEvalThreshold] = useState('0.25'); // '0.25' (Calibrated) | '0.50' (Standard)

  const loadEvaluationMetrics = async () => {
    setEvalLoading(true);
    try {
      const data = await api.getModelEvaluationMetrics();
      setEvalMetrics(data);
    } catch (err) {
      console.error('Failed to load evaluation metrics:', err);
    } finally {
      setEvalLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    handleLookupFlight('AI202');
    handleSearchInventory('DEL', 'BOM');
    loadEvaluationMetrics();
  }, []);

  const handleLookupFlight = async (flightNum) => {
    if (!flightNum) return;
    setFlightLoading(true);
    setFlightError(null);
    try {
      // Query fused prediction & status endpoint
      const data = await api.getFlightPrediction(flightNum);
      setFlightStatusData(data);
    } catch (err) {
      console.error('Flight lookup failed:', err);
      setFlightError(err?.response?.data?.detail || err?.message || `Failed to retrieve data for flight ${flightNum}`);
      setFlightStatusData(null);
    } finally {
      setFlightLoading(false);
    }
  };

  const handleSearchInventory = async (orig, dest) => {
    if (!orig || !dest) return;
    setSearchLoading(true);
    setSearchError(null);
    try {
      const items = await api.searchFlightInventory({ origin: orig, destination: dest, min_seats: 1 });
      setSearchResults(items || []);
    } catch (err) {
      console.error('Flight search failed:', err);
      setSearchError(err?.response?.data?.detail || err?.message || 'Flight search failed');
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSendAgentQuery = async (queryText) => {
    const textToSend = queryText || inputPrompt;
    if (!textToSend.trim()) return;

    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputPrompt('');
    setAgentLoading(true);
    setAgentError(null);

    try {
      const res = await api.sendAgentQuery({ message: textToSend });
      const assistantMsg = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: res.answer,
        sections: res.sections || {},
        selected_tools: res.selected_tools || [],
        duration_ms: res.execution_duration_ms,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error('Agent query failed:', err);
      setAgentError(err?.response?.data?.detail || err?.message || 'Agent interaction failed');
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: '⚠️ I encountered an issue coordinating tools for this request. Please verify your query or try again.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setAgentLoading(false);
    }
  };

  // Helper for Probability styling & calibrated wording
  const getProbabilityColor = (prob) => {
    if (prob >= 0.60) return 'text-rose-400 border-rose-500/40 bg-rose-950/20';
    if (prob >= 0.35) return 'text-amber-400 border-amber-500/40 bg-amber-950/20';
    return 'text-emerald-400 border-emerald-500/40 bg-emerald-950/20';
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Platform Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-white/[0.08] pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-xs font-mono font-semibold bg-sky-500/15 text-sky-300 border border-sky-400/30">
              <Sparkles className="w-3 h-3 text-sky-400 animate-pulse" />
              Unified Flight Intelligence
            </span>
            <span className="text-xs font-mono text-slate-400">Stage 7 Agent Active</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight mt-1.5 font-display">
            AeroAI Flight Intelligence Hub
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 font-sans">
            Autonomous multi-modal plane combining predictive delay models, live transponder radar, surface weather, and travel-policy RAG.
          </p>
        </div>

        {/* View Toggle */}
        <div className="flex bg-[#070b16] p-1.5 rounded-2xl border border-white/[0.08] self-start md:self-auto shadow-inner">
          <button
            onClick={() => setActiveTab('intelligence')}
            className={`flex items-center gap-2 px-3.5 sm:px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer font-display ${
              activeTab === 'intelligence'
                ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white shadow-[0_0_15px_rgba(14,165,233,0.3)]'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Plane className="w-4 h-4" />
            <span className="hidden sm:inline">Flight Radar &</span> Predictor
          </button>
          <button
            onClick={() => setActiveTab('benchmarks')}
            className={`flex items-center gap-2 px-3.5 sm:px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer font-display ${
              activeTab === 'benchmarks'
                ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white shadow-[0_0_15px_rgba(14,165,233,0.3)]'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Model Benchmarks</span>
          </button>
          <button
            onClick={() => setActiveTab('agent')}
            className={`flex items-center gap-2 px-3.5 sm:px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer font-display ${
              activeTab === 'agent'
                ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white shadow-[0_0_15px_rgba(14,165,233,0.3)]'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Bot className="w-4 h-4" />
            <span className="hidden sm:inline">AeroAI</span> Agent
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: FLIGHT RADAR & DELAY PREDICTOR                                     */}
      {/* ========================================================================= */}
      {activeTab === 'intelligence' && (
        <div className="space-y-6">
          {/* Quick Lookup Toolbar */}
          <div className="bg-[#070b16]/80 backdrop-blur-2xl rounded-3xl border border-white/[0.08] p-5 shadow-glass-card relative overflow-hidden">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleLookupFlight(flightNumberInput);
                }}
                className="flex items-center gap-3 flex-1 max-w-md"
              >
                <div className="relative flex-1">
                  <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
                  <input
                    type="text"
                    value={flightNumberInput}
                    onChange={(e) => setFlightNumberInput(e.target.value.toUpperCase())}
                    placeholder="Enter Flight Number (e.g. AI202, 6E205, BA142)"
                    className="w-full pl-10 pr-4 py-2.5 bg-[#04060d] border border-white/[0.1] rounded-xl text-white font-mono placeholder:text-slate-500 text-xs focus:outline-none focus:border-sky-400 focus:shadow-[0_0_15px_rgba(56,189,248,0.25)] transition"
                  />
                </div>
                <button
                  type="submit"
                  disabled={flightLoading}
                  className="px-4 py-2.5 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl flex items-center gap-1.5 transition shadow-[0_0_15px_rgba(14,165,233,0.3)] cursor-pointer font-display"
                >
                  {flightLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Plane className="w-3.5 h-3.5" />}
                  Inspect
                </button>
              </form>

              {/* Sample Flight Chips */}
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs text-slate-400 font-mono font-medium">Quick Presets:</span>
                {SAMPLE_FLIGHTS.map((sf) => (
                  <button
                    key={sf.code}
                    onClick={() => {
                      setFlightNumberInput(sf.code);
                      handleLookupFlight(sf.code);
                    }}
                    className={`px-3 py-1.5 text-xs rounded-xl font-mono border transition-all cursor-pointer ${
                      flightNumberInput === sf.code
                        ? 'bg-sky-500/20 text-sky-300 border-sky-400/40 shadow-[0_0_10px_rgba(56,189,248,0.25)]'
                        : 'bg-[#04060d] text-slate-400 border-white/[0.08] hover:border-white/20 hover:text-white'
                    }`}
                  >
                    {sf.code}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Error Banner */}
          {flightError && (
            <div className="p-4 rounded-2xl bg-rose-950/30 border border-rose-500/30 text-rose-200 text-xs flex items-center gap-3 backdrop-blur-xl">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
              <div className="flex-1 font-medium">{flightError}</div>
              <button
                onClick={() => handleLookupFlight(flightNumberInput)}
                className="px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white text-xs rounded-xl font-semibold transition cursor-pointer"
              >
                Retry
              </button>
            </div>
          )}

          {/* Loading Skeleton */}
          {flightLoading && !flightStatusData && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="h-64 bg-[#070b16]/70 rounded-3xl border border-white/[0.06] shimmer-wave"></div>
              <div className="h-64 bg-[#070b16]/70 rounded-3xl border border-white/[0.06] shimmer-wave"></div>
              <div className="h-64 bg-[#070b16]/70 rounded-3xl border border-white/[0.06] shimmer-wave"></div>
            </div>
          )}

          {/* Main Inspection Grid */}
          {flightStatusData && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Card 1: Operational Status & Radar Telemetry */}
              <div className="bg-[#070b16]/80 rounded-3xl border border-white/[0.08] p-6 flex flex-col justify-between backdrop-blur-2xl shadow-glass-card hover:border-white/20 transition-all relative overflow-hidden">
                <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-sky-400/30 to-transparent pointer-events-none" />
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider font-mono">
                      Flight Operational Status
                    </span>
                    <span
                      className={`px-3 py-0.5 rounded-full text-[11px] font-mono font-semibold border ${
                        flightStatusData.status_data_source === 'LIVE'
                          ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30 shadow-[0_0_10px_rgba(16,185,129,0.2)]'
                          : 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                      }`}
                    >
                      {flightStatusData.status_data_source} DATA
                    </span>
                  </div>

                  <div className="mt-4 flex items-baseline justify-between">
                    <div>
                      <h2 className="text-3xl font-black text-white font-mono tracking-tight font-display">
                        {flightStatusData.flight_number}
                      </h2>
                      <p className="text-xs text-slate-400 font-sans mt-0.5">{flightStatusData.carrier}</p>
                    </div>
                    <div className="text-right">
                      <span className="inline-block px-3 py-1 rounded-xl text-xs font-mono font-bold uppercase bg-[#04060d] text-sky-300 border border-white/[0.08]">
                        {flightStatusData.status_record?.status || 'SCHEDULED'}
                      </span>
                      <p className="text-xs text-slate-400 mt-1">
                        Delay: {flightStatusData.status_record?.delay_minutes ?? 0} mins
                      </p>
                    </div>
                  </div>

                  {/* Route Visualizer */}
                  <div className="mt-6 flex items-center justify-between p-3.5 bg-slate-950/70 rounded-xl border border-slate-800/80">
                    <div className="text-center">
                      <p className="text-xl font-bold text-white font-mono">{flightStatusData.origin}</p>
                      <p className="text-xs text-slate-400">Departure</p>
                    </div>
                    <div className="flex-1 flex items-center justify-center px-4">
                      <div className="h-0.5 bg-slate-700 flex-1"></div>
                      <Plane className="w-4 h-4 text-cyan-400 mx-2 transform rotate-90" />
                      <div className="h-0.5 bg-slate-700 flex-1"></div>
                    </div>
                    <div className="text-center">
                      <p className="text-xl font-bold text-white font-mono">{flightStatusData.destination}</p>
                      <p className="text-xs text-slate-400">Arrival</p>
                    </div>
                  </div>

                  {/* Telemetry info */}
                  {flightStatusData.status_record?.position && (
                    <div className="mt-4 p-3 bg-slate-950/40 rounded-xl border border-slate-800/50 text-xs font-mono text-slate-300 space-y-1">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Coordinates:</span>
                        <span>
                          Lat {flightStatusData.status_record.position.latitude?.toFixed(3)}, Lon{' '}
                          {flightStatusData.status_record.position.longitude?.toFixed(3)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Altitude / Speed:</span>
                        <span>
                          {flightStatusData.status_record.position.altitude_ft?.toLocaleString()} ft |{' '}
                          {flightStatusData.status_record.position.velocity_kts} kts
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                <div className="mt-5 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500 flex items-center justify-between">
                  <span>Provider: {flightStatusData.status_provider}</span>
                  <span>{flightStatusData.status_data_source === 'MOCK' ? 'Synthetic Fallback' : 'Live ADS-B Radar'}</span>
                </div>
              </div>

              {/* Card 2: ML Delay Probability & Visual Gauge */}
              <div className="bg-[#070b16]/80 rounded-3xl border border-white/[0.08] p-6 flex flex-col justify-between backdrop-blur-2xl shadow-glass-card hover:border-white/20 transition-all relative overflow-hidden">
                <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-purple-400/30 to-transparent pointer-events-none" />
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider font-mono">
                      Machine Learning Delay Risk
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-purple-500/15 text-purple-300 border border-purple-500/30 shadow-[0_0_10px_rgba(168,85,247,0.2)]">
                      PREDICTED
                    </span>
                  </div>

                  {/* Probability Gauge */}
                  <div className="mt-5 text-center">
                    <div className="inline-block relative">
                      <div
                        className={`text-5xl font-black font-mono tracking-tight font-display ${getProbabilityColor(
                          flightStatusData.prediction?.delay_probability ?? 0.25
                        )}`}
                      >
                        <CountUpNumber
                          value={Math.round((flightStatusData.prediction?.delay_probability ?? 0.25) * 100)}
                          duration={0.8}
                          suffix="%"
                        />
                      </div>
                      <p className="text-sm font-semibold text-slate-200 mt-1 font-display">
                        {flightStatusData.prediction?.predicted_class ?? 'On Time'}
                      </p>
                    </div>

                    {/* Progress Track */}
                    <div className="mt-4 w-full bg-[#04060d] h-3 rounded-full overflow-hidden p-0.5 border border-white/[0.08]">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${
                          (flightStatusData.prediction?.delay_probability ?? 0.25) >= 0.50
                            ? 'bg-gradient-to-r from-amber-500 to-rose-500 shadow-[0_0_12px_rgba(244,63,94,0.4)]'
                            : 'bg-gradient-to-r from-cyan-500 to-emerald-500 shadow-[0_0_12px_rgba(14,165,233,0.4)]'
                        }`}
                        style={{
                          width: `${Math.min(
                            100,
                            Math.max(5, (flightStatusData.prediction?.delay_probability ?? 0.25) * 100)
                          )}%`
                        }}
                      ></div>
                    </div>
                  </div>

                  {/* Calibrated Uncertainty Disclaimer */}
                  <div className="mt-5 p-3 rounded-2xl bg-[#04060d]/80 border border-white/[0.08] text-[11px] text-slate-400 space-y-1">
                    <div className="flex items-center gap-1.5 font-semibold text-slate-300">
                      <Info className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                      Calibrated Statistical Forecast
                    </div>
                    <p>
                      Predicted probability derived from Stage 4 Random Forest trained on U.S. DOT BTS flight records + NOAA surface weather. Operational outcomes remain subject to tactical ATC decisions.
                    </p>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-white/[0.08] text-[11px] text-slate-500 flex items-center justify-between font-mono">
                  <span>Model: {flightStatusData.prediction?.model_name || 'Random Forest'}</span>
                  <span>Target: Dep Delay &ge; 15 mins</span>
                </div>
                <div className="mt-2 pt-2 border-t border-white/[0.06] flex justify-end">
                  <button
                    onClick={() => setActiveTab('benchmarks')}
                    className="text-xs text-sky-400 hover:text-sky-300 font-semibold inline-flex items-center gap-1.5 transition-colors group cursor-pointer"
                  >
                    <span>ROC-AUC 0.6929 • View Precision, Recall & F1 Benchmarks</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </div>
              </div>

              {/* Card 3: SHAP Feature Attributions & Weather Intelligence */}
              <div className="bg-[#070b16]/80 rounded-3xl border border-white/[0.08] p-6 flex flex-col justify-between backdrop-blur-2xl shadow-glass-card hover:border-white/20 transition-all relative overflow-hidden">
                <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-sky-400/30 to-transparent pointer-events-none" />
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider font-mono">
                      Model Factors (TreeSHAP)
                    </span>
                    <span className="text-xs text-sky-400 font-medium font-mono">Local Explanations</span>
                  </div>

                  {/* Compliant Non-Causal Framing */}
                  <p className="text-xs text-slate-400 mt-2 italic">
                    "These features contributed most to the model's prediction."
                  </p>

                  {/* Top Features List */}
                  <div className="mt-3 space-y-2">
                    {flightStatusData.prediction?.explanation && flightStatusData.prediction.explanation.length > 0 ? (
                      flightStatusData.prediction.explanation.slice(0, 4).map((item, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-2.5 rounded-xl bg-[#04060d]/80 border border-white/[0.08] text-xs font-mono"
                        >
                          <span className="text-slate-300 truncate max-w-[180px]">{item.feature}</span>
                          <span
                            className={
                              item.impact.includes('+')
                                ? 'text-rose-400 font-semibold'
                                : 'text-emerald-400 font-semibold'
                            }
                          >
                            {item.impact}
                          </span>
                        </div>
                      ))
                    ) : (
                      <div className="p-3 bg-[#04060d]/80 rounded-xl text-xs text-slate-500 text-center font-mono">
                        Standard operational parameters within baseline limits.
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-white/[0.08] text-[11px] text-slate-500 flex items-center justify-between font-mono">
                  <span>Attribution: TreeSHAP (Lundberg et al.)</span>
                  <span>Non-Causal Evidence</span>
                </div>
              </div>
            </div>
          )}

          {/* Alternative Flight Search & Inventory */}
          <div className="bg-[#070b16]/80 rounded-3xl border border-white/[0.08] p-6 shadow-glass-card backdrop-blur-2xl">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2 font-display">
                  <Search className="w-5 h-5 text-sky-400" />
                  Alternative Flight Inventory & Protection Search
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Search active flight availability, remaining seats, and rebooking options with strict provenance tagging.
                </p>
              </div>

              {/* Corridor Selector */}
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  maxLength={3}
                  value={searchOrigin}
                  onChange={(e) => setSearchOrigin(e.target.value.toUpperCase())}
                  className="w-16 text-center py-2 bg-[#04060d] border border-white/[0.1] rounded-xl text-white font-mono text-sm uppercase focus:outline-none focus:border-sky-400"
                  placeholder="DEL"
                />
                <ArrowRight className="w-4 h-4 text-slate-500" />
                <input
                  type="text"
                  maxLength={3}
                  value={searchDest}
                  onChange={(e) => setSearchDest(e.target.value.toUpperCase())}
                  className="w-16 text-center py-2 bg-[#04060d] border border-white/[0.1] rounded-xl text-white font-mono text-sm uppercase focus:outline-none focus:border-sky-400"
                  placeholder="BOM"
                />
                <button
                  onClick={() => handleSearchInventory(searchOrigin, searchDest)}
                  disabled={searchLoading}
                  className="px-4 py-2 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition shadow-[0_0_15px_rgba(14,165,233,0.3)] cursor-pointer"
                >
                  {searchLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
                  Search
                </button>
              </div>
            </div>

            {/* Results Grid */}
            {searchLoading ? (
              <div className="py-8 text-center text-slate-400 text-sm flex items-center justify-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-sky-400" />
                Scanning live and partner GDS flight inventory...
              </div>
            ) : searchResults.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#04060d]/80 text-slate-400 border-b border-white/[0.08] font-mono">
                    <tr>
                      <th className="py-3 px-3">Flight</th>
                      <th className="py-3 px-3">Carrier</th>
                      <th className="py-3 px-3">Departure</th>
                      <th className="py-3 px-3">Arrival</th>
                      <th className="py-3 px-3">Seats</th>
                      <th className="py-3 px-3">Price</th>
                      <th className="py-3 px-3">Data Source</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.06] font-mono">
                    {searchResults.map((item, idx) => (
                      <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                        <td className="py-3.5 px-3 font-bold text-white">{item.flight_number}</td>
                        <td className="py-3.5 px-3 text-slate-300 font-sans">{item.carrier}</td>
                        <td className="py-3.5 px-3 text-sky-300">
                          {item.departure_time ? item.departure_time.slice(11, 16) : 'N/A'}
                        </td>
                        <td className="py-3.5 px-3 text-slate-300">
                          {item.arrival_time ? item.arrival_time.slice(11, 16) : 'N/A'}
                        </td>
                        <td className="py-3.5 px-3">
                          <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 text-[11px] font-semibold">
                            {item.available_seats} seats
                          </span>
                        </td>
                        <td className="py-3.5 px-3 text-slate-200">₹{item.price_inr?.toLocaleString() || 4500}</td>
                        <td className="py-3.5 px-3">
                          <span
                            className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                              item.data_source === 'LIVE'
                                ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                                : 'bg-[#04060d] text-slate-400 border-white/[0.08]'
                            }`}
                          >
                            {item.data_source}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-8 text-center text-slate-500 text-sm">
                No alternative flights found for corridor {searchOrigin} &rarr; {searchDest}.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: MODEL EVALUATION & BENCHMARK PERFORMANCE                           */}
      {/* ========================================================================= */}
      {activeTab === 'benchmarks' && (
        <div className="space-y-6">
          {/* Header Banner */}
          <div className="bg-[#070b16]/80 rounded-3xl border border-white/[0.08] p-6 shadow-glass-card backdrop-blur-2xl relative overflow-hidden">
            <div className="absolute right-0 top-0 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20"></div>
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative z-10">
              <div>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-0.5 rounded-full text-xs font-mono font-semibold bg-sky-500/15 text-sky-300 border border-sky-400/30 flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-sky-400" />
                    Stage 4 Empirical Evaluation
                  </span>
                  <span className="text-xs text-slate-400 font-mono">
                    82,609 Out-of-Time Test Flights (Oct–Dec 2013)
                  </span>
                </div>
                <h2 className="text-2xl font-extrabold text-white mt-1.5 tracking-tight font-display">
                  Machine Learning Model Benchmarks &amp; Performance Metrics
                </h2>
                <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
                  Rigorous evaluation comparing Baseline (Logistic Regression), Random Forest, and XGBoost on out-of-time holdouts (Months 10–12).
                  Target: Arrival Delay &ge; 15 minutes. Synchronized with NOAA surface weather at scheduled departure time to eliminate data leakage.
                </p>
              </div>

              {/* Threshold Toggle Pill */}
              <div className="flex items-center gap-2 bg-[#04060d] p-1.5 rounded-2xl border border-white/[0.08] self-start lg:self-center shadow-inner">
                <span className="text-xs text-slate-400 font-mono pl-2 hidden sm:inline">Threshold:</span>
                <button
                  onClick={() => setEvalThreshold('0.25')}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer font-display ${
                    evalThreshold === '0.25'
                      ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white shadow-[0_0_15px_rgba(14,165,233,0.3)]'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  0.25 (Calibrated Operational)
                </button>
                <button
                  onClick={() => setEvalThreshold('0.50')}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer font-display ${
                    evalThreshold === '0.50'
                      ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white shadow-[0_0_15px_rgba(14,165,233,0.3)]'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  0.50 (Standard Academic)
                </button>
              </div>
            </div>
          </div>

          {/* 6 Hero Metric KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {/* ROC-AUC */}
            <div className="bg-[#070b16]/80 rounded-3xl border border-white/[0.08] p-4 shadow-glass-card hover:border-white/20 transition-all backdrop-blur-2xl">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1 font-mono">
                <span>ROC-AUC</span>
                <TrendingUp className="w-3.5 h-3.5 text-sky-400" />
              </div>
              <p className="text-2xl font-black font-mono text-sky-300 font-display">0.6929</p>
              <p className="text-[11px] text-slate-400 mt-1">Random Forest (Selected)</p>
              <span className="mt-2 inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                +9.6% vs Baseline
              </span>
            </div>

            {/* PR-AUC */}
            <div className="bg-[#070b16]/80 rounded-3xl border border-white/[0.08] p-4 shadow-glass-card hover:border-white/20 transition-all backdrop-blur-2xl">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1 font-mono">
                <span>PR-AUC</span>
                <Target className="w-3.5 h-3.5 text-purple-400" />
              </div>
              <p className="text-2xl font-black font-mono text-purple-300 font-display">0.4257</p>
              <p className="text-[11px] text-slate-400 mt-1">XGBoost / RF (0.4244)</p>
              <span className="mt-2 inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold bg-purple-500/15 text-purple-300 border border-purple-500/30">
                Prior: 22.97%
              </span>
            </div>

            {/* Accuracy */}
            <div className="bg-[#070b16]/80 rounded-3xl border border-white/[0.08] p-4 shadow-glass-card hover:border-white/20 transition-all backdrop-blur-2xl">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1 font-mono">
                <span>Accuracy</span>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              </div>
              <p className="text-2xl font-black font-mono text-emerald-300 font-display">
                {evalThreshold === '0.25' ? '73.69%' : '77.78%'}
              </p>
              <p className="text-[11px] text-slate-400 mt-1">
                {evalThreshold === '0.25' ? 'Operational @ 0.25' : 'Standard @ 0.50'}
              </p>
              <span className="mt-2 inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold bg-[#04060d] text-slate-400 border border-white/[0.08]">
                82,609 Cases
              </span>
            </div>

            {/* Precision */}
            <div className="bg-[#070b16]/80 rounded-3xl border border-white/[0.08] p-4 shadow-glass-card hover:border-white/20 transition-all backdrop-blur-2xl">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1 font-mono">
                <span>Precision</span>
                <Award className="w-3.5 h-3.5 text-blue-400" />
              </div>
              <p className="text-2xl font-black font-mono text-blue-300 font-display">
                {evalThreshold === '0.25' ? '42.72%' : '68.05%'}
              </p>
              <p className="text-[11px] text-slate-400 mt-1">Positive Pred. Value</p>
              <span className="mt-2 inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-500/15 text-blue-300 border border-blue-500/30">
                {evalThreshold === '0.25' ? '8,111 / 18,987' : '1,165 / 1,712'}
              </span>
            </div>

            {/* Recall (Caught Delays) */}
            <div className="bg-[#070b16]/80 rounded-3xl border border-white/[0.08] p-4 shadow-glass-card hover:border-white/20 transition-all backdrop-blur-2xl">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1 font-mono">
                <span>Recall</span>
                <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
              </div>
              <p className="text-2xl font-black font-mono text-amber-300 font-display">
                {evalThreshold === '0.25' ? '42.75%' : '6.14%'}
              </p>
              <p className="text-[11px] text-slate-400 mt-1">
                {evalThreshold === '0.25' ? '8,111 Caught' : '1,165 Caught'}
              </p>
              <span className="mt-2 inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                {evalThreshold === '0.25' ? '7x Delays Caught' : 'High Miss Rate'}
              </span>
            </div>

            {/* F1 Score */}
            <div className="bg-[#070b16]/80 rounded-3xl border border-white/[0.08] p-4 shadow-glass-card hover:border-white/20 transition-all backdrop-blur-2xl">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1 font-mono">
                <span>F1 Score</span>
                <Sliders className="w-3.5 h-3.5 text-rose-400" />
              </div>
              <p className="text-2xl font-black font-mono text-rose-300 font-display">
                {evalThreshold === '0.25' ? '0.4274' : '0.1126'}
              </p>
              <p className="text-[11px] text-slate-400 mt-1">Harmonic Mean</p>
              <span className="mt-2 inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/15 text-rose-300 border border-rose-500/30">
                {evalThreshold === '0.25' ? 'Optimal Utility' : 'Uncalibrated'}
              </span>
            </div>
          </div>

          {/* Model Comparison Table & Operational Tradeoff */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Table */}
            <div className="lg:col-span-2 bg-[#070b16]/80 rounded-3xl border border-white/[0.08] p-6 shadow-glass-card backdrop-blur-2xl">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2 font-display">
                    <Database className="w-5 h-5 text-sky-400" />
                    Multi-Architecture Benchmark Comparison
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Evaluated across 82,609 flights at {evalThreshold === '0.25' ? 'calibrated threshold = 0.25' : 'standard threshold = 0.50'}
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-white/[0.08] text-slate-400 uppercase tracking-wider font-semibold font-mono">
                      <th className="py-3 px-3">Architecture</th>
                      <th className="py-3 px-3">ROC-AUC</th>
                      <th className="py-3 px-3">PR-AUC</th>
                      <th className="py-3 px-3">Accuracy</th>
                      <th className="py-3 px-3">Precision</th>
                      <th className="py-3 px-3">Recall</th>
                      <th className="py-3 px-3">F1 Score</th>
                      <th className="py-3 px-3">Delays Caught</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.06] font-mono">
                    {/* Baseline */}
                    <tr className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3 px-3 font-sans font-medium text-slate-300">
                        Baseline (Logistic Regression)
                      </td>
                      <td className="py-3 px-3 text-slate-400">0.6321</td>
                      <td className="py-3 px-3 text-slate-400">0.3470</td>
                      <td className="py-3 px-3 text-slate-300">
                        {evalThreshold === '0.25' ? '77.23%' : '77.06%'}
                      </td>
                      <td className="py-3 px-3 text-slate-300">
                        {evalThreshold === '0.25' ? '55.16%' : '92.59%'}
                      </td>
                      <td className="py-3 px-3 text-slate-300">
                        {evalThreshold === '0.25' ? '4.62%' : '0.13%'}
                      </td>
                      <td className="py-3 px-3 text-slate-300">
                        {evalThreshold === '0.25' ? '0.0853' : '0.0026'}
                      </td>
                      <td className="py-3 px-3 text-slate-400">
                        {evalThreshold === '0.25' ? '877' : '25'}
                      </td>
                    </tr>

                    {/* Random Forest (Selected) */}
                    <tr className="bg-sky-500/10 border-l-2 border-sky-400 hover:bg-sky-500/15 transition-colors">
                      <td className="py-3 px-3 font-sans font-bold text-white flex items-center gap-1.5">
                        <Award className="w-3.5 h-3.5 text-sky-400" />
                        Random Forest (100 Trees)
                        <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-sky-500/20 text-sky-300 border border-sky-400/30">
                          SELECTED
                        </span>
                      </td>
                      <td className="py-3 px-3 font-bold text-sky-300">0.6929</td>
                      <td className="py-3 px-3 text-slate-200">0.4244</td>
                      <td className="py-3 px-3 text-slate-200">
                        {evalThreshold === '0.25' ? '73.69%' : '77.78%'}
                      </td>
                      <td className="py-3 px-3 text-slate-200">
                        {evalThreshold === '0.25' ? '42.72%' : '68.05%'}
                      </td>
                      <td className="py-3 px-3 font-bold text-amber-300">
                        {evalThreshold === '0.25' ? '42.75%' : '6.14%'}
                      </td>
                      <td className="py-3 px-3 font-bold text-rose-300">
                        {evalThreshold === '0.25' ? '0.4274' : '0.1126'}
                      </td>
                      <td className="py-3 px-3 font-bold text-emerald-300">
                        {evalThreshold === '0.25' ? '8,111' : '1,165'}
                      </td>
                    </tr>

                    {/* XGBoost */}
                    <tr className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3 px-3 font-sans font-medium text-slate-300">
                        XGBoost (150 Trees)
                      </td>
                      <td className="py-3 px-3 text-slate-300">0.6876</td>
                      <td className="py-3 px-3 font-bold text-purple-300">0.4257</td>
                      <td className="py-3 px-3 text-slate-300">
                        {evalThreshold === '0.25' ? '76.77%' : '77.98%'}
                      </td>
                      <td className="py-3 px-3 text-slate-300">
                        {evalThreshold === '0.25' ? '49.07%' : '65.89%'}
                      </td>
                      <td className="py-3 px-3 text-slate-300">
                        {evalThreshold === '0.25' ? '30.88%' : '8.54%'}
                      </td>
                      <td className="py-3 px-3 text-slate-300">
                        {evalThreshold === '0.25' ? '0.3791' : '0.1513'}
                      </td>
                      <td className="py-3 px-3 text-slate-400">
                        {evalThreshold === '0.25' ? '5,859' : '1,621'}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Operational Rationale Callout */}
              <div className="mt-4 p-3.5 bg-[#04060d]/80 rounded-2xl border border-white/[0.08] text-xs text-slate-400 space-y-1">
                <p className="font-semibold text-slate-200 font-display">
                  Why Random Forest Was Selected for Production:
                </p>
                <p className="leading-relaxed">
                  In airline disruption management, missing a delayed flight (False Negative) leaves passengers stranded without proactive rebooking. 
                  At the calibrated operational threshold (0.25), Random Forest captures <strong className="text-amber-300">8,111 delayed flights (42.75% recall)</strong>, 
                  compared to 5,859 for XGBoost and only 877 for Baseline, achieving the highest operational F1 score (0.4274).
                </p>
              </div>
            </div>

            {/* Confusion Matrix Card */}
            <div className="bg-[#070b16]/80 rounded-3xl border border-white/[0.08] p-6 shadow-glass-card backdrop-blur-2xl flex flex-col justify-between">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-1 font-display">
                  <Sliders className="w-5 h-5 text-sky-400" />
                  Confusion Matrix (Random Forest)
                </h3>
                <p className="text-xs text-slate-400 mb-4 font-mono">
                  Holdout: 82,609 flights @ threshold = {evalThreshold}
                </p>

                {/* 2x2 Matrix */}
                <div className="grid grid-cols-2 gap-2 text-center font-mono">
                  {/* True Negatives */}
                  <div className="bg-[#04060d] p-3 rounded-2xl border border-emerald-500/30 shadow-[0_0_10px_rgba(16,185,129,0.1)]">
                    <p className="text-[10px] text-slate-400 uppercase tracking-wider font-sans">True Negatives</p>
                    <p className="text-xl font-bold text-emerald-400 mt-1 font-display">
                      {evalThreshold === '0.25' ? '52,761' : '63,090'}
                    </p>
                    <p className="text-[10px] text-slate-400 mt-0.5">Correct On-Time</p>
                  </div>

                  {/* False Positives */}
                  <div className="bg-[#04060d] p-3 rounded-2xl border border-amber-500/30 shadow-[0_0_10px_rgba(245,158,11,0.1)]">
                    <p className="text-[10px] text-slate-400 uppercase tracking-wider font-sans">False Positives</p>
                    <p className="text-xl font-bold text-amber-400 mt-1 font-display">
                      {evalThreshold === '0.25' ? '10,876' : '547'}
                    </p>
                    <p className="text-[10px] text-slate-400 mt-0.5">False Alarms</p>
                  </div>

                  {/* False Negatives */}
                  <div className="bg-[#04060d] p-3 rounded-2xl border border-rose-500/30 shadow-[0_0_10px_rgba(244,63,94,0.1)]">
                    <p className="text-[10px] text-slate-400 uppercase tracking-wider font-sans">False Negatives</p>
                    <p className="text-xl font-bold text-rose-400 mt-1 font-display">
                      {evalThreshold === '0.25' ? '10,861' : '17,807'}
                    </p>
                    <p className="text-[10px] text-slate-400 mt-0.5">Missed Delays</p>
                  </div>

                  {/* True Positives */}
                  <div className="bg-[#04060d] p-3 rounded-2xl border border-sky-500/30 shadow-[0_0_10px_rgba(14,165,233,0.1)]">
                    <p className="text-[10px] text-slate-400 uppercase tracking-wider font-sans">True Positives</p>
                    <p className="text-xl font-bold text-sky-400 mt-1 font-display">
                      {evalThreshold === '0.25' ? '8,111' : '1,165'}
                    </p>
                    <p className="text-[10px] text-slate-400 mt-0.5">Caught Delays</p>
                  </div>
                </div>

                <div className="mt-4 space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-white/[0.06]">
                    <span className="text-slate-400">Specificity (True Negative Rate):</span>
                    <span className="font-mono text-white font-semibold">
                      {evalThreshold === '0.25' ? '82.91%' : '99.14%'}
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/[0.06]">
                    <span className="text-slate-400">Sensitivity (True Positive Rate):</span>
                    <span className="font-mono text-sky-300 font-semibold">
                      {evalThreshold === '0.25' ? '42.75%' : '6.14%'}
                    </span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Class Base Rate (Delayed):</span>
                    <span className="font-mono text-slate-300">22.97%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: AEROAI UNIFIED AGENT CHAT                                          */}
      {/* ========================================================================= */}
      {activeTab === 'agent' && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Chat Stream */}
          <div className="lg:col-span-3 bg-[#070b16]/80 rounded-3xl border border-white/[0.08] flex flex-col h-[700px] shadow-glass-card overflow-hidden backdrop-blur-2xl">
            {/* Chat Header */}
            <div className="p-4 border-b border-white/[0.08] bg-[#04060d]/60 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-[0_0_15px_rgba(14,165,233,0.3)]">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2 font-display">
                    AeroAI Unified Agent
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  </h3>
                  <p className="text-[11px] text-slate-400 font-sans">
                    Selective dynamic tool router • 5 integrated capabilities
                  </p>
                </div>
              </div>
              <button
                onClick={() =>
                  setMessages([
                    {
                      id: 'welcome-reset',
                      role: 'assistant',
                      content: 'Conversation history reset. How can I assist you with flights, delay predictions, or regulatory policies?',
                      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                    }
                  ])
                }
                className="text-xs text-slate-400 hover:text-white px-3 py-1.5 rounded-xl bg-[#04060d] border border-white/[0.08] hover:border-white/20 transition cursor-pointer font-mono"
              >
                Clear Chat
              </button>
            </div>

            {/* Messages Scroll Area */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-3xl p-4 sm:p-5 text-sm leading-relaxed backdrop-blur-xl ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white rounded-br-none shadow-[0_0_20px_rgba(14,165,233,0.3)]'
                        : 'bg-[#04060d]/90 border border-white/[0.08] text-slate-200 rounded-bl-none shadow-glass-card'
                    }`}
                  >
                    {/* Tool Invocation Chips */}
                    {msg.selected_tools && msg.selected_tools.length > 0 && (
                      <div className="mb-3 pb-2 border-b border-white/[0.08] flex flex-wrap items-center gap-1.5">
                        <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider font-mono">
                          Active Tools:
                        </span>
                        {msg.selected_tools.map((t) => (
                          <span
                            key={t}
                            className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-sky-500/15 text-sky-300 border border-sky-400/30"
                          >
                            {t}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Pre-formatted Response Text */}
                    <div className="whitespace-pre-wrap font-sans text-[13.5px] leading-relaxed">
                      {msg.content}
                    </div>

                    {/* Rich Structured Sections Renderer */}
                    {msg.sections?.policy_information?.citations &&
                      msg.sections.policy_information.citations.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-white/[0.08]">
                          <p className="text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1">
                            <FileText className="w-3.5 h-3.5 text-sky-400" />
                            Grounded Regulatory Citations:
                          </p>
                          <div className="flex flex-wrap gap-1.5">
                            {msg.sections.policy_information.citations.map((c, cIdx) => (
                              <button
                                key={cIdx}
                                onClick={() => setSelectedCitationDoc(c)}
                                className="px-2.5 py-1 rounded-xl bg-[#070b16] hover:bg-white/[0.05] border border-white/[0.1] text-[11px] text-sky-300 font-mono flex items-center gap-1 transition-all cursor-pointer shadow-sm hover:border-sky-400/40"
                              >
                                {c.document_title} § {c.section}
                                <ExternalLink className="w-2.5 h-2.5" />
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                  </div>
                  <span className="text-[10px] text-slate-500 mt-1 px-1 font-mono">
                    {msg.timestamp} {msg.duration_ms ? `• ${msg.duration_ms.toFixed(0)}ms` : ''}
                  </span>
                </div>
              ))}

              {agentLoading && (
                <div className="flex items-center gap-3 p-4 bg-[#04060d]/80 rounded-2xl border border-white/[0.08] max-w-sm backdrop-blur-xl">
                  <RefreshCw className="w-4 h-4 animate-spin text-sky-400" />
                  <span className="text-xs text-slate-400 font-mono animate-pulse">
                    Routing tools &amp; consulting evidence...
                  </span>
                </div>
              )}
            </div>

            {/* Input Bar */}
            <div className="p-4 border-t border-white/[0.08] bg-[#04060d]/80 backdrop-blur-xl">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendAgentQuery();
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  value={inputPrompt}
                  onChange={(e) => setInputPrompt(e.target.value)}
                  placeholder="Ask AeroAI (e.g., 'Will AI202 be delayed?', 'Can I get a refund for a 4hr delay?')"
                  className="flex-1 bg-[#070b16] border border-white/[0.1] rounded-2xl px-4 py-2.5 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-sky-400 focus:shadow-[0_0_15px_rgba(56,189,248,0.25)] transition"
                />
                <button
                  type="submit"
                  disabled={agentLoading || !inputPrompt.trim()}
                  className="px-5 py-2.5 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 disabled:opacity-40 text-white font-semibold rounded-2xl text-sm flex items-center gap-1.5 transition shadow-[0_0_15px_rgba(14,165,233,0.3)] cursor-pointer font-display"
                >
                  <Send className="w-4 h-4" />
                  Ask
                </button>
              </form>
            </div>
          </div>

          {/* Right Sidebar: Suggested Questions & Regulatory Knowledge */}
          <div className="space-y-4">
            <div className="bg-[#070b16]/80 rounded-3xl border border-white/[0.08] p-5 shadow-glass-card backdrop-blur-2xl">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-1.5 font-mono">
                <Sparkles className="w-3.5 h-3.5 text-sky-400" />
                Suggested Inquiries
              </h4>
              <div className="space-y-2">
                {SUGGESTED_AGENT_PROMPTS.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendAgentQuery(prompt)}
                    className="w-full text-left p-3 rounded-2xl bg-[#04060d]/80 hover:bg-white/[0.05] border border-white/[0.08] hover:border-sky-400/30 text-xs text-slate-300 hover:text-white transition-all leading-snug cursor-pointer font-sans"
                  >
                    "{prompt}"
                  </button>
                ))}
              </div>
            </div>

            {/* Evidence Modal / Popover */}
            {selectedCitationDoc && (
              <div className="bg-[#070b16]/95 rounded-3xl border border-sky-400/40 p-5 shadow-[0_0_25px_rgba(56,189,248,0.15)] space-y-3 backdrop-blur-2xl">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-sky-300 uppercase tracking-wider flex items-center gap-1.5 font-mono">
                    <ShieldCheck className="w-4 h-4 text-sky-400" />
                    Regulatory Evidence
                  </span>
                  <button
                    onClick={() => setSelectedCitationDoc(null)}
                    className="text-xs text-slate-400 hover:text-white cursor-pointer font-mono"
                  >
                    Close
                  </button>
                </div>
                <div className="p-3.5 bg-[#04060d] rounded-2xl border border-white/[0.08] text-xs space-y-1.5 font-mono text-slate-300">
                  <p className="font-bold text-white font-sans">{selectedCitationDoc.document_title}</p>
                  <p className="text-[11px] text-slate-400">
                    Regulator: {selectedCitationDoc.regulator} ({selectedCitationDoc.region})
                  </p>
                  <p className="text-[11px] text-slate-400">Section: {selectedCitationDoc.section}</p>
                  {selectedCitationDoc.page_number && (
                    <p className="text-[11px] text-slate-400">Page: {selectedCitationDoc.page_number}</p>
                  )}
                  {selectedCitationDoc.quote && (
                    <blockquote className="mt-2 pl-3 border-l-2 border-sky-400 italic text-[11px] text-slate-300 font-sans">
                      "{selectedCitationDoc.quote}"
                    </blockquote>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default AeroAIFlightIntelligenceView;
