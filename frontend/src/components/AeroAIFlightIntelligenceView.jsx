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
  { code: 'AI202', label: 'AI202', carrier: 'Air India', desc: 'Domestic Trunk Route' },
  { code: 'UK981', label: 'UK981', carrier: 'Vistara', desc: 'Airborne Telemetry' },
  { code: '6E205', label: '6E205', carrier: 'IndiGo', desc: 'Golden Triangle' },
  { code: 'BA142', label: 'BA142', carrier: 'British Airways', desc: 'Transatlantic Long-Haul' },
  { code: 'DL450', label: 'DL450', carrier: 'Delta Air Lines', desc: 'U.S. Transcontinental' },
];

const SUGGESTED_AGENT_PROMPTS = [
  'Will flight AI202 be delayed?',
  'If my flight is delayed by 4 hours, can I get a refund under DGCA rules?',
  'My flight tomorrow AI202 has high delay risk. What should I do and what are my rights?',
  'Find alternative flights from DEL to BOM',
  'What is the checked baggage allowance on Air India?'
];

export function AeroAIFlightIntelligenceView() {
  const [activeTab, setActiveTab] = useState('intelligence'); // 'intelligence' | 'benchmarks' | 'agent'
  
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
          content: 'I encountered an issue coordinating tools for this request. Please verify your query or try again.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setAgentLoading(false);
    }
  };

  return (
    <div className="space-y-6 sm:space-y-8 w-full">
      {/* Top Action Bar & Hub Header - Professional Aviation Intelligence */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 sm:gap-6">
        <div className="flex flex-col gap-2 max-w-3xl">
          <div className="flex flex-wrap items-center gap-2 mb-0.5">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-surface-container-high/90 border border-primary/30 text-primary text-[10px] sm:text-[11px] font-label-caps tracking-wider shadow-sm font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-primary-container animate-pulse" />
              Unified Flight Intelligence
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded-md bg-surface-container-low border border-surface-container-high text-on-surface-variant text-[10px] sm:text-[11px] font-label-caps tracking-wider font-semibold">
              Stage 7 Agent Active
            </span>
          </div>

          <h1 className="font-headline-md text-2xl sm:text-3xl lg:text-4xl font-extrabold text-on-surface tracking-tight bg-gradient-to-r from-on-surface via-primary to-primary-container bg-clip-text text-transparent">
            AeroAI Flight Intelligence Hub
          </h1>
          <p className="text-xs sm:text-sm text-on-surface-variant/90 max-w-2xl font-normal leading-relaxed">
            Agentic platform combining flight-delay prediction, weather intelligence, explainable ML, travel-policy RAG, and flight telemetry.
          </p>
        </div>

        {/* Segmented Viewport Switcher - Spacious & Intentional */}
        <div className="inline-flex items-center flex-wrap p-1.5 rounded-xl bg-surface-container-low/90 backdrop-blur-md border border-surface-container-high shadow-sm gap-2 shrink-0 self-start lg:self-auto">
          <button
            onClick={() => setActiveTab('intelligence')}
            className={`flex items-center gap-2 px-3.5 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all cursor-pointer h-9 sm:h-9.5 ${
              activeTab === 'intelligence'
                ? 'bg-surface-container-high text-primary-container shadow-sm border border-primary/20'
                : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/50'
            }`}
            type="button"
          >
            <Plane className="w-4 h-4" />
            <span className="leading-none text-left">Flight Radar &amp; Predictor</span>
          </button>
          <button
            onClick={() => setActiveTab('benchmarks')}
            className={`flex items-center gap-2 px-3.5 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all cursor-pointer h-9 sm:h-9.5 ${
              activeTab === 'benchmarks'
                ? 'bg-surface-container-high text-primary-container shadow-sm border border-primary/20'
                : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/50'
            }`}
            type="button"
          >
            <BarChart3 className="w-4 h-4" />
            <span className="leading-none text-left">Model Benchmarks &amp; Metrics</span>
          </button>
          <button
            onClick={() => setActiveTab('agent')}
            className={`flex items-center gap-2 px-3.5 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all cursor-pointer h-9 sm:h-9.5 ${
              activeTab === 'agent'
                ? 'bg-surface-container-high text-primary-container shadow-sm border border-primary/20'
                : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/50'
            }`}
            type="button"
          >
            <Bot className="w-4 h-4" />
            <span className="leading-none text-left">AeroAI Agent</span>
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: FLIGHT RADAR & DELAY PREDICTOR                                     */}
      {/* ========================================================================= */}
      {activeTab === 'intelligence' && (
        <div className="space-y-6 sm:space-y-8">
          {/* Search, Filter & Quick Presets Toolbar */}
          <div className="w-full p-4 sm:p-5 rounded-xl bg-surface-container-low/90 backdrop-blur-md border border-surface-container-high shadow-sm flex flex-col xl:flex-row items-stretch xl:items-center justify-between gap-4 xl:gap-6">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleLookupFlight(flightNumberInput);
              }}
              className="flex items-center flex-1 max-w-xl gap-3"
            >
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-outline" />
                <input
                  type="text"
                  value={flightNumberInput}
                  onChange={(e) => setFlightNumberInput(e.target.value.toUpperCase())}
                  placeholder="Search flight code (e.g. AI202)..."
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-surface-container-lowest text-on-surface placeholder:text-outline/60 focus:outline-none focus:ring-2 focus:ring-primary-container border border-surface-container-high font-mono text-xs sm:text-sm tracking-wide transition-all h-10"
                />
              </div>
              <button
                type="submit"
                disabled={flightLoading}
                className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-primary-container to-primary-fixed-dim text-on-primary text-xs sm:text-sm font-bold hover:brightness-110 active:scale-[0.98] transition-all shadow-md shrink-0 cursor-pointer disabled:opacity-50 h-10"
              >
                {flightLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Plane className="w-4 h-4" />}
                <span>Inspect</span>
              </button>
            </form>

            {/* Quick Preset Pills */}
            <div className="flex items-center flex-wrap gap-2 text-xs font-sans xl:pl-6 xl:border-l xl:border-surface-container-high/60">
              <span className="text-on-surface-variant font-label-caps text-[11px] uppercase mr-1.5 tracking-wider font-semibold whitespace-nowrap">
                Quick Presets:
              </span>
              {SAMPLE_FLIGHTS.map((sf) => (
                <button
                  key={sf.code}
                  onClick={() => {
                    setFlightNumberInput(sf.code);
                    handleLookupFlight(sf.code);
                  }}
                  className={`preset-btn min-w-[70px] justify-center px-3.5 py-1.5 rounded-lg font-mono text-xs font-bold transition-all hover:scale-105 cursor-pointer h-8 flex items-center shadow-sm ${
                    flightNumberInput === sf.code
                      ? 'bg-surface-container-high text-primary-container border border-primary/40'
                      : 'bg-surface-container border border-surface-container-high text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high'
                  }`}
                  type="button"
                >
                  {sf.code}
                </button>
              ))}
            </div>
          </div>

          {/* Error Banner */}
          {flightError && (
            <div className="p-4 sm:p-4.5 rounded-xl bg-surface-container-low border border-error/40 text-error text-xs sm:text-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4 backdrop-blur-md shadow-sm">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-error shrink-0" />
                <span className="font-medium leading-relaxed">{flightError}</span>
              </div>
              <button
                onClick={() => handleLookupFlight(flightNumberInput)}
                className="px-4 py-2 rounded-lg bg-error-container text-on-error-container font-bold transition hover:brightness-110 cursor-pointer text-xs h-9 shrink-0 shadow-sm flex items-center gap-2"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Retry</span>
              </button>
            </div>
          )}

          {/* Loading Skeleton */}
          {flightLoading && !flightStatusData && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="h-56 bg-surface-container-low/70 rounded-xl border border-surface-container-high/60 shimmer-wave" />
              <div className="h-56 bg-surface-container-low/70 rounded-xl border border-surface-container-high/60 shimmer-wave" />
              <div className="h-56 bg-surface-container-low/70 rounded-xl border border-surface-container-high/60 shimmer-wave" />
            </div>
          )}

          {/* Main Analysis 3-Column Glass Bento Grid - Professional Aviation Dashboard */}
          {flightStatusData && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 sm:gap-6 items-stretch">
              {/* Card 1: Operational Status */}
              <div className="flex flex-col justify-between p-5 sm:p-6 rounded-xl bg-surface-container-low/90 backdrop-blur-md border border-surface-container-high shadow-sm relative overflow-hidden group hover:border-primary-container/40 transition-all">
                <div className="absolute -right-6 -top-6 w-28 h-28 bg-primary-container/5 rounded-full blur-xl group-hover:bg-primary-container/10 transition-all pointer-events-none" />
                
                <div className="flex flex-col gap-4 relative z-10">
                  <div className="flex items-center justify-between">
                    <span className="font-label-caps text-[11px] uppercase tracking-wider text-outline font-semibold">
                      Flight Operational Status
                    </span>
                    <span className="px-2.5 py-1 rounded-md bg-surface-container border border-surface-container-high text-on-surface-variant font-label-caps tracking-wider uppercase text-[9px] font-semibold">
                      {flightStatusData.status_data_source === 'LIVE' ? 'Live ADS-B' : 'Mock Data'}
                    </span>
                  </div>

                  <div className="flex items-start justify-between">
                    <div className="flex flex-col">
                      <span className="font-headline-md text-2xl sm:text-3xl font-black text-on-surface tracking-tight">
                        {flightStatusData.flight_number}
                      </span>
                      <span className="text-xs sm:text-sm text-on-surface-variant font-medium mt-0.5">
                        {flightStatusData.carrier}
                      </span>
                    </div>
                    <div className="flex flex-col items-end gap-1.5">
                      <span className="px-2.5 py-1 rounded-md bg-surface-container-high border border-primary-container/30 text-primary-container font-label-caps font-bold tracking-wider uppercase text-[10px] shadow-sm">
                        {flightStatusData.status_record?.status || 'Scheduled'}
                      </span>
                      <span className="text-xs text-on-surface-variant font-mono">
                        Delay: {flightStatusData.status_record?.delay_minutes ?? 0} mins
                      </span>
                    </div>
                  </div>

                  {/* Tactile Air Vector Visualizer */}
                  <div className="py-3 px-4 rounded-xl bg-surface-container-lowest/90 border border-surface-container-high/60 flex items-center justify-between gap-3 shadow-inner">
                    <div className="flex flex-col">
                      <span className="text-lg font-bold text-on-surface font-mono">
                        {flightStatusData.origin}
                      </span>
                      <span className="text-[10px] text-outline tracking-wider uppercase font-semibold">
                        Departure
                      </span>
                    </div>
                    <div className="flex-1 flex items-center justify-center relative px-3">
                      <div className="w-full h-[2px] bg-surface-container-highest relative flex items-center justify-center">
                        <span className="text-primary-container bg-surface-container-lowest px-2 py-1 rounded-full border border-primary-container/30 shadow-sm">
                          <Plane className="w-4 h-4 text-primary-container rotate-90" />
                        </span>
                      </div>
                    </div>
                    <div className="flex flex-col items-end">
                      <span className="text-lg font-bold text-on-surface font-mono">
                        {flightStatusData.destination}
                      </span>
                      <span className="text-[10px] text-outline tracking-wider uppercase font-semibold">
                        Arrival
                      </span>
                    </div>
                  </div>

                  {/* Telemetry coordinate box if available */}
                  {flightStatusData.status_record?.position && (
                    <div className="p-3 bg-surface-container-lowest/90 rounded-lg border border-surface-container-high/60 text-[11px] font-mono text-on-surface-variant space-y-1">
                      <div className="flex justify-between">
                        <span className="text-outline">Coordinates:</span>
                        <span>
                          Lat {flightStatusData.status_record.position.latitude?.toFixed(3)}, Lon{' '}
                          {flightStatusData.status_record.position.longitude?.toFixed(3)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-outline">Altitude / Speed:</span>
                        <span>
                          {flightStatusData.status_record.position.altitude_ft?.toLocaleString()} ft |{' '}
                          {flightStatusData.status_record.position.velocity_kts} kts
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                <div className="pt-3.5 mt-3.5 border-t border-surface-container-high/60 flex items-center justify-between text-outline relative z-10 font-mono text-[11px]">
                  <span>Provider: {flightStatusData.status_provider}</span>
                  <span>{flightStatusData.status_data_source === 'LIVE' ? 'Live Telemetry' : 'Synthetic Fallback'}</span>
                </div>
              </div>

              {/* Card 2: ML Delay Risk & Metric Matrix */}
              <div className="flex flex-col justify-between p-5 sm:p-6 rounded-xl bg-surface-container-low/90 backdrop-blur-md border border-surface-container-high shadow-sm relative overflow-hidden group hover:border-primary-container/40 transition-all">
                <div className="absolute -right-6 -top-6 w-28 h-28 bg-secondary/5 rounded-full blur-xl group-hover:bg-secondary/10 transition-all pointer-events-none" />
                
                <div className="flex flex-col gap-4 relative z-10">
                  <div className="flex items-center justify-between">
                    <span className="font-label-caps text-[11px] uppercase tracking-wider text-outline font-semibold">
                      Machine Learning Delay Risk
                    </span>
                    <span className="px-2.5 py-1 rounded-md bg-surface-container-high border border-secondary/30 text-secondary font-label-caps tracking-wider uppercase text-[9px] font-semibold">
                      Predicted
                    </span>
                  </div>

                  {/* Primary Metric Ring / Gauge Display */}
                  <div className="flex flex-col items-center justify-center text-center py-2">
                    <div className="flex items-baseline gap-1">
                      <span className="font-display-lg text-4xl sm:text-5xl font-extrabold text-primary tracking-tight">
                        <CountUpNumber
                          value={Math.round((flightStatusData.prediction?.delay_probability ?? 0.21) * 100)}
                          suffix="%"
                        />
                      </span>
                    </div>
                    <span className="text-xs sm:text-sm text-primary-fixed-dim mt-1 font-bold tracking-wide">
                      {flightStatusData.prediction?.predicted_class || 'Likely On-Time'}
                    </span>

                    {/* Progress channel */}
                    <div className="w-full max-w-xs h-2.5 rounded-full bg-surface-container-lowest mt-4 overflow-hidden p-0.5 border border-surface-container-high shadow-inner">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${
                          (flightStatusData.prediction?.delay_probability ?? 0.21) >= 0.5
                            ? 'bg-gradient-to-r from-amber-400 to-error shadow-sm'
                            : 'bg-gradient-to-r from-primary to-primary-container shadow-sm'
                        }`}
                        style={{
                          width: `${Math.min(
                            100,
                            Math.max(8, (flightStatusData.prediction?.delay_probability ?? 0.21) * 100)
                          )}%`
                        }}
                      />
                    </div>
                  </div>

                  {/* Calibrated Statistical Forecast Callout */}
                  <div className="p-3.5 rounded-xl bg-surface-container-lowest/90 border border-surface-container-high shadow-inner flex gap-3 items-start">
                    <Info className="w-4 h-4 text-primary-container shrink-0 mt-0.5" />
                    <div className="flex flex-col gap-1">
                      <span className="text-xs text-primary font-bold">
                        Calibrated Statistical Forecast
                      </span>
                      <p className="text-[11px] text-on-surface-variant leading-relaxed">
                        Predicted probability derived from Stage 4 Random Forest trained on U.S. DOT BTS flight records + NOAA surface weather. Operational outcomes remain subject to tactical ATC decisions.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col gap-2 pt-3.5 mt-3.5 border-t border-surface-container-high/60 relative z-10">
                  <div className="flex items-center justify-between text-outline font-mono text-[11px]">
                    <span>Model: {flightStatusData.prediction?.model_name || 'Random Forest'}</span>
                    <span>Target: Dep Delay &ge; 15 mins</span>
                  </div>
                  <button
                    onClick={() => setActiveTab('benchmarks')}
                    className="inline-flex items-center justify-between text-xs text-primary hover:text-primary-container transition-colors py-1 group/link font-semibold cursor-pointer text-left"
                  >
                    <span className="group-hover/link:underline">
                      ROC-AUC 0.6929 • View Benchmarks
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover/link:translate-x-1 transition-transform" />
                  </button>
                </div>
              </div>

              {/* Card 3: TreeSHAP Feature Attribution */}
              <div className="flex flex-col justify-between p-5 sm:p-6 rounded-xl bg-surface-container-low/90 backdrop-blur-md border border-surface-container-high shadow-sm relative overflow-hidden group hover:border-primary-container/40 transition-all">
                <div className="absolute -right-6 -top-6 w-28 h-28 bg-primary-container/5 rounded-full blur-xl group-hover:bg-primary-container/10 transition-all pointer-events-none" />
                
                <div className="flex flex-col gap-3.5 relative z-10">
                  <div className="flex items-center justify-between">
                    <span className="font-label-caps text-[11px] uppercase tracking-wider text-outline font-semibold">
                      Model Factors (TreeSHAP)
                    </span>
                    <button
                      onClick={() => setActiveTab('benchmarks')}
                      className="text-primary hover:text-primary-container font-label-caps tracking-wider uppercase transition-colors text-[10px] cursor-pointer font-semibold"
                    >
                      Local Explanations
                    </button>
                  </div>
                  <p className="text-[11px] italic text-on-surface-variant font-light">
                    “These features contributed most to the model’s prediction.”
                  </p>

                  {/* Attribution Factor Horizontal Bars */}
                  <div className="flex flex-col gap-2.5">
                    {flightStatusData.prediction?.explanation && flightStatusData.prediction.explanation.length > 0 ? (
                      flightStatusData.prediction.explanation.slice(0, 4).map((item, idx) => {
                        const isDelay = item.impact.includes('+');
                        const pctMatch = item.impact.match(/([0-9.]+)%/);
                        const pctValue = pctMatch ? parseFloat(pctMatch[1]) : 5;
                        const barWidth = Math.min(100, Math.max(25, pctValue * 8));

                        return (
                          <div
                            key={idx}
                            className="p-2.5 sm:p-3 rounded-lg bg-surface-container-lowest/90 border border-surface-container-high/60 shadow-sm flex flex-col gap-1.5 hover:border-outline/40 transition-all"
                          >
                            <div className="flex items-center justify-between text-xs font-mono">
                              <span className="text-on-surface truncate pr-2 font-medium">
                                {item.feature}
                              </span>
                              <span
                                className={`font-bold shrink-0 ${
                                  isDelay ? 'text-error' : 'text-primary-container'
                                }`}
                              >
                                {item.impact}
                              </span>
                            </div>
                            <div className="flex items-center gap-2.5">
                              <div className="flex-1 h-2 rounded-full bg-surface-container-high overflow-hidden p-0.5">
                                <div
                                  className={`h-full rounded-full ${
                                    isDelay
                                      ? 'bg-error shadow-sm'
                                      : 'bg-primary-container shadow-sm'
                                  }`}
                                  style={{ width: `${barWidth}%` }}
                                />
                              </div>
                              <span
                                className={`text-[9px] shrink-0 font-label-caps uppercase ${
                                  isDelay ? 'text-error' : 'text-primary'
                                }`}
                              >
                                {isDelay ? 'toward Delayed' : 'toward On-Time'}
                              </span>
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="p-4 bg-surface-container-lowest/90 rounded-lg text-xs text-on-surface-variant text-center font-mono border border-surface-container-high/60">
                        Operational parameters within nominal baseline limits.
                      </div>
                    )}
                  </div>
                </div>

                <div className="pt-3.5 mt-3.5 border-t border-surface-container-high/60 flex items-center justify-between text-outline font-mono text-[11px] relative z-10">
                  <span>Attribution: TreeSHAP</span>
                  <span>Non-Causal Evidence</span>
                </div>
              </div>
            </div>
          )}

          {/* Alternative Flight Inventory & Protection Search Section - Spacious & Distinct */}
          <div className="w-full flex flex-col gap-5 p-5 sm:p-6 rounded-xl bg-surface-container-low/90 backdrop-blur-md border border-surface-container-high shadow-sm relative overflow-hidden mt-2">
            {/* Table Header & Route Input Controls */}
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-surface-container-high/60">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-primary-container/10 border border-primary-container/30 flex items-center justify-center text-primary-container shrink-0">
                    <Search className="w-4 h-4 text-primary-container" />
                  </div>
                  <h2 className="font-headline-md text-base sm:text-lg font-bold text-on-surface tracking-tight">
                    Alternative Flight Inventory &amp; Protection Search
                  </h2>
                </div>
                <p className="text-xs sm:text-sm text-on-surface-variant font-normal leading-relaxed">
                  Search active flight availability, remaining seats, and rebooking options with strict provenance tagging.
                </p>
              </div>

              {/* Corridor Search Controls with Clear Gap Between Route Selector and Search Button */}
              <div className="flex items-center flex-wrap gap-3 shrink-0">
                {/* Route Selector Pill */}
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-container-lowest border border-surface-container-high shadow-inner h-9">
                  <span className="text-[10px] text-outline font-label-caps uppercase tracking-wider font-semibold mr-0.5">
                    Route:
                  </span>
                  <input
                    type="text"
                    maxLength={3}
                    value={searchOrigin}
                    onChange={(e) => setSearchOrigin(e.target.value.toUpperCase())}
                    className="w-10 text-center bg-surface-container-high/90 text-primary font-mono text-xs font-bold rounded px-1 py-0.5 border border-surface-container-highest focus:outline-none focus:border-primary-container uppercase"
                    placeholder="DEL"
                  />
                  <ArrowRight className="w-3.5 h-3.5 text-primary-container shrink-0" />
                  <input
                    type="text"
                    maxLength={3}
                    value={searchDest}
                    onChange={(e) => setSearchDest(e.target.value.toUpperCase())}
                    className="w-10 text-center bg-surface-container-high/90 text-primary font-mono text-xs font-bold rounded px-1 py-0.5 border border-surface-container-highest focus:outline-none focus:border-primary-container uppercase"
                    placeholder="BOM"
                  />
                </div>

                {/* Search Button Separated with Distinct Gap */}
                <button
                  onClick={() => handleSearchInventory(searchOrigin, searchDest)}
                  disabled={searchLoading}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-container text-on-primary-container text-xs font-bold hover:brightness-110 active:scale-95 transition-all shadow-sm cursor-pointer disabled:opacity-50 h-9 shrink-0"
                  type="button"
                >
                  {searchLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
                  <span>Search Availability</span>
                </button>
              </div>
            </div>

            {/* Inventory Data Table */}
            {searchLoading ? (
              <div className="py-8 text-center text-on-surface-variant text-xs flex items-center justify-center gap-2.5">
                <RefreshCw className="w-4 h-4 animate-spin text-primary-container" />
                <span>Scanning active airline reservation inventory &amp; GDS seat manifests...</span>
              </div>
            ) : searchResults.length > 0 ? (
              <div className="w-full overflow-x-auto rounded-lg bg-surface-container-lowest border border-surface-container-high/80 shadow-inner">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-container-high/50 text-outline font-label-caps tracking-wider uppercase text-[10px] border-b border-surface-container-high">
                      <th className="py-3 px-4">Flight</th>
                      <th className="py-3 px-4">Carrier</th>
                      <th className="py-3 px-4">Departure</th>
                      <th className="py-3 px-4">Arrival</th>
                      <th className="py-3 px-4">Seats</th>
                      <th className="py-3 px-4">Price</th>
                      <th className="py-3 px-4">Data Source</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-container-high/40 text-xs text-on-surface">
                    {searchResults.map((item, idx) => (
                      <tr key={idx} className="hover:bg-surface-container-high/30 transition-colors group">
                        <td className="py-2.5 px-4 font-mono font-bold text-primary group-hover:translate-x-0.5 transition-transform">
                          {item.flight_number}
                        </td>
                        <td className="py-2.5 px-4 text-on-surface-variant font-medium">
                          {item.carrier}
                        </td>
                        <td className="py-2.5 px-4 font-mono font-bold text-primary-container">
                          {item.departure_time ? item.departure_time.slice(11, 16) : '10:47'}
                        </td>
                        <td className="py-2.5 px-4 font-mono text-on-surface-variant">
                          {item.arrival_time ? item.arrival_time.slice(11, 16) : '12:57'}
                        </td>
                        <td className="py-2.5 px-4">
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-surface-container-high border border-primary/20 text-primary-fixed-dim text-[10px] font-bold shadow-sm">
                            <span className="w-1.5 h-1.5 rounded-full bg-primary-container animate-pulse" />
                            {item.available_seats} seats
                          </span>
                        </td>
                        <td className="py-2.5 px-4 font-mono font-bold text-on-surface">
                          ₹{item.price_inr?.toLocaleString() || 4500}
                        </td>
                        <td className="py-2.5 px-4">
                          <span className="px-2.5 py-0.5 rounded bg-surface-container border border-surface-container-high text-outline font-label-caps uppercase text-[9px] tracking-wider font-semibold">
                            {item.data_source || 'MOCK'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-8 px-4 rounded-lg bg-surface-container-lowest/60 border border-surface-container-high/60 text-center text-on-surface-variant text-xs font-mono flex flex-col items-center justify-center gap-2">
                <Search className="w-5 h-5 text-outline/60" />
                <span>No alternative flights found for corridor {searchOrigin} &rarr; {searchDest}.</span>
                <span className="text-[11px] text-outline">Try searching active trunk corridors like DEL &rarr; BOM, BOM &rarr; BLR, or DEL &rarr; DXB.</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: MODEL EVALUATION & BENCHMARK PERFORMANCE                           */}
      {/* ========================================================================= */}
      {activeTab === 'benchmarks' && (
        <div className="space-y-6 sm:space-y-8">
          {/* Header Banner */}
          <div className="bg-surface-container-low/90 rounded-xl border border-surface-container-high p-5 sm:p-6 shadow-sm backdrop-blur-md relative overflow-hidden">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 sm:gap-6 relative z-10">
              <div className="space-y-1.5 max-w-3xl">
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-surface-container-high border border-primary/30 text-primary text-[10px] sm:text-[11px] font-label-caps tracking-wider shadow-sm font-semibold">
                    <Activity className="w-3.5 h-3.5 text-primary-container" />
                    Stage 4 Empirical Evaluation
                  </span>
                  <span className="text-[11px] text-on-surface-variant font-mono">
                    82,609 Out-of-Time Test Flights (Oct–Dec 2013)
                  </span>
                </div>
                <h2 className="font-headline-md text-xl sm:text-2xl font-bold text-on-surface tracking-tight">
                  Machine Learning Model Benchmarks &amp; Performance Metrics
                </h2>
                <p className="text-xs sm:text-sm text-on-surface-variant font-normal leading-relaxed">
                  Rigorous evaluation comparing Baseline (Logistic Regression), Random Forest, and XGBoost on out-of-time holdouts (Months 10–12).
                  Target: Arrival Delay &ge; 15 minutes. Synchronized with NOAA surface weather at scheduled departure time to eliminate data leakage.
                </p>
              </div>

              {/* Threshold Toggle Pill */}
              <div className="flex items-center gap-2 bg-surface-container-lowest p-1.5 rounded-xl border border-surface-container-high self-start lg:self-center shadow-inner shrink-0">
                <span className="text-[11px] text-outline font-label-caps uppercase pl-2 hidden sm:inline font-semibold">Threshold:</span>
                <button
                  onClick={() => setEvalThreshold('0.25')}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer h-8 ${
                    evalThreshold === '0.25'
                      ? 'bg-surface-container-high text-primary-container shadow-sm border border-primary/30'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  0.25 (Calibrated)
                </button>
                <button
                  onClick={() => setEvalThreshold('0.50')}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer h-8 ${
                    evalThreshold === '0.50'
                      ? 'bg-surface-container-high text-primary-container shadow-sm border border-primary/30'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  0.50 (Standard)
                </button>
              </div>
            </div>
          </div>

          {/* 6 Hero Metric KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5 sm:gap-4">
            {/* ROC-AUC */}
            <div className="bg-surface-container-low/90 rounded-xl border border-surface-container-high p-4 sm:p-4.5 shadow-sm hover:border-primary-container/40 transition-all backdrop-blur-md">
              <div className="flex items-center justify-between text-[10px] text-outline mb-1 font-label-caps uppercase tracking-wider font-semibold">
                <span>ROC-AUC</span>
                <TrendingUp className="w-3.5 h-3.5 text-primary-container" />
              </div>
              <p className="text-xl sm:text-2xl font-black font-mono text-primary font-display">0.6929</p>
              <p className="text-[10px] text-on-surface-variant mt-1">Random Forest</p>
              <span className="mt-2 inline-block px-2 py-0.5 rounded text-[9px] font-bold bg-surface-container-high text-primary-fixed-dim border border-primary/20">
                +9.6% vs Base
              </span>
            </div>

            {/* PR-AUC */}
            <div className="bg-surface-container-low/90 rounded-xl border border-surface-container-high p-4 sm:p-4.5 shadow-sm hover:border-primary-container/40 transition-all backdrop-blur-md">
              <div className="flex items-center justify-between text-[10px] text-outline mb-1 font-label-caps uppercase tracking-wider font-semibold">
                <span>PR-AUC</span>
                <Target className="w-3.5 h-3.5 text-secondary" />
              </div>
              <p className="text-xl sm:text-2xl font-black font-mono text-secondary font-display">0.4257</p>
              <p className="text-[10px] text-on-surface-variant mt-1">XGBoost / RF (0.42)</p>
              <span className="mt-2 inline-block px-2 py-0.5 rounded text-[9px] font-bold bg-surface-container-high text-secondary border border-secondary/20">
                Prior: 22.97%
              </span>
            </div>

            {/* Accuracy */}
            <div className="bg-surface-container-low/90 rounded-xl border border-surface-container-high p-4 sm:p-4.5 shadow-sm hover:border-primary-container/40 transition-all backdrop-blur-md">
              <div className="flex items-center justify-between text-[10px] text-outline mb-1 font-label-caps uppercase tracking-wider font-semibold">
                <span>Accuracy</span>
                <CheckCircle2 className="w-3.5 h-3.5 text-primary-container" />
              </div>
              <p className="text-xl sm:text-2xl font-black font-mono text-primary font-display">
                {evalThreshold === '0.25' ? '73.69%' : '77.78%'}
              </p>
              <p className="text-[10px] text-on-surface-variant mt-1">
                {evalThreshold === '0.25' ? 'Op @ 0.25' : 'Std @ 0.50'}
              </p>
              <span className="mt-2 inline-block px-2 py-0.5 rounded text-[9px] font-mono bg-surface-container text-outline border border-surface-container-high">
                82,609 Cases
              </span>
            </div>

            {/* Precision */}
            <div className="bg-surface-container-low/90 rounded-xl border border-surface-container-high p-4 sm:p-4.5 shadow-sm hover:border-primary-container/40 transition-all backdrop-blur-md">
              <div className="flex items-center justify-between text-[10px] text-outline mb-1 font-label-caps uppercase tracking-wider font-semibold">
                <span>Precision</span>
                <Award className="w-3.5 h-3.5 text-tertiary-fixed-dim" />
              </div>
              <p className="text-xl sm:text-2xl font-black font-mono text-tertiary font-display">
                {evalThreshold === '0.25' ? '42.72%' : '68.05%'}
              </p>
              <p className="text-[10px] text-on-surface-variant mt-1">Random Forest</p>
              <span className="mt-2 inline-block px-2 py-0.5 rounded text-[9px] font-mono bg-surface-container text-on-surface-variant border border-surface-container-high">
                {evalThreshold === '0.25' ? '8.1k / 18.9k' : '1.1k / 1.7k'}
              </span>
            </div>

            {/* Recall */}
            <div className="bg-surface-container-low/90 rounded-xl border border-surface-container-high p-4 sm:p-4.5 shadow-sm hover:border-primary-container/40 transition-all backdrop-blur-md">
              <div className="flex items-center justify-between text-[10px] text-outline mb-1 font-label-caps uppercase tracking-wider font-semibold">
                <span>Recall (Sensitivity)</span>
                <Sliders className="w-3.5 h-3.5 text-primary-container" />
              </div>
              <p className="text-xl sm:text-2xl font-black font-mono text-primary-container font-display">
                {evalThreshold === '0.25' ? '42.75%' : '6.14%'}
              </p>
              <p className="text-[10px] text-on-surface-variant mt-1">
                {evalThreshold === '0.25' ? '8,111 delays caught' : '1,165 delays caught'}
              </p>
              <span className="mt-2 inline-block px-2 py-0.5 rounded text-[9px] font-bold bg-surface-container-high text-primary-fixed-dim border border-primary/20">
                {evalThreshold === '0.25' ? '9.25x recall gain' : 'Baseline 4.62%'}
              </span>
            </div>

            {/* F1 Score */}
            <div className="bg-surface-container-low/90 rounded-xl border border-surface-container-high p-4 sm:p-4.5 shadow-sm hover:border-primary-container/40 transition-all backdrop-blur-md">
              <div className="flex items-center justify-between text-[10px] text-outline mb-1 font-label-caps uppercase tracking-wider font-semibold">
                <span>F1 Score</span>
                <Database className="w-3.5 h-3.5 text-secondary-fixed-dim" />
              </div>
              <p className="text-xl sm:text-2xl font-black font-mono text-secondary font-display">
                {evalThreshold === '0.25' ? '0.4274' : '0.1126'}
              </p>
              <p className="text-[10px] text-on-surface-variant mt-1">Harmonic Mean</p>
              <span className="mt-2 inline-block px-2 py-0.5 rounded text-[9px] font-bold bg-surface-container-high text-secondary border border-secondary/20">
                {evalThreshold === '0.25' ? 'Optimal Balance' : 'Low Sensitivity'}
              </span>
            </div>
          </div>

          {/* Model Comparison Table */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 sm:gap-6">
            <div className="lg:col-span-2 bg-surface-container-low/90 rounded-xl border border-surface-container-high p-5 sm:p-6 shadow-sm backdrop-blur-md flex flex-col justify-between">
              <div>
                <div className="mb-4">
                  <h3 className="text-base sm:text-lg font-bold text-on-surface flex items-center gap-2.5 font-headline-md">
                    <BarChart3 className="w-4 h-4 text-primary-container" />
                    Empirical Model Comparison (Out-of-Time Holdout)
                  </h3>
                  <p className="text-xs text-on-surface-variant mt-1">
                    Evaluated across 82,609 flights at {evalThreshold === '0.25' ? 'calibrated threshold = 0.25' : 'standard threshold = 0.50'}
                  </p>
                </div>

                <div className="overflow-x-auto rounded-lg bg-surface-container-lowest border border-surface-container-high shadow-inner">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-surface-container-high/50 text-outline font-label-caps tracking-wider uppercase text-[10px] border-b border-surface-container-high">
                        <th className="py-2.5 px-3.5">Architecture</th>
                        <th className="py-2.5 px-3.5">ROC-AUC</th>
                        <th className="py-2.5 px-3.5">PR-AUC</th>
                        <th className="py-2.5 px-3.5">Accuracy</th>
                        <th className="py-2.5 px-3.5">Precision</th>
                        <th className="py-2.5 px-3.5">Recall</th>
                        <th className="py-2.5 px-3.5">F1 Score</th>
                        <th className="py-2.5 px-3.5">Delays Caught</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-container-high/40 font-mono text-on-surface">
                      {/* Baseline */}
                      <tr className="hover:bg-surface-container-high/30 transition-colors">
                        <td className="py-2.5 px-3.5 font-sans font-medium text-on-surface-variant">
                          Baseline (Logistic Regression)
                        </td>
                        <td className="py-2.5 px-3.5 text-outline">0.6321</td>
                        <td className="py-2.5 px-3.5 text-outline">0.3470</td>
                        <td className="py-2.5 px-3.5">{evalThreshold === '0.25' ? '77.23%' : '77.06%'}</td>
                        <td className="py-2.5 px-3.5">{evalThreshold === '0.25' ? '55.16%' : '92.59%'}</td>
                        <td className="py-2.5 px-3.5">{evalThreshold === '0.25' ? '4.62%' : '0.13%'}</td>
                        <td className="py-2.5 px-3.5">{evalThreshold === '0.25' ? '0.0853' : '0.0026'}</td>
                        <td className="py-2.5 px-3.5 text-outline">{evalThreshold === '0.25' ? '877' : '25'}</td>
                      </tr>

                      {/* Random Forest (Selected) */}
                      <tr className="bg-surface-container-high/60 border-l-2 border-primary-container hover:bg-surface-container-high transition-colors">
                        <td className="py-2.5 px-3.5 font-sans font-bold text-on-surface flex items-center gap-2">
                          <Award className="w-3.5 h-3.5 text-primary-container" />
                          Random Forest (100 Trees)
                          <span className="px-1.5 py-0.2 rounded text-[8px] font-bold bg-surface-container-lowest text-primary-container border border-primary-container/30 uppercase">
                            SELECTED
                          </span>
                        </td>
                        <td className="py-2.5 px-3.5 font-bold text-primary">0.6929</td>
                        <td className="py-2.5 px-3.5 text-on-surface">0.4244</td>
                        <td className="py-2.5 px-3.5 text-on-surface">{evalThreshold === '0.25' ? '73.69%' : '77.78%'}</td>
                        <td className="py-2.5 px-3.5 text-on-surface">{evalThreshold === '0.25' ? '42.72%' : '68.05%'}</td>
                        <td className="py-2.5 px-3.5 font-bold text-primary-fixed-dim">{evalThreshold === '0.25' ? '42.75%' : '6.14%'}</td>
                        <td className="py-2.5 px-3.5 font-bold text-primary">{evalThreshold === '0.25' ? '0.4274' : '0.1126'}</td>
                        <td className="py-2.5 px-3.5 font-bold text-primary-container">{evalThreshold === '0.25' ? '8,111' : '1,165'}</td>
                      </tr>

                      {/* XGBoost */}
                      <tr className="hover:bg-surface-container-high/30 transition-colors">
                        <td className="py-2.5 px-3.5 font-sans font-medium text-on-surface-variant">
                          XGBoost (150 Trees)
                        </td>
                        <td className="py-2.5 px-3.5 text-on-surface">0.6876</td>
                        <td className="py-2.5 px-3.5 font-bold text-secondary">0.4257</td>
                        <td className="py-2.5 px-3.5">{evalThreshold === '0.25' ? '76.77%' : '77.98%'}</td>
                        <td className="py-2.5 px-3.5">{evalThreshold === '0.25' ? '49.07%' : '65.89%'}</td>
                        <td className="py-2.5 px-3.5">{evalThreshold === '0.25' ? '30.88%' : '8.54%'}</td>
                        <td className="py-2.5 px-3.5">{evalThreshold === '0.25' ? '0.3791' : '0.1513'}</td>
                        <td className="py-2.5 px-3.5 text-outline">{evalThreshold === '0.25' ? '5,859' : '1,621'}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Operational Rationale Callout */}
              <div className="mt-4 p-3.5 bg-surface-container-lowest/90 rounded-xl border border-surface-container-high text-xs text-on-surface-variant space-y-1">
                <p className="font-semibold text-primary font-sans text-xs">
                  Why Random Forest Was Selected for Production:
                </p>
                <p className="leading-relaxed text-[11px]">
                  In airline disruption management, missing a delayed flight (False Negative) leaves passengers stranded without proactive rebooking. 
                  At the calibrated operational threshold (0.25), Random Forest captures <strong className="text-primary-container font-semibold">8,111 delayed flights (42.75% recall)</strong>, 
                  compared to 5,859 for XGBoost and only 877 for Baseline, achieving the highest operational F1 score (0.4274).
                </p>
              </div>
            </div>

            {/* Confusion Matrix Card */}
            <div className="bg-surface-container-low/90 rounded-xl border border-surface-container-high p-5 sm:p-6 shadow-sm backdrop-blur-md flex flex-col justify-between">
              <div>
                <h3 className="text-sm sm:text-base font-bold text-on-surface flex items-center gap-2 mb-1 font-headline-md">
                  <Sliders className="w-4 h-4 text-primary-container" />
                  Confusion Matrix (Random Forest)
                </h3>
                <p className="text-[11px] text-outline mb-4 font-mono">
                  Holdout: 82,609 flights @ threshold = {evalThreshold}
                </p>

                {/* 2x2 Matrix */}
                <div className="grid grid-cols-2 gap-3 text-center font-mono">
                  {/* True Negatives */}
                  <div className="bg-surface-container-lowest p-3 rounded-lg border border-surface-container-high shadow-inner">
                    <p className="text-[9px] text-outline uppercase tracking-wider font-label-caps">True Negatives</p>
                    <p className="text-lg font-bold text-primary mt-1 font-display">
                      {evalThreshold === '0.25' ? '52,761' : '63,090'}
                    </p>
                    <p className="text-[9px] text-on-surface-variant mt-0.5">Correct On-Time</p>
                  </div>

                  {/* False Positives */}
                  <div className="bg-surface-container-lowest p-3 rounded-lg border border-surface-container-high shadow-inner">
                    <p className="text-[9px] text-outline uppercase tracking-wider font-label-caps">False Positives</p>
                    <p className="text-lg font-bold text-amber-300 mt-1 font-display">
                      {evalThreshold === '0.25' ? '10,876' : '547'}
                    </p>
                    <p className="text-[9px] text-on-surface-variant mt-0.5">False Alarms</p>
                  </div>

                  {/* False Negatives */}
                  <div className="bg-surface-container-lowest p-3 rounded-lg border border-surface-container-high shadow-inner">
                    <p className="text-[9px] text-outline uppercase tracking-wider font-label-caps">False Negatives</p>
                    <p className="text-lg font-bold text-error mt-1 font-display">
                      {evalThreshold === '0.25' ? '10,861' : '17,807'}
                    </p>
                    <p className="text-[9px] text-on-surface-variant mt-0.5">Missed Delays</p>
                  </div>

                  {/* True Positives */}
                  <div className="bg-surface-container-lowest p-3 rounded-lg border border-primary-container/30 shadow-sm">
                    <p className="text-[9px] text-primary uppercase tracking-wider font-label-caps font-bold">True Positives</p>
                    <p className="text-lg font-bold text-primary-container mt-1 font-display">
                      {evalThreshold === '0.25' ? '8,111' : '1,165'}
                    </p>
                    <p className="text-[9px] text-primary-fixed-dim mt-0.5">Caught Delays</p>
                  </div>
                </div>

                <div className="mt-4 space-y-1.5 text-xs">
                  <div className="flex justify-between py-1.5 border-b border-surface-container-high/60">
                    <span className="text-on-surface-variant text-[11px]">Specificity (TNR):</span>
                    <span className="font-mono text-on-surface font-semibold text-[11px]">
                      {evalThreshold === '0.25' ? '82.91%' : '99.14%'}
                    </span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-surface-container-high/60">
                    <span className="text-on-surface-variant text-[11px]">Sensitivity (TPR):</span>
                    <span className="font-mono text-primary-container font-semibold text-[11px]">
                      {evalThreshold === '0.25' ? '42.75%' : '6.14%'}
                    </span>
                  </div>
                  <div className="flex justify-between py-1.5">
                    <span className="text-on-surface-variant text-[11px]">Class Base Rate:</span>
                    <span className="font-mono text-outline font-semibold text-[11px]">22.97%</span>
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
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-5 sm:gap-6">
          {/* Main Chat Stream */}
          <div className="lg:col-span-3 bg-surface-container-low/90 rounded-xl border border-surface-container-high flex flex-col h-[560px] shadow-sm overflow-hidden backdrop-blur-md">
            {/* Chat Header */}
            <div className="p-4 sm:p-4.5 border-b border-surface-container-high bg-surface-container-lowest/80 flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-surface-container-high to-surface-container border border-primary-container/30 flex items-center justify-center text-primary-container shadow-sm shrink-0">
                  <Bot className="w-4 h-4 text-primary-container" />
                </div>
                <div>
                  <h3 className="text-xs sm:text-sm font-bold text-on-surface flex items-center gap-2 font-headline-md">
                    AeroAI Agent Multi-Tool Engine
                    <span className="px-2 py-0.5 rounded text-[9px] font-mono bg-surface-container text-primary-container border border-primary/20">
                      RAG + ML Delay + Radar
                    </span>
                  </h3>
                  <p className="text-[11px] text-on-surface-variant mt-0.5">
                    Conversational agent equipped with 5 tools: Policy RAG, ADS-B Radar, BTS ML Delay, METAR Weather, Flight GDS
                  </p>
                </div>
              </div>
              <button
                onClick={() =>
                  setMessages([
                    {
                      id: 'welcome',
                      role: 'assistant',
                      content:
                        'Session restarted. I am ready to analyze flights, verify airline regulations, or simulate delay impact.',
                      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                    }
                  ])
                }
                className="px-3.5 py-1.5 rounded-lg bg-surface-container-high hover:bg-surface-container-highest text-outline hover:text-on-surface text-xs font-semibold border border-surface-container-high transition cursor-pointer h-8 shrink-0"
              >
                Clear History
              </button>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-xl p-3.5 sm:p-4 shadow-sm ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-r from-primary-container to-primary-fixed-dim text-on-primary font-medium'
                        : 'bg-surface-container-lowest border border-surface-container-high text-on-surface'
                    }`}
                  >
                    {/* Tool Badges */}
                    {msg.selected_tools && msg.selected_tools.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5 mb-2.5 pb-2 border-b border-surface-container-high/40">
                        <span className="text-[9px] font-label-caps uppercase text-outline font-semibold">
                          Invoked Engines:
                        </span>
                        {msg.selected_tools.map((t) => (
                          <span
                            key={t}
                            className="px-2 py-0.5 rounded text-[9px] font-mono bg-surface-container-high text-primary-fixed-dim border border-primary/20"
                          >
                            {t}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Content */}
                    <div className="whitespace-pre-wrap font-sans text-xs sm:text-[13px] leading-relaxed">
                      {msg.content}
                    </div>

                    {/* Regulatory Citations */}
                    {msg.sections?.policy_information?.citations &&
                      msg.sections.policy_information.citations.length > 0 && (
                        <div className="mt-3 pt-2.5 border-t border-surface-container-high/40">
                          <p className="text-[11px] font-semibold text-primary mb-1.5 flex items-center gap-1.5">
                            <FileText className="w-3.5 h-3.5 text-primary-container" />
                            Grounded Regulatory Citations:
                          </p>
                          <div className="flex flex-wrap gap-1.5">
                            {msg.sections.policy_information.citations.map((c, cIdx) => (
                              <button
                                key={cIdx}
                                onClick={() => setSelectedCitationDoc(c)}
                                className="px-2.5 py-1 rounded-lg bg-surface-container hover:bg-surface-container-high border border-surface-container-high text-[10px] text-primary font-mono flex items-center gap-1.5 transition-all cursor-pointer shadow-sm hover:border-primary/40"
                              >
                                {c.document_title} • {c.section}
                                <ExternalLink className="w-2.5 h-2.5" />
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                  </div>
                  <span className="text-[9px] text-outline mt-1 px-1 font-mono">
                    {msg.timestamp} {msg.duration_ms ? `• ${msg.duration_ms.toFixed(0)}ms` : ''}
                  </span>
                </div>
              ))}

              {agentLoading && (
                <div className="flex items-center gap-3 p-3.5 bg-surface-container-lowest rounded-xl border border-surface-container-high max-w-sm backdrop-blur-md">
                  <RefreshCw className="w-4 h-4 animate-spin text-primary-container" />
                  <span className="text-xs text-on-surface-variant font-mono animate-pulse">
                    Routing tools &amp; consulting evidence...
                  </span>
                </div>
              )}
            </div>

            {/* Input Bar */}
            <div className="p-3.5 sm:p-4 border-t border-surface-container-high bg-surface-container-lowest/80 backdrop-blur-md">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendAgentQuery();
                }}
                className="flex items-center gap-3"
              >
                <input
                  type="text"
                  value={inputPrompt}
                  onChange={(e) => setInputPrompt(e.target.value)}
                  placeholder="Ask AeroAI (e.g., 'Will AI202 be delayed?', 'Can I get a refund for a 4hr delay?')"
                  className="flex-1 bg-surface-container border border-surface-container-high rounded-lg px-4 py-2.5 text-xs sm:text-sm text-on-surface placeholder:text-outline/60 focus:outline-none focus:ring-2 focus:ring-primary-container transition h-10"
                />
                <button
                  type="submit"
                  disabled={agentLoading || !inputPrompt.trim()}
                  className="px-5 py-2.5 bg-gradient-to-r from-primary-container to-primary-fixed-dim hover:brightness-110 active:scale-[0.98] disabled:opacity-40 text-on-primary text-xs sm:text-sm font-bold rounded-lg flex items-center gap-2 transition shadow-md cursor-pointer h-10"
                >
                  <Send className="w-4 h-4" />
                  <span>Ask</span>
                </button>
              </form>
            </div>
          </div>

          {/* Right Sidebar */}
          <div className="space-y-4">
            <div className="bg-surface-container-low/90 rounded-xl border border-surface-container-high p-4 sm:p-5 shadow-sm backdrop-blur-md">
              <h4 className="text-[11px] font-bold text-outline uppercase tracking-wider mb-3 flex items-center gap-1.5 font-label-caps">
                <Sparkles className="w-3.5 h-3.5 text-primary-container" />
                Suggested Inquiries
              </h4>
              <div className="space-y-2">
                {SUGGESTED_AGENT_PROMPTS.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendAgentQuery(prompt)}
                    className="w-full text-left p-2.5 sm:p-3 rounded-lg bg-surface-container-lowest/90 hover:bg-surface-container-high border border-surface-container-high hover:border-primary/30 text-xs text-on-surface-variant hover:text-on-surface transition-all leading-relaxed cursor-pointer font-sans"
                  >
                    "{prompt}"
                  </button>
                ))}
              </div>
            </div>

            {/* Evidence Modal / Popover */}
            {selectedCitationDoc && (
              <div className="bg-surface-container-low/95 rounded-xl border border-primary-container/40 p-4 sm:p-4.5 shadow-md space-y-3 backdrop-blur-xl">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-primary uppercase tracking-wider flex items-center gap-1.5 font-label-caps">
                    <ShieldCheck className="w-4 h-4 text-primary-container" />
                    Regulatory Evidence
                  </span>
                  <button
                    onClick={() => setSelectedCitationDoc(null)}
                    className="text-xs text-outline hover:text-on-surface cursor-pointer font-mono px-2 py-0.5 rounded hover:bg-surface-container-high transition"
                  >
                    Close
                  </button>
                </div>
                <div className="p-3 bg-surface-container-lowest rounded-lg border border-surface-container-high text-xs space-y-1.5 font-mono text-on-surface-variant">
                  <p className="font-bold text-on-surface font-sans text-xs">{selectedCitationDoc.document_title}</p>
                  <p className="text-[10px] text-outline">
                    Regulator: {selectedCitationDoc.regulator} ({selectedCitationDoc.region})
                  </p>
                  <p className="text-[10px] text-outline">Section: {selectedCitationDoc.section}</p>
                  {selectedCitationDoc.page_number && (
                    <p className="text-[10px] text-outline">Page: {selectedCitationDoc.page_number}</p>
                  )}
                  {selectedCitationDoc.quote && (
                    <blockquote className="mt-2 pl-3 border-l-2 border-primary-container italic text-[11px] text-on-surface font-sans leading-relaxed">
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
