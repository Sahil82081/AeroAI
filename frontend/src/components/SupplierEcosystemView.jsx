import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plane,
  Train,
  Bus,
  Hotel,
  Search,
  RefreshCw,
  CheckCircle2,
  AlertOctagon,
  Clock,
  DollarSign,
  Layers,
  ArrowRight,
  RotateCcw,
  ShieldAlert,
  Sliders,
  Cpu,
  Zap,
  Check
} from 'lucide-react';
import { apiService } from '../services/api';

export function SupplierEcosystemView() {
  const [activeSupplierTab, setActiveSupplierTab] = useState('trains');
  const [originFilter, setOriginFilter] = useState('Delhi');
  const [destinationFilter, setDestinationFilter] = useState('Jaipur');
  const [hotelLocationFilter, setHotelLocationFilter] = useState('Jaipur');

  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionResult, setActionResult] = useState(null);
  const [actionError, setActionError] = useState(null);

  // Simulation controls
  const [simLatencyMs, setSimLatencyMs] = useState(35);
  const [simFailureMode, setSimFailureMode] = useState('none');
  const [disruptionWaiver, setDisruptionWaiver] = useState(true);
  const [lastLatency, setLastLatency] = useState(null);
  const [adapterTrace, setAdapterTrace] = useState(null);

  const fetchInventory = async (supplierType = activeSupplierTab, orig = originFilter, dest = destinationFilter, loc = hotelLocationFilter) => {
    setLoading(true);
    setActionError(null);
    try {
      const simParams = {
        simulate_latency_ms: simLatencyMs,
        simulate_failure: simFailureMode !== 'none' ? simFailureMode : undefined,
      };

      let res;
      if (supplierType === 'flights') {
        res = await apiService.searchSupplierFlights({
          origin: orig || undefined,
          destination: dest || undefined,
          ...simParams,
        });
      } else if (supplierType === 'trains') {
        res = await apiService.searchSupplierTrains({
          origin: orig || undefined,
          destination: dest || undefined,
          ...simParams,
        });
      } else if (supplierType === 'buses') {
        res = await apiService.searchSupplierBuses({
          origin: orig || undefined,
          destination: dest || undefined,
          ...simParams,
        });
      } else {
        res = await apiService.searchSupplierHotels({
          location: loc || undefined,
          ...simParams,
        });
      }

      setInventory(res.results || []);
      setLastLatency(res.simulated_latency_ms);
      setAdapterTrace(res.adapter_trace || null);
    } catch (err) {
      setInventory([]);
      const detail = err.response?.data?.detail;
      setActionError(typeof detail === 'object' ? detail : { message: err.message || 'Supplier API Failure' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory(activeSupplierTab, originFilter, destinationFilter, hotelLocationFilter);
  }, [activeSupplierTab]);

  const handlePresetRoute = (type, orig, dest, loc = '') => {
    setActiveSupplierTab(type);
    setOriginFilter(orig);
    setDestinationFilter(dest);
    if (loc) setHotelLocationFilter(loc);
    fetchInventory(type, orig, dest, loc);
  };

  const handleRebook = async (item) => {
    setActionError(null);
    try {
      const res = await apiService.rebookSupplierBooking({
        original_booking_ref: `ORIG-${item.transport_id}`,
        transport_id: item.transport_id,
        passenger_name: 'Sahil Sharma',
        seats: 1,
        reason: 'DISRUPTION_RECOVERY',
        waive_change_fee: disruptionWaiver,
        simulate_latency_ms: simLatencyMs,
        simulate_failure: simFailureMode !== 'none' ? simFailureMode : undefined,
      });
      setActionResult({ type: 'REBOOK_CONFIRMED', data: res });
      setLastLatency(res.simulated_latency_ms);
      setAdapterTrace(res.adapter_trace || null);
      fetchInventory();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setActionError(typeof detail === 'object' ? detail : { message: err.message });
    }
  };

  const handleRefund = async (item) => {
    setActionError(null);
    try {
      const id = item.transport_id || item.hotel_id;
      const res = await apiService.refundSupplierBooking({
        booking_reference: `REF-${id}-882`,
        transport_id: id,
        supplier_type: item.supplier_type,
        original_price: item.price || item.price_per_night || 800,
        currency: item.currency || 'INR',
        reason: disruptionWaiver ? 'CARRIER_DISRUPTION_WAIVER' : 'VOLUNTARY_CANCELLATION',
        is_disruption_waiver: disruptionWaiver,
        simulate_latency_ms: simLatencyMs,
        simulate_failure: simFailureMode !== 'none' ? simFailureMode : undefined,
      });
      setActionResult({ type: 'REFUND_EVALUATED', data: res });
      setLastLatency(res.simulated_latency_ms);
      setAdapterTrace(res.adapter_trace || null);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setActionError(typeof detail === 'object' ? detail : { message: err.message });
    }
  };

  const handleCancel = async (item) => {
    setActionError(null);
    try {
      const id = item.transport_id || item.hotel_id;
      const res = await apiService.cancelSupplierBooking({
        booking_reference: `PNR-${id}-401`,
        transport_id: id,
        supplier_type: item.supplier_type,
        original_price: item.price || item.price_per_night || 800,
        reason: disruptionWaiver ? 'DISRUPTION_CASCADE' : 'TRAVELER_REQUEST',
        simulate_latency_ms: simLatencyMs,
        simulate_failure: simFailureMode !== 'none' ? simFailureMode : undefined,
      });
      setActionResult({ type: 'BOOKING_CANCELLED', data: res });
      setLastLatency(res.simulated_latency_ms);
      setAdapterTrace(res.adapter_trace || null);
      fetchInventory();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setActionError(typeof detail === 'object' ? detail : { message: err.message });
    }
  };

  const handleHotelModify = async (hotel) => {
    setActionError(null);
    try {
      const res = await apiService.modifySupplierHotel({
        booking_reference: `HTL-RES-${hotel.hotel_id}`,
        hotel_id: hotel.hotel_id,
        new_check_in: '2026-10-20T22:45:00',
        late_arrival_notice: true,
        notes: 'Delayed arrival due to upstream flight/train connection shift. Please hold room.',
        simulate_latency_ms: simLatencyMs,
        simulate_failure: simFailureMode !== 'none' ? simFailureMode : undefined,
      });
      setActionResult({ type: 'HOTEL_CHECKIN_MODIFIED', data: res });
      setLastLatency(res.simulated_latency_ms);
      setAdapterTrace(res.adapter_trace || null);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setActionError(typeof detail === 'object' ? detail : { message: err.message });
    }
  };

  const handleResetSimulation = async () => {
    await apiService.resetSupplierSimulation();
    setSimFailureMode('none');
    setSimLatencyMs(35);
    setActionResult(null);
    setActionError(null);
    fetchInventory(activeSupplierTab, originFilter, destinationFilter, hotelLocationFilter);
  };

  return (
    <div className="space-y-4">
      {/* Architecture & Mock Disclaimer Header */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="p-3.5 sm:p-4 rounded-xl bg-surface-container-low/90 backdrop-blur-2xl border border-surface-container-high shadow-glass-card space-y-3 relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
        <div className="flex flex-wrap items-center justify-between gap-3 relative z-10">
          <div>
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-mono shadow-[0_0_8px_rgba(16,185,129,0.15)]">
                STAGE 5 &middot; SIMULATED MOCK SUPPLIER API ECOSYSTEM
              </span>
              {lastLatency !== null && (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-[#0d1527] text-sky-400 border border-surface-container-high flex items-center gap-1 shadow-sm">
                  <Clock className="w-3 h-3 text-sky-400" /> {lastLatency} ms simulated latency
                </span>
              )}
            </div>
            <h2 className="text-lg sm:text-xl font-bold text-white mt-1 tracking-tight font-display">
              Decoupled Multi-Modal Supplier Ecosystem (Flight, Train, Bus &amp; Hotel Mock Services)
            </h2>
            <p className="text-xs text-on-surface-variant mt-0.5 max-w-3xl leading-relaxed font-sans">
              All APIs below are explicitly marked as <strong className="text-emerald-400">MOCK APIs</strong>. Agents communicate strictly through the decoupled adapter chain so real GDS/CRS providers can replace mocks without changing agent code.
            </p>
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleResetSimulation}
            className="px-3 py-1.5 rounded-lg bg-[#0d1527] hover:bg-[#131f38] text-xs font-semibold text-slate-200 border border-surface-container-high hover:border-emerald-500/40 flex items-center gap-1.5 cursor-pointer transition shadow-sm h-8"
          >
            <RotateCcw className="w-3.5 h-3.5 text-emerald-400" />
            <span>Reset Mock Inventory</span>
          </motion.button>
        </div>

        {/* Visual Architecture Chain */}
        <div className="p-3 rounded-xl bg-surface-container-lowest/90 border border-surface-container-high flex flex-wrap items-center justify-between gap-2.5 text-xs">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 font-semibold flex items-center gap-1 font-mono shadow-sm text-[11px]">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
              1. Recovery Agent
            </span>
            <ArrowRight className="w-3 h-3 text-slate-600" />
            <span className="px-2.5 py-1 rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-300 font-semibold flex items-center gap-1 font-mono shadow-sm text-[11px]">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
              2. Supplier Service Interface
            </span>
            <ArrowRight className="w-3 h-3 text-slate-600" />
            <span className="px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 font-semibold flex items-center gap-1 font-mono shadow-sm text-[11px]">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              3. Supplier HTTP Adapter
            </span>
            <ArrowRight className="w-3 h-3 text-slate-600" />
            <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-semibold flex items-center gap-1 font-mono shadow-sm text-[11px]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              4. Mock Supplier REST API
            </span>
          </div>
          {adapterTrace && (
            <span className="font-mono text-[10px] text-on-surface-variant bg-white/[0.04] px-2.5 py-0.5 rounded-md border border-surface-container-high/60">
              {adapterTrace.adapter_class} &rarr; <strong className="text-emerald-400">{adapterTrace.mock_api_endpoint}</strong>
            </span>
          )}
        </div>
      </motion.div>

      {/* Simulation Controls & Quick Route Presets */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left 2 cols: Supplier Tabs + Filter Bar + Inventory Cards */}
        <div className="lg:col-span-2 space-y-3.5">
          {/* 4 Supplier Service Selector Tabs */}
          <div className="flex flex-wrap items-center justify-between gap-2 bg-surface-container-low/90 p-1.5 rounded-xl border border-surface-container-high backdrop-blur-2xl">
            <div className="flex flex-wrap gap-1">
              {[
                { id: 'flights', label: '1. Flights', icon: Plane, endpoint: 'GET /flights/search' },
                { id: 'trains', label: '2. Trains', icon: Train, endpoint: 'GET /trains/search' },
                { id: 'buses', label: '3. Buses', icon: Bus, endpoint: 'GET /buses/search' },
                { id: 'hotels', label: '4. Hotels', icon: Hotel, endpoint: 'GET /hotels/search' },
              ].map((tab) => {
                const Icon = tab.icon;
                const active = activeSupplierTab === tab.id;
                return (
                  <motion.button
                    whileTap={{ scale: 0.97 }}
                    key={tab.id}
                    onClick={() => setActiveSupplierTab(tab.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer font-display h-8 ${
                      active
                        ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-[0_0_12px_rgba(16,185,129,0.2)] border border-emerald-400/30'
                        : 'text-on-surface-variant hover:text-slate-200 hover:bg-white/[0.05]'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span>{tab.label}</span>
                  </motion.button>
                );
              })}
            </div>

            {/* Quick Route Presets */}
            <div className="flex items-center gap-1 text-[10px] font-sans">
              <button
                onClick={() => handlePresetRoute('trains', 'Delhi', 'Jaipur')}
                className="px-2 py-0.5 rounded-md bg-[#0d1527] hover:bg-[#152038] text-slate-300 border border-surface-container-high hover:border-emerald-500/30 cursor-pointer transition"
              >
                Delhi &rarr; Jaipur
              </button>
              <button
                onClick={() => handlePresetRoute('flights', 'Mumbai', 'Delhi')}
                className="px-2 py-0.5 rounded-md bg-[#0d1527] hover:bg-[#152038] text-slate-300 border border-surface-container-high hover:border-emerald-500/30 cursor-pointer transition"
              >
                Mumbai &rarr; Delhi
              </button>
              <button
                onClick={() => handlePresetRoute('flights', 'SFO', 'HND')}
                className="px-2 py-0.5 rounded-md bg-[#0d1527] hover:bg-[#152038] text-slate-300 border border-surface-container-high hover:border-emerald-500/30 cursor-pointer transition"
              >
                SFO &rarr; HND
              </button>
              <button
                onClick={() => handlePresetRoute(activeSupplierTab, '', '', '')}
                className="px-2 py-0.5 rounded-md bg-[#0d1527] hover:bg-[#152038] text-sky-400 border border-surface-container-high hover:border-sky-500/30 cursor-pointer transition"
              >
                Show All
              </button>
            </div>
          </div>

          {/* Search Inputs */}
          <div className="p-3 rounded-xl bg-surface-container-low/90 border border-surface-container-high backdrop-blur-2xl flex flex-wrap items-end gap-2.5">
            {activeSupplierTab !== 'hotels' ? (
              <>
                <div className="flex-1 min-w-[130px]">
                  <label className="block text-[10px] font-semibold text-on-surface-variant mb-1 font-sans">Origin City / Code</label>
                  <input
                    type="text"
                    value={originFilter}
                    onChange={(e) => setOriginFilter(e.target.value)}
                    placeholder="e.g. Delhi, Mumbai, SFO"
                    className="w-full px-2.5 py-1.5 rounded-lg bg-surface-container-lowest border border-surface-container-high text-xs text-white focus:outline-none focus:border-emerald-500/50 transition font-sans h-8.5"
                  />
                </div>
                <div className="flex-1 min-w-[130px]">
                  <label className="block text-[10px] font-semibold text-on-surface-variant mb-1 font-sans">Destination City / Code</label>
                  <input
                    type="text"
                    value={destinationFilter}
                    onChange={(e) => setDestinationFilter(e.target.value)}
                    placeholder="e.g. Jaipur, Delhi, HND"
                    className="w-full px-2.5 py-1.5 rounded-lg bg-surface-container-lowest border border-surface-container-high text-xs text-white focus:outline-none focus:border-emerald-500/50 transition font-sans h-8.5"
                  />
                </div>
              </>
            ) : (
              <div className="flex-1 min-w-[180px]">
                <label className="block text-[10px] font-semibold text-on-surface-variant mb-1 font-sans">Hotel City / Location</label>
                <input
                  type="text"
                  value={hotelLocationFilter}
                  onChange={(e) => setHotelLocationFilter(e.target.value)}
                  placeholder="e.g. Jaipur, Delhi, Mumbai, Tokyo"
                  className="w-full px-2.5 py-1.5 rounded-lg bg-surface-container-lowest border border-surface-container-high text-xs text-white focus:outline-none focus:border-emerald-500/50 transition font-sans h-8.5"
                />
              </div>
            )}

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => fetchInventory()}
              disabled={loading}
              className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white text-xs font-bold flex items-center gap-1.5 cursor-pointer shadow-[0_0_12px_rgba(56,189,248,0.2)] transition font-display disabled:opacity-50 h-8.5"
            >
              <Search className="w-3.5 h-3.5" />
              <span>{loading ? 'Querying...' : 'Search Supplier API'}</span>
            </motion.button>
          </div>

          {/* Inventory Cards */}
          <div className="space-y-2.5">
            {inventory.length > 0 ? (
              inventory.map((item, idx) => {
                const id = item.transport_id || item.hotel_id;
                const rules = item.cancellation_rules || {};
                return (
                  <motion.div
                    key={id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.25, delay: idx * 0.04 }}
                    className="p-3.5 rounded-xl bg-surface-container-low/90 border border-surface-container-high hover:border-emerald-500/30 transition shadow-glass-card space-y-2.5"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-2.5">
                      <div>
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="px-2 py-0.5 rounded-md bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-mono text-[11px] font-bold">
                            {id}
                          </span>
                          <span className="text-sm font-bold text-white font-display">
                            {item.provider}
                          </span>
                          <span className="text-[11px] text-on-surface-variant font-mono">
                            {item.flight_number || item.train_number || item.bus_number || item.room_type}
                          </span>
                          <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-white/[0.06] text-amber-300 font-mono border border-surface-container-high">
                            MOCK API
                          </span>
                        </div>

                        {item.supplier_type !== 'hotel' ? (
                          <div className="text-xs text-slate-300 mt-1 flex flex-wrap items-center gap-1.5 font-sans">
                            <span className="font-semibold text-sky-400">{item.origin}</span>
                            <span className="text-outline">&rarr;</span>
                            <span className="font-semibold text-sky-400">{item.destination}</span>
                            <span className="text-slate-600">|</span>
                            <span className="font-mono text-[10px] text-on-surface-variant">Dep: <strong className="text-slate-200">{item.departure}</strong></span>
                            <span className="text-outline">&rarr;</span>
                            <span className="font-mono text-[10px] text-on-surface-variant">Arr: <strong className="text-slate-200">{item.arrival}</strong></span>
                          </div>
                        ) : (
                          <div className="text-xs text-slate-300 mt-1 font-sans">
                            <span className="font-semibold text-sky-400">{item.location}</span> &middot; {item.address} &middot; Check-in: <strong className="text-slate-200">{item.check_in_window}</strong>
                          </div>
                        )}
                      </div>

                      <div className="text-right">
                        <div className="text-base font-bold text-emerald-400 font-display">
                          {item.currency} {item.price || item.price_per_night}
                        </div>
                        <div className="text-[10px] text-on-surface-variant font-sans">
                          {item.supplier_type !== 'hotel'
                            ? `${item.available_seats} seats available`
                            : `${item.available_rooms} rooms available`}
                        </div>
                      </div>
                    </div>

                    {/* Cancellation & Refund Rules Strip */}
                    <div className="p-2.5 rounded-lg bg-surface-container-lowest/90 border border-surface-container-high/60 flex flex-wrap items-center justify-between gap-2 text-[10px] text-on-surface-variant font-sans">
                      <div className="flex flex-wrap items-center gap-2">
                        <span>
                          Tier: <strong className="text-slate-200 font-mono">{rules.fare_tier || 'STANDARD'}</strong>
                        </span>
                        <span className="text-slate-600">&bull;</span>
                        <span>
                          Refundable:{' '}
                          <strong className={item.refund_eligibility ? 'text-emerald-400' : 'text-rose-400'}>
                            {item.refund_eligibility ? 'Yes' : 'Non-Refundable (Tax Only)'}
                          </strong>
                        </span>
                        <span className="text-slate-600">&bull;</span>
                        <span>
                          Penalty: <strong className="text-slate-200">{rules.penalty_pct}%</strong> (min {item.currency} {rules.cancellation_fee})
                        </span>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex flex-wrap items-center gap-1.5">
                        {item.supplier_type !== 'hotel' ? (
                          <motion.button
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => handleRebook(item)}
                            className="px-2.5 py-1 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white font-semibold font-mono text-[10px] cursor-pointer shadow-sm transition"
                          >
                            POST /bookings/rebook
                          </motion.button>
                        ) : (
                          <motion.button
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => handleHotelModify(item)}
                            className="px-2.5 py-1 rounded-md bg-indigo-600 hover:bg-indigo-500 text-white font-semibold font-mono text-[10px] cursor-pointer shadow-sm transition"
                          >
                            POST /hotel/modify (Late Check-in)
                          </motion.button>
                        )}
                        <motion.button
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          onClick={() => handleRefund(item)}
                          className="px-2.5 py-1 rounded-md bg-sky-600/80 hover:bg-sky-500 text-white font-semibold font-mono text-[10px] cursor-pointer shadow-sm transition"
                        >
                          POST /bookings/refund
                        </motion.button>
                        <motion.button
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          onClick={() => handleCancel(item)}
                          className="px-2.5 py-1 rounded-md bg-rose-600/80 hover:bg-rose-500 text-white font-semibold font-mono text-[10px] cursor-pointer shadow-sm transition"
                        >
                          POST /bookings/cancel
                        </motion.button>
                      </div>
                    </div>
                  </motion.div>
                );
              })
            ) : (
              <div className="p-8 rounded-xl bg-surface-container-low/60 border border-surface-container-high text-center text-xs text-outline font-sans">
                {loading ? 'Querying Mock Supplier API...' : 'No matching inventory found for current filter or failure simulated.'}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Fault & Latency Simulator + Live Response Inspector */}
        <div className="space-y-3.5">
          <motion.div
            initial={{ opacity: 0, x: 15 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="p-3.5 rounded-xl bg-surface-container-low/90 backdrop-blur-2xl border border-surface-container-high shadow-glass-card space-y-3"
          >
            <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-amber-400 font-mono">
              <Sliders className="w-3.5 h-3.5 text-amber-400" />
              <span>Supplier Fault &amp; Latency Controls</span>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs text-slate-300 font-sans">
                Simulated API Latency: <strong className="text-sky-400 font-mono">{simLatencyMs} ms</strong>
              </label>
              <input
                type="range"
                min="0"
                max="500"
                step="5"
                value={simLatencyMs}
                onChange={(e) => setSimLatencyMs(Number(e.target.value))}
                className="w-full accent-sky-500 cursor-pointer"
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs text-slate-300 font-sans">Simulate Supplier Failure Mode</label>
              <select
                value={simFailureMode}
                onChange={(e) => setSimFailureMode(e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg bg-surface-container-lowest border border-surface-container-high text-xs text-white focus:outline-none focus:border-amber-500/50 transition font-sans h-8.5"
              >
                <option value="none">None (Healthy 200 OK)</option>
                <option value="timeout">HTTP 504 - Supplier Gateway Timeout</option>
                <option value="service_unavailable">HTTP 503 - Supplier GDS Unavailable</option>
                <option value="seat_unavailable">HTTP 409 - Seat/Room Inventory Exhausted</option>
              </select>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-surface-container-high">
              <span className="text-xs text-slate-300 font-sans font-medium">Disruption Waiver Active</span>
              <input
                type="checkbox"
                checked={disruptionWaiver}
                onChange={(e) => setDisruptionWaiver(e.target.checked)}
                className="w-3.5 h-3.5 accent-emerald-500 cursor-pointer"
              />
            </div>
            <p className="text-[10px] text-outline leading-relaxed font-sans">
              When <strong className="text-on-surface-variant">Disruption Waiver</strong> is enabled, involuntary rebookings and refund claims waive standard airline/rail cancellation penalties.
            </p>
          </motion.div>

          {/* Error Alert if failure injected */}
          {actionError && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="p-3.5 rounded-xl bg-rose-950/30 border border-rose-500/40 space-y-2 shadow-lg"
            >
              <div className="flex items-center gap-1.5 text-xs font-bold text-rose-400 font-mono">
                <AlertOctagon className="w-3.5 h-3.5" />
                <span>SIMULATED SUPPLIER API ERROR ({actionError.error_code || 'ERROR'})</span>
              </div>
              <p className="text-xs text-rose-200 font-sans">{actionError.message}</p>
              <pre className="p-2.5 rounded-lg bg-surface-container-lowest text-[10px] text-rose-300 overflow-x-auto font-mono border border-rose-500/20">
                {JSON.stringify(actionError, null, 2)}
              </pre>
            </motion.div>
          )}

          {/* Action Confirmation / Refund Inspector */}
          {actionResult && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-2 shadow-lg"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5 font-mono">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {actionResult.type}
                </span>
                <span className="text-[9px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                  MOCK CONFIRMATION
                </span>
              </div>
              <pre className="p-2.5 rounded-lg bg-surface-container-lowest border border-surface-container-high text-[10px] text-slate-300 overflow-x-auto max-h-72 font-mono leading-relaxed">
                {JSON.stringify(actionResult.data, null, 2)}
              </pre>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
