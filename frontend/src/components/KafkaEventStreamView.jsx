import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Radio,
  Zap,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ArrowRight,
  RotateCcw,
  Layers,
  ShieldCheck,
  Terminal,
  Play,
  Trash2,
  CopyCheck,
  Activity,
  Server
} from 'lucide-react';
import { api } from '../services/api';

const EXPECTED_MILESTONES = [
  { label: 'Flight delay detected', topic: 'disruption.detected', agent: 'Disruption API' },
  { label: 'Train connection affected', topic: 'journey.affected', agent: 'Impact Agent' },
  { label: 'Searching alternatives', topic: 'recovery.requested', agent: 'Impact Agent' },
  { label: 'Optimization completed', topic: 'recovery.planned', agent: 'Recovery Agent' },
  { label: 'Train rebooked', topic: 'action.completed', agent: 'Action Agent' },
  { label: 'Hotel updated', topic: 'action.completed', agent: 'Action Agent' },
  { label: 'Traveler notified', topic: 'notification.requested', agent: 'Notification Agent' },
];

export function KafkaEventStreamView() {
  const [wsConnected, setWsConnected] = useState(false);
  const [wsFrames, setWsFrames] = useState([]);
  const [topicsData, setTopicsData] = useState(null);
  const [streamData, setStreamData] = useState(null);
  const [consumersData, setConsumersData] = useState(null);
  const [dlqData, setDlqData] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState('ALL');
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [lastPipelineResult, setLastPipelineResult] = useState(null);
  const [runningMode, setRunningMode] = useState(null);
  const [stepDelayMs, setStepDelayMs] = useState(120);
  const wsRef = useRef(null);

  const fetchBrokerState = async () => {
    try {
      const [tRes, sRes, cRes, dRes] = await Promise.all([
        api.getKafkaTopics(),
        api.getKafkaEventStream(selectedTopic !== 'ALL' ? { topic: selectedTopic } : {}),
        api.getKafkaConsumers(),
        api.getKafkaDlq(),
      ]);
      setTopicsData(tRes);
      setStreamData(sRes);
      setConsumersData(cRes);
      setDlqData(dRes);
      if (!selectedEvent && sRes?.events?.length > 0) {
        setSelectedEvent(sRes.events[0]);
      }
    } catch (err) {
      console.error('Failed to load Kafka state:', err);
    }
  };

  useEffect(() => {
    fetchBrokerState();
  }, [selectedTopic]);

  // Connect to Real-Time WebSocket stream
  useEffect(() => {
    let ws;
    let reconnectTimer;

    const connectWs = () => {
      try {
        const wsUrl = api.getKafkaWebSocketUrl();
        ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setWsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const parsed = JSON.parse(event.data);
            if (parsed.type === 'WS_CONNECTED') {
              if (Array.isArray(parsed.recent_milestones) && parsed.recent_milestones.length > 0) {
                setWsFrames(parsed.recent_milestones.slice().reverse());
              }
            } else if (parsed.type === 'KAFKA_EVENT') {
              setWsFrames((prev) => [parsed, ...prev.slice(0, 79)]);
              setSelectedEvent(parsed);
            }
          } catch (e) {
            console.error('WS frame parse error:', e);
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          reconnectTimer = setTimeout(connectWs, 2500);
        };

        ws.onerror = () => {
          setWsConnected(false);
        };
      } catch (e) {
        console.error('WS connection error:', e);
      }
    };

    connectWs();

    return () => {
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws) ws.close();
    };
  }, []);

  const handleTriggerPipeline = async (mode = 'normal') => {
    setRunningMode(mode);
    try {
      const corrId = `corr-${Date.now().toString().slice(-6)}`;
      const payload = {
        journey_id: 1,
        booking_ref: 'AI-202',
        disruption_type: 'flight_delay',
        delay_minutes: 240,
        correlation_id: corrId,
        step_delay_ms: Number(stepDelayMs) || 0,
        max_retries: 2,
        inject_consumer_failure:
          mode === 'transient_retry'
            ? 'recovery_agent_transient'
            : mode === 'poison_dlq'
            ? 'action_agent_poison_pill'
            : null,
      };
      const res = await api.triggerKafkaDisruptionPipeline(payload);
      setLastPipelineResult(res);
      await fetchBrokerState();
    } catch (err) {
      console.error('Pipeline trigger failed:', err);
    } finally {
      setRunningMode(null);
    }
  };

  const handleTestIdempotentConsumer = async () => {
    setRunningMode('idempotent');
    try {
      const rootEvtId = lastPipelineResult?.root_event_id || 'evt-demo-dup-001';
      const idemKey = lastPipelineResult?.idempotency_key || 'KAFKA-IDEM-DEMO-DUP-001';
      const corrId = lastPipelineResult?.correlation_id || 'corr-idem-demo';

      // Ensure initial event is published if none exists yet
      if (!lastPipelineResult) {
        await api.triggerKafkaDisruptionPipeline({
          journey_id: 1,
          booking_ref: 'AI-202',
          disruption_type: 'flight_delay',
          delay_minutes: 240,
          correlation_id: corrId,
          event_id: rootEvtId,
          idempotency_key: idemKey,
        });
      }

      // Now publish the exact same event_id & idempotency_key again to `disruption.detected`
      await api.publishCustomKafkaEvent({
        topic: 'disruption.detected',
        event_type: 'DISRUPTION_DETECTED',
        producer: 'disruption-api (duplicate-replay)',
        correlation_id: corrId,
        event_id: rootEvtId,
        idempotency_key: idemKey,
        ui_message: 'Flight delay detected (Duplicate Delivery Attempt)',
        payload: {
          journey_id: 1,
          booking_ref: 'AI-202',
          disruption_type: 'flight_delay',
          delay_minutes: 240,
        },
      });
      await fetchBrokerState();
    } catch (err) {
      console.error('Idempotency test error:', err);
    } finally {
      setRunningMode(null);
    }
  };

  const handleReplayDlq = async (dlqId) => {
    setRunningMode(`replay-${dlqId}`);
    try {
      await api.replayKafkaDlqEvent(dlqId);
      await fetchBrokerState();
    } catch (err) {
      console.error('DLQ replay error:', err);
    } finally {
      setRunningMode(null);
    }
  };

  const handleResetBroker = async () => {
    setRunningMode('reset');
    try {
      await api.resetKafkaBroker();
      setWsFrames([]);
      setLastPipelineResult(null);
      setSelectedEvent(null);
      await fetchBrokerState();
    } catch (err) {
      console.error('Reset broker error:', err);
    } finally {
      setRunningMode(null);
    }
  };

  const achievedMilestones = new Set(
    wsFrames.map((f) => f.ui_message).concat(lastPipelineResult?.realtime_milestones || [])
  );

  return (
    <div className="space-y-4">
      {/* Top Architecture Banner */}
      <div className="rounded-xl border border-white/[0.08] bg-[#070b16]/80 p-3.5 sm:p-4 backdrop-blur-2xl shadow-sm relative overflow-hidden">
        <div className="absolute inset-0 aviation-grid-overlay opacity-30 pointer-events-none" />
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-indigo-500/30 to-transparent pointer-events-none" />

        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 relative z-10">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase tracking-wider bg-indigo-500/15 text-indigo-300 border border-indigo-500/30">
                Stage 9 &middot; Apache Kafka + WebSocket
              </span>
              <span
                className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold border backdrop-blur-md ${
                  wsConnected
                    ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30 shadow-[0_0_8px_rgba(16,185,129,0.2)]'
                    : 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
                {wsConnected ? 'WebSocket Live (/api/v1/events/ws)' : 'WebSocket Reconnecting...'}
              </span>
            </div>
            <h2 className="text-base sm:text-lg font-bold text-white flex items-center gap-2 font-display tracking-tight">
              <Radio className="w-4 h-4 text-indigo-400" />
              Event-Driven Disruption Recovery Mesh (Apache Kafka)
            </h2>
            <p className="text-xs text-slate-300 max-w-3xl font-sans leading-relaxed">
              Decoupled producers and idempotent agent consumer groups communicating over partitioned Kafka topics with correlation IDs, automatic retries, Dead-Letter Topic (<code className="text-rose-300 font-mono">recovery.dlq</code>) routing, and real-time WebSocket streaming.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 relative z-10">
            <div className="flex items-center gap-1.5 bg-[#04060d] border border-white/[0.08] rounded-lg px-2.5 py-1 text-xs h-8">
              <span className="text-slate-400 font-mono text-[10px]">Delay:</span>
              <select
                value={stepDelayMs}
                onChange={(e) => setStepDelayMs(Number(e.target.value))}
                className="bg-transparent text-indigo-300 font-mono font-semibold focus:outline-none cursor-pointer text-xs"
              >
                <option value={0} className="bg-[#070b16]">0ms</option>
                <option value={120} className="bg-[#070b16]">120ms</option>
                <option value={300} className="bg-[#070b16]">300ms</option>
              </select>
            </div>

            <button
              onClick={handleResetBroker}
              disabled={runningMode !== null}
              className="h-8 px-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-white/[0.08] text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5 text-slate-400" />
              <span>Reset</span>
            </button>
          </div>
        </div>

        {/* Pipeline Topology Strip */}
        <div className="mt-3.5 pt-3 border-t border-white/[0.08] overflow-x-auto relative z-10">
          <div className="flex items-center gap-1.5 min-w-max text-xs">
            {[
              { name: 'Disruption API', role: 'Producer', topic: 'disruption.detected', color: 'border-rose-500/40 bg-rose-950/20 text-rose-200' },
              { name: 'Kafka Broker', role: 'Partitioned Log', topic: 'corr_id hash', color: 'border-indigo-500/40 bg-indigo-950/30 text-indigo-200' },
              { name: 'Impact Agent', role: 'impact-agent-group', topic: 'journey.affected', color: 'border-amber-500/40 bg-amber-950/20 text-amber-200' },
              { name: 'Kafka Broker', role: 'Topic Bus', topic: 'recovery.requested', color: 'border-indigo-500/40 bg-indigo-950/30 text-indigo-200' },
              { name: 'Recovery Agent', role: 'recovery-agent-group', topic: 'recovery.planned', color: 'border-sky-500/40 bg-sky-950/20 text-sky-200' },
              { name: 'Kafka Broker', role: 'Topic Bus', topic: 'action.requested', color: 'border-indigo-500/40 bg-indigo-950/30 text-indigo-200' },
              { name: 'Action Agent', role: 'action-agent-group', topic: 'action.completed', color: 'border-teal-500/40 bg-teal-950/20 text-teal-200' },
              { name: 'Kafka Broker', role: 'Topic Bus', topic: 'notification.requested', color: 'border-indigo-500/40 bg-indigo-950/30 text-indigo-200' },
              { name: 'Notification Agent', role: 'notification-agent-group', topic: 'WebSocket Push', color: 'border-emerald-500/40 bg-emerald-950/20 text-emerald-200' },
            ].map((node, idx, arr) => (
              <React.Fragment key={idx}>
                <div className={`px-2.5 py-1.5 rounded-lg border ${node.color} flex flex-col shadow-sm backdrop-blur-md`}>
                  <span className="font-bold text-[10px] font-display">{node.name}</span>
                  <span className="text-[9px] opacity-75 font-mono">{node.topic}</span>
                </div>
                {idx < arr.length - 1 && <ArrowRight className="w-3 h-3 text-slate-600 shrink-0" />}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>

      {/* Action Trigger Buttons */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
        <motion.button
          whileHover={{ y: -1 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => handleTriggerPipeline('normal')}
          disabled={runningMode !== null}
          className="p-3.5 rounded-xl bg-gradient-to-br from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 disabled:opacity-50 text-white text-left transition shadow-sm cursor-pointer flex flex-col justify-between"
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider bg-black/25 border border-white/10 px-2 py-0.5 rounded-md font-mono">
              1. Full Event Cascade
            </span>
            <Play className="w-3.5 h-3.5" />
          </div>
          <div className="mt-2.5">
            <div className="font-bold text-xs sm:text-sm font-display">Trigger Kafka Disruption Pipeline</div>
            <p className="text-[11px] text-indigo-100/80 mt-0.5 font-sans leading-relaxed">
              Emits Flight AI-202 delay (+240m) &rarr; streams all 7 recovery milestones over WebSocket.
            </p>
          </div>
        </motion.button>

        <motion.button
          whileHover={{ y: -1 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleTestIdempotentConsumer}
          disabled={runningMode !== null}
          className="p-3.5 rounded-xl bg-[#070b16]/80 hover:bg-[#0b1120] border border-teal-500/40 text-left transition shadow-sm cursor-pointer flex flex-col justify-between"
        >
          <div className="flex items-center justify-between text-teal-400">
            <span className="text-[10px] font-bold uppercase tracking-wider bg-teal-500/10 border border-teal-500/30 px-2 py-0.5 rounded-md font-mono">
              2. Idempotent Consumer
            </span>
            <CopyCheck className="w-3.5 h-3.5" />
          </div>
          <div className="mt-2.5">
            <div className="font-bold text-xs sm:text-sm text-slate-100 font-display">Replay Duplicate Kafka Event</div>
            <p className="text-[11px] text-slate-400 mt-0.5 font-sans leading-relaxed">
              Re-sends identical <code className="text-teal-300 font-mono">event_id</code> / <code className="text-teal-300 font-mono">idempotency_key</code> &mdash; deduplicates &amp; skips.
            </p>
          </div>
        </motion.button>

        <motion.button
          whileHover={{ y: -1 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => handleTriggerPipeline('transient_retry')}
          disabled={runningMode !== null}
          className="p-3.5 rounded-xl bg-[#070b16]/80 hover:bg-[#0b1120] border border-amber-500/40 text-left transition shadow-sm cursor-pointer flex flex-col justify-between"
        >
          <div className="flex items-center justify-between text-amber-400">
            <span className="text-[10px] font-bold uppercase tracking-wider bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded-md font-mono">
              3. Consumer Retry Policy
            </span>
            <RotateCcw className="w-3.5 h-3.5" />
          </div>
          <div className="mt-2.5">
            <div className="font-bold text-xs sm:text-sm text-slate-100 font-display">Simulate Transient Failure &amp; Retry</div>
            <p className="text-[11px] text-slate-400 mt-0.5 font-sans leading-relaxed">
              Recovery Agent fails on attempt #1, retries automatically, and succeeds on retry #1.
            </p>
          </div>
        </motion.button>

        <motion.button
          whileHover={{ y: -1 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => handleTriggerPipeline('poison_dlq')}
          disabled={runningMode !== null}
          className="p-3.5 rounded-xl bg-[#070b16]/80 hover:bg-[#0b1120] border border-rose-500/40 text-left transition shadow-sm cursor-pointer flex flex-col justify-between"
        >
          <div className="flex items-center justify-between text-rose-400">
            <span className="text-[10px] font-bold uppercase tracking-wider bg-rose-500/10 border border-rose-500/30 px-2 py-0.5 rounded-md font-mono">
              4. Dead-Letter Topic (DLQ)
            </span>
            <AlertTriangle className="w-3.5 h-3.5" />
          </div>
          <div className="mt-2.5">
            <div className="font-bold text-xs sm:text-sm text-slate-100 font-display">Simulate Poison-Pill &rarr; DLQ</div>
            <p className="text-[11px] text-slate-400 mt-0.5 font-sans leading-relaxed">
              Exhausts consumer retries on <code className="text-rose-300 font-mono">action.requested</code> &rarr; routes to <code className="text-rose-300 font-mono">recovery.dlq</code>.
            </p>
          </div>
        </motion.button>
      </div>

      {/* Real-Time WebSocket Recovery Milestones Bar */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3.5 sm:p-4">
        <div className="flex items-center justify-between mb-2.5">
          <div className="flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-emerald-400" />
            <h3 className="text-xs sm:text-sm font-bold text-slate-100">
              Real-Time WebSocket Recovery Progression
            </h3>
          </div>
          {lastPipelineResult?.correlation_id && (
            <span className="text-[10px] font-mono text-indigo-300 bg-indigo-950/60 border border-indigo-500/30 px-2 py-0.5 rounded-md">
              corr_id: {lastPipelineResult.correlation_id}
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-2">
          {EXPECTED_MILESTONES.map((ms, idx) => {
            const isDone = achievedMilestones.has(ms.label);
            return (
              <div
                key={ms.label}
                className={`p-2 rounded-lg border transition ${
                  isDone
                    ? 'border-emerald-500/40 bg-emerald-950/25 text-emerald-200'
                    : 'border-slate-800 bg-slate-950/60 text-slate-400'
                }`}
              >
                <div className="flex items-center justify-between text-[9px] font-mono mb-0.5">
                  <span>STEP {idx + 1}</span>
                  {isDone ? (
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                  ) : (
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-700" />
                  )}
                </div>
                <div className="font-bold text-[11px] leading-snug">"{ms.label}"</div>
                <div className="mt-1 text-[9px] font-mono opacity-75 truncate">{ms.topic}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Grid: Left = 11 Kafka Topics & Consumer Groups, Right = Live Event Stream & Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column: Kafka Topics Catalog & Consumer Groups (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Kafka Topics List */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 sm:p-4">
            <div className="flex items-center justify-between mb-2.5">
              <div className="flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-indigo-400" />
                <h3 className="text-xs sm:text-sm font-bold text-white">Kafka Topics ({topicsData?.total_topics || 11})</h3>
              </div>
              <button
                onClick={() => setSelectedTopic('ALL')}
                className={`text-[10px] px-2 py-0.5 rounded-md font-mono cursor-pointer ${
                  selectedTopic === 'ALL'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                Show All ({topicsData?.total_events_published || 0})
              </button>
            </div>

            <div className="space-y-1 max-h-[300px] overflow-y-auto pr-1">
              {(topicsData?.topics || []).map((t) => {
                const isDlq = t.topic === 'recovery.dlq';
                const isSelected = selectedTopic === t.topic;
                return (
                  <button
                    key={t.topic}
                    onClick={() => setSelectedTopic(t.topic)}
                    className={`w-full text-left px-2.5 py-1.5 rounded-lg border transition flex items-center justify-between cursor-pointer ${
                      isSelected
                        ? 'border-indigo-500 bg-indigo-950/50 text-white'
                        : isDlq && t.message_count > 0
                        ? 'border-rose-500/40 bg-rose-950/20 text-rose-200'
                        : 'border-slate-800/80 bg-slate-950/60 hover:bg-slate-800/50 text-slate-300'
                    }`}
                  >
                    <div>
                      <div className="font-mono text-[11px] font-semibold flex items-center gap-1.5">
                        <span>{t.topic}</span>
                        {isDlq && (
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                            DLQ
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-0.5">
                        Partitions: {t.partitions} &middot; Consumers:{' '}
                        {t.subscribed_consumer_groups?.length > 0
                          ? t.subscribed_consumer_groups.join(', ')
                          : 'sink / audit'}
                      </div>
                    </div>
                    <span
                      className={`px-1.5 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                        t.message_count > 0
                          ? isDlq
                            ? 'bg-rose-500/20 text-rose-300'
                            : 'bg-indigo-500/20 text-indigo-300'
                          : 'bg-slate-800 text-slate-500'
                      }`}
                    >
                      {t.message_count}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Idempotent Consumer Groups Telemetry */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 sm:p-4">
            <div className="flex items-center justify-between mb-2.5">
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-teal-400" />
                <h3 className="text-xs sm:text-sm font-bold text-white">Idempotent Consumer Groups</h3>
              </div>
              <span className="text-[10px] font-mono text-teal-300">
                Skips: {topicsData?.idempotent_skips_count || 0}
              </span>
            </div>

            <div className="space-y-2">
              {(consumersData?.consumer_groups || []).map((cg) => (
                <div
                  key={cg.group_id}
                  className="p-2.5 rounded-lg border border-slate-800 bg-slate-950/60 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-200 text-xs">{cg.agent_name}</span>
                    <span className="font-mono text-[9px] text-indigo-300 bg-indigo-950/60 px-1.5 py-0.5 rounded">
                      {cg.group_id}
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-400 font-mono truncate">
                    Topics: {cg.subscribed_topics.join(', ')}
                  </div>
                  <div className="grid grid-cols-4 gap-1 pt-0.5 text-center">
                    <div className="bg-slate-900 rounded p-1">
                      <div className="text-[9px] text-slate-400">Processed</div>
                      <div className="font-mono font-bold text-emerald-400 text-xs">{cg.events_processed}</div>
                    </div>
                    <div className="bg-slate-900 rounded p-1">
                      <div className="text-[9px] text-slate-400">Idem Skips</div>
                      <div className="font-mono font-bold text-teal-400 text-xs">{cg.idempotent_skips}</div>
                    </div>
                    <div className="bg-slate-900 rounded p-1">
                      <div className="text-[9px] text-slate-400">Retries</div>
                      <div className="font-mono font-bold text-amber-400 text-xs">{cg.retry_attempts}</div>
                    </div>
                    <div className="bg-slate-900 rounded p-1">
                      <div className="text-[9px] text-slate-400">To DLQ</div>
                      <div className="font-mono font-bold text-rose-400 text-xs">{cg.dlq_routed}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Live Event Stream, DLQ Replay & Schema Inspector (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Dead-Letter Topic (recovery.dlq) Alert Box if any DLQ records exist */}
          {dlqData?.records?.length > 0 && (
            <div className="rounded-xl border border-rose-500/40 bg-rose-950/20 p-3.5 sm:p-4 space-y-2.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-rose-300">
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                  <h3 className="text-xs sm:text-sm font-bold">
                    Dead-Letter Topic (`recovery.dlq`) &mdash; {dlqData.records.length} Poison-Pill Event(s)
                  </h3>
                </div>
              </div>
              <div className="space-y-1.5">
                {dlqData.records.map((rec) => (
                  <div
                    key={rec.dlq_id}
                    className="p-2.5 rounded-lg bg-slate-950/80 border border-rose-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 text-xs"
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono font-bold text-rose-300">{rec.dlq_id}</span>
                        <span className="text-slate-400">from</span>
                        <span className="font-mono text-amber-300">{rec.failed_topic}</span>
                        <span className="text-slate-400">({rec.failed_consumer_group})</span>
                      </div>
                      <div className="text-slate-300 text-xs">{rec.error_message}</div>
                      <div className="text-[10px] text-slate-500 font-mono">
                        Attempts: {rec.retry_attempts} &middot; Correlation: {rec.original_event?.correlation_id}
                      </div>
                    </div>
                    <button
                      onClick={() => handleReplayDlq(rec.dlq_id)}
                      disabled={rec.replayed || runningMode !== null}
                      className={`h-7 px-2.5 rounded-lg font-semibold text-xs shrink-0 cursor-pointer ${
                        rec.replayed
                          ? 'bg-emerald-950/50 text-emerald-400 border border-emerald-500/30'
                          : 'bg-rose-600 hover:bg-rose-500 text-white'
                      }`}
                    >
                      {rec.replayed ? 'Replayed ✓' : 'Sanitize & Replay'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Live Event Log Table */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 sm:p-4">
            <div className="flex items-center justify-between mb-2.5">
              <div className="flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-sky-400" />
                <h3 className="text-xs sm:text-sm font-bold text-white">
                  Kafka Event Log {selectedTopic !== 'ALL' ? `(${selectedTopic})` : '(All Topics)'}
                </h3>
              </div>
              <span className="text-[11px] text-slate-400">
                Click event to inspect <code className="text-indigo-300">Envelope</code>
              </span>
            </div>

            <div className="space-y-1.5 max-h-[300px] overflow-y-auto pr-1">
              {(streamData?.events || []).length === 0 ? (
                <div className="text-center py-10 text-xs text-slate-500 font-mono">
                  No Kafka events recorded yet. Click <strong>"Trigger Kafka Disruption Pipeline"</strong> above to stream events!
                </div>
              ) : (
                <AnimatePresence initial={false}>
                  {(streamData?.events || []).map((evt, idx) => {
                    const isSelected = selectedEvent?.event_id === evt.event_id;
                    return (
                      <motion.div
                        key={evt.event_id}
                        initial={{ opacity: 0, x: -16, scale: 0.98 }}
                        animate={{ opacity: 1, x: 0, scale: 1 }}
                        exit={{ opacity: 0, x: 16 }}
                        transition={{ duration: 0.2, delay: Math.min(idx * 0.02, 0.2) }}
                        onClick={() => setSelectedEvent(evt)}
                        className={`p-2.5 rounded-xl border transition-all duration-150 cursor-pointer text-xs relative overflow-hidden ${
                          isSelected
                            ? 'border-indigo-400 bg-indigo-950/50 shadow-sm ring-1 ring-indigo-400/30'
                            : 'border-white/[0.08] bg-[#070b16]/75 hover:bg-[#0b1120] hover:border-white/20'
                        }`}
                      >
                        <div className="flex flex-wrap items-center justify-between gap-1.5">
                          <div className="flex items-center gap-1.5">
                            <span className="px-2 py-0.5 rounded-md bg-indigo-500/15 text-indigo-300 font-mono font-semibold text-[10px] border border-indigo-500/30">
                              {evt.topic}
                            </span>
                            <span className="font-bold text-slate-200 font-display text-xs">{evt.ui_message || evt.event_type}</span>
                          </div>
                          <div className="flex items-center gap-1.5 font-mono text-[9px] text-slate-400">
                            <span>p:{evt.partition}</span>
                            <span>off:{evt.offset}</span>
                            {evt.retry_count > 0 && (
                              <span className="text-amber-300 bg-amber-500/15 px-1.5 py-0.5 rounded border border-amber-500/30 font-bold">
                                retry:{evt.retry_count}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="mt-1 flex flex-wrap items-center gap-2.5 text-[9px] font-mono text-slate-400">
                          <span>event_id: <span className="text-slate-300">{evt.event_id}</span></span>
                          <span>corr_id: <span className="text-indigo-300">{evt.correlation_id}</span></span>
                          <span>producer: <span className="text-sky-300">{evt.producer}</span></span>
                        </div>
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
              )}
            </div>
          </div>

          {/* Structured Kafka Event Schema Inspector */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 sm:p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5 text-emerald-400" />
                <h3 className="text-xs sm:text-sm font-bold text-white">KafkaEventEnvelope Schema Inspector</h3>
              </div>
              {selectedEvent && (
                <span className="text-[10px] font-mono text-emerald-300">
                  {selectedEvent.idempotency_key}
                </span>
              )}
            </div>

            {selectedEvent ? (
              <pre className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-[10px] font-mono text-slate-200 overflow-x-auto max-h-[240px]">
                {JSON.stringify(selectedEvent, null, 2)}
              </pre>
            ) : (
              <div className="text-center py-6 text-xs text-slate-500">
                Select an event from the Kafka Event Log above to inspect its full envelope, headers, correlation ID, and payload.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
