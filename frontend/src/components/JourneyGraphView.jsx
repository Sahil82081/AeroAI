import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Plane, 
  Train, 
  Bus, 
  Hotel, 
  Ticket, 
  ArrowRight, 
  AlertTriangle, 
  ShieldCheck, 
  Clock, 
  MapPin, 
  Layers, 
  GitFork, 
  Calendar, 
  Info,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import { CountUpNumber, StatCard } from './ui/SaaSPrimitives';

export function JourneyGraphView({ 
  journey, 
  graphData, 
  loading, 
  onRefreshGraph 
}) {
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState(null);

  const nodes = graphData?.nodes || [];
  const edges = graphData?.edges || [];
  const riskSummary = graphData?.risk_summary;

  const getTypeIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'flight':
        return <Plane className="w-4 h-4 text-sky-400" />;
      case 'train':
        return <Train className="w-4 h-4 text-amber-400" />;
      case 'bus':
        return <Bus className="w-4 h-4 text-emerald-400" />;
      case 'hotel':
        return <Hotel className="w-4 h-4 text-indigo-400" />;
      case 'activity':
      case 'tour':
        return <Ticket className="w-4 h-4 text-pink-400" />;
      default:
        return <MapPin className="w-4 h-4 text-on-surface-variant" />;
    }
  };

  const getRiskBadge = (risk) => {
    switch (risk) {
      case 'SAFE':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>SAFE CONNECTION</span>
          </span>
        );
      case 'TIGHT':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            <span>TIGHT CONNECTION</span>
          </span>
        );
      case 'IMPOSSIBLE':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-rose-500/15 text-rose-300 border border-rose-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
            <span>IMPOSSIBLE CONNECTION</span>
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[11px] text-on-surface-variant bg-slate-900 border border-surface-container-high font-mono">
            {risk || 'NONE'}
          </span>
        );
    }
  };

  const formatDateTime = (dtStr) => {
    if (!dtStr) return 'N/A';
    try {
      const d = new Date(dtStr);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' (' + d.toLocaleDateString([], { month: 'short', day: 'numeric' }) + ')';
    } catch {
      return dtStr;
    }
  };

  return (
    <div className="space-y-4">
      
      {/* Top Banner: NetworkX Graph Topology & Risk Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        
        {/* Metric 1: Total Multi-Modal Nodes */}
        <StatCard
          title="Journey Vertices"
          value={nodes.length}
          subtext="NetworkX DAG Directed Graph"
          icon={Layers}
          color="sky"
          delay={0.05}
        />

        {/* Metric 2: Detected Connections */}
        <StatCard
          title="Transfers & Edges"
          value={edges.length}
          subtext="Chronological Sequential Flow"
          icon={GitFork}
          color="violet"
          delay={0.1}
        />

        {/* Metric 3: Safe Connections */}
        <StatCard
          title="Safe Buffers"
          value={riskSummary?.safe_connections || 0}
          subtext="Exceeds min required buffer"
          icon={ShieldCheck}
          color="emerald"
          delay={0.15}
        />

        {/* Metric 4: Tight / Impossible Risks */}
        <StatCard
          title="Connection Risk"
          value={
            (riskSummary?.impossible_connections || 0) > 0
              ? `${riskSummary?.impossible_connections} Critical`
              : (riskSummary?.tight_connections || 0) > 0
              ? `${riskSummary?.tight_connections} Tight`
              : 'Safe'
          }
          subtext={`Topology status: ${riskSummary?.highest_risk || 'SAFE'}`}
          icon={AlertTriangle}
          color={
            riskSummary?.highest_risk === 'IMPOSSIBLE'
              ? 'rose'
              : riskSummary?.highest_risk === 'TIGHT'
              ? 'amber'
              : 'emerald'
          }
          delay={0.2}
        />

      </div>

      {/* Critical Dependencies Alert if any */}
      {riskSummary?.critical_dependencies && riskSummary.critical_dependencies.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-3 sm:p-3.5 rounded-xl bg-amber-950/25 border border-amber-500/30 flex items-start gap-3 backdrop-blur-xl shadow-md shadow-amber-950/30"
        >
          <div className="p-1.5 rounded-lg bg-amber-500/20 text-amber-400 shrink-0 mt-0.5">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div className="text-xs space-y-1">
            <span className="font-bold text-amber-300 font-display">Vulnerable Connection Points Identified:</span>
            <ul className="list-disc list-inside text-slate-300 space-y-0.5 font-mono text-[11px]">
              {riskSummary.critical_dependencies.map((dep, idx) => (
                <li key={idx}>{dep}</li>
              ))}
            </ul>
          </div>
        </motion.div>
      )}

      {/* Interactive Visual Graph: Sequential Pipeline */}
      <div className="p-4 sm:p-5 rounded-xl border border-surface-container-high bg-surface-container-low/90 backdrop-blur-2xl shadow-xl space-y-4 relative overflow-hidden">
        <div className="absolute inset-0 aviation-grid-overlay opacity-30 pointer-events-none" />

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-surface-container-high pb-3 relative z-10">
          <div>
            <h3 className="text-base font-bold text-white font-display flex items-center gap-2">
              <span>Multi-Modal Journey Pipeline</span>
              <span className="text-[11px] font-normal text-on-surface-variant font-mono px-2 py-0.5 rounded-md bg-white/[0.05] border border-surface-container-high/60">
                {journey?.title || 'Active Journey'}
              </span>
            </h3>
            <p className="text-xs text-on-surface-variant mt-0.5 font-sans">
              NetworkX DAG visual representation showing sequential bookings, transfer buffers, and downstream dependencies.
            </p>
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onRefreshGraph}
            disabled={loading}
            className="h-8 px-3 py-1.5 rounded-lg bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-xs font-semibold text-white shadow-md shadow-sky-600/20 cursor-pointer transition flex items-center gap-1.5 self-start sm:self-auto"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Recompute Graph</span>
          </motion.button>
        </div>

        {/* Visual Sequence Chain */}
        <div className="space-y-3 relative z-10">
          {nodes.length > 0 ? (
            nodes.map((node, index) => {
              const outgoingEdge = edges.find(e => e.source === node.id);

              return (
                <div key={node.id} className="space-y-3">
                  {/* Node Card */}
                  <motion.div 
                    whileHover={{ y: -1 }}
                    onClick={() => { setSelectedNodeId(node.id); setSelectedEdgeId(null); }}
                    className={`p-3.5 sm:p-4 rounded-xl border transition-all duration-200 cursor-pointer relative overflow-hidden ${
                      selectedNodeId === node.id 
                        ? 'bg-[#0f172a]/95 border-sky-400 shadow-[0_0_16px_rgba(14,165,233,0.25)] ring-1 ring-sky-400/50' 
                        : 'bg-surface-container-high/80 border-surface-container-high hover:border-white/20 shadow-sm'
                    }`}
                  >
                    <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent pointer-events-none" />

                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      
                      {/* Left: Type Icon + Provider + Title */}
                      <div className="flex items-start sm:items-center gap-3">
                        <div className="p-2 rounded-xl bg-surface-container-lowest border border-surface-container-high shadow-inner shrink-0">
                          {getTypeIcon(node.type)}
                        </div>
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-[11px] font-bold uppercase tracking-wider text-sky-400 font-mono">
                              {node.type}
                            </span>
                            <span className="text-[11px] text-slate-600">&bull;</span>
                            <span className="text-xs font-semibold text-slate-300 font-sans">
                              {node.provider}
                            </span>
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/[0.06] text-on-surface-variant border border-surface-container-high/60">
                              {node.key}
                            </span>
                          </div>
                          <h4 className="text-xs sm:text-sm font-bold text-white mt-0.5 font-display">
                            {node.name}
                          </h4>
                        </div>
                      </div>

                      {/* Right: Route + Times + Status */}
                      <div className="flex flex-wrap items-center gap-4 sm:gap-5 text-xs text-slate-300">
                        {node.origin && (
                          <div className="text-left sm:text-right">
                            <div className="text-on-surface-variant text-[10px] font-mono uppercase tracking-wider">Route</div>
                            <div className="font-semibold text-white flex items-center gap-1.5 mt-0.5 text-xs">
                              <span>{node.origin}</span>
                              {node.destination && node.destination !== node.origin && (
                                <>
                                  <ArrowRight className="w-3.5 h-3.5 text-sky-400" />
                                  <span>{node.destination}</span>
                                </>
                              )}
                            </div>
                          </div>
                        )}

                        <div className="text-left sm:text-right">
                          <div className="text-on-surface-variant text-[10px] font-mono uppercase tracking-wider">Schedule Window</div>
                          <div className="font-mono text-slate-200 mt-0.5 text-xs">
                            {formatDateTime(node.start_time)} &rarr; {formatDateTime(node.end_time)}
                          </div>
                        </div>

                        <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full font-medium bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                          {node.status || 'CONFIRMED'}
                        </span>
                      </div>

                    </div>
                  </motion.div>

                  {/* Connecting Line & Transfer Edge Card */}
                  {outgoingEdge && (
                    <div className="flex flex-col items-center my-2">
                      {/* Animated Connector Path with Pulse */}
                      <div className="relative w-0.5 h-5 bg-gradient-to-b from-sky-400 to-indigo-500">
                        <span className="absolute top-1/2 -left-1 w-2.5 h-2.5 rounded-full bg-sky-400 shadow-[0_0_6px_rgba(56,189,248,0.9)] -translate-y-1/2 animate-ping" />
                      </div>

                      {/* Edge Transfer Card */}
                      <motion.div 
                        whileHover={{ scale: 1.01 }}
                        onClick={() => { setSelectedEdgeId(outgoingEdge.id); setSelectedNodeId(null); }}
                        className={`w-full max-w-xl p-3 sm:p-3.5 rounded-xl border text-xs cursor-pointer transition-all duration-200 flex items-center justify-between gap-3 backdrop-blur-xl shadow-md ${
                          outgoingEdge.risk_level === 'IMPOSSIBLE'
                            ? 'bg-rose-950/30 border-rose-500/40 text-rose-200 shadow-rose-950/40'
                            : outgoingEdge.risk_level === 'TIGHT'
                              ? 'bg-amber-950/30 border-amber-500/40 text-amber-200 shadow-amber-950/40'
                              : 'bg-surface-container-high border-surface-container-high text-slate-300 hover:border-sky-500/40'
                        }`}
                      >
                        <div className="flex items-center gap-2.5">
                          <div className={`p-1.5 rounded-lg border ${
                            outgoingEdge.risk_level === 'IMPOSSIBLE'
                              ? 'bg-rose-500/20 border-rose-500/30 text-rose-400'
                              : outgoingEdge.risk_level === 'TIGHT'
                                ? 'bg-amber-500/20 border-amber-500/30 text-amber-400'
                                : 'bg-emerald-500/20 border-emerald-500/30 text-emerald-400'
                          }`}>
                            <Clock className="w-3.5 h-3.5" />
                          </div>
                          <div>
                            <div className="font-bold text-white flex items-center gap-2 font-display text-xs">
                              <span>Connection Buffer: {outgoingEdge.buffer_minutes} mins</span>
                              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/[0.08] text-slate-300">
                                {outgoingEdge.transfer_type.replace(/_/g, ' ')}
                              </span>
                            </div>
                            <div className="text-[11px] text-on-surface-variant mt-0.5 font-sans">
                              {outgoingEdge.risk_reason}
                            </div>
                          </div>
                        </div>

                        <div>
                          {getRiskBadge(outgoingEdge.risk_level)}
                        </div>
                      </motion.div>

                      {/* Connecting Line Continued */}
                      <div className="w-0.5 h-5 bg-gradient-to-b from-indigo-500 to-sky-400" />
                    </div>
                  )}

                </div>
              );
            })
          ) : (
            <div className="p-8 text-center text-xs text-outline italic font-mono">
              No bookings recorded in journey. Ingest bookings via email in the Inbox tab to build the graph.
            </div>
          )}
        </div>

      </div>

    </div>
  );
}

export default JourneyGraphView;
