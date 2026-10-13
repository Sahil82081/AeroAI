import React, { useState, useEffect } from 'react';
import { apiService } from './services/api';
import { DashboardShell } from './components/DashboardShell';

export function App() {
  const [health, setHealth] = useState(null);
  const [user, setUser] = useState(null);
  const [journeys, setJourneys] = useState([]);
  const [disruptions, setDisruptions] = useState([]);
  const [recoveryPlans, setRecoveryPlans] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [inboxEmails, setInboxEmails] = useState([]);
  const [sampleEmails, setSampleEmails] = useState([]);
  const [graphData, setGraphData] = useState(null);
  const [latestImpactResult, setLatestImpactResult] = useState(null);
  const [forwardingLoading, setForwardingLoading] = useState(false);
  const [simulationLoading, setSimulationLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Health
      try {
        const healthData = await apiService.checkHealth();
        setHealth(healthData);
      } catch (hErr) {
        setHealth({ status: 'offline', database: 'disconnected' });
      }

      // 2. Samples
      try {
        const samples = await apiService.getSampleEmails();
        setSampleEmails(samples || []);
      } catch (sErr) {
        console.warn('Samples fetch error:', sErr);
      }

      // 3. Auth - Demo login if not logged in
      try {
        let currentUser;
        try {
          currentUser = await apiService.getCurrentUser();
        } catch {
          await apiService.login('traveler@example.com', 'password123');
          currentUser = await apiService.getCurrentUser();
        }
        setUser(currentUser);

        // 4. Ingestion Inbox
        try {
          const inbox = await apiService.getInboxEmails();
          setInboxEmails(inbox || []);
        } catch (iErr) {
          console.warn('Inbox fetch error:', iErr);
        }

        // 5. Journeys, Disruptions, Plans, Notifications, Graph
        const jList = await apiService.getJourneys();
        setJourneys(jList || []);

        if (jList && jList.length > 0) {
          const journeyId = jList[0].id;
          const [dList, pList, nList, gData] = await Promise.all([
            apiService.getDisruptions(journeyId),
            apiService.getRecoveryPlans(journeyId),
            apiService.getNotifications(),
            apiService.getJourneyGraph(journeyId)
          ]);
          setDisruptions(dList || []);
          setRecoveryPlans(pList || []);
          setNotifications(nList || []);
          setGraphData(gData || null);
        } else {
          setDisruptions([]);
          setRecoveryPlans([]);
          setNotifications([]);
          setGraphData(null);
        }
      } catch (authErr) {
        console.warn('API sync warning:', authErr);
      }
    } catch (err) {
      setError(err.message || 'Error communicating with backend');
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshGraph = async () => {
    if (journeys && journeys.length > 0) {
      try {
        const gData = await apiService.getJourneyGraph(journeys[0].id);
        setGraphData(gData);
      } catch (err) {
        console.error('Error refreshing graph:', err);
      }
    }
  };

  const handleForwardEmail = async (payload) => {
    setForwardingLoading(true);
    setError(null);
    try {
      await apiService.forwardEmail(payload);
      // Refresh inbox, journeys, and graph
      await loadData();
    } catch (err) {
      console.error('Error forwarding email:', err);
      setError(err.response?.data?.detail || 'Failed to forward email');
    } finally {
      setForwardingLoading(false);
    }
  };

  const handleSimulateDisruption = async (payload) => {
    setSimulationLoading(true);
    setError(null);
    try {
      const impact = await apiService.simulateDisruption(payload);
      setLatestImpactResult(impact);
      // Reload updated bookings, graph, and disruptions list
      await loadData();
    } catch (err) {
      console.error('Error simulating disruption:', err);
      setError(err.response?.data?.detail || 'Failed to simulate disruption');
    } finally {
      setSimulationLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <DashboardShell
      user={user}
      health={health}
      journeys={journeys}
      disruptions={disruptions}
      recoveryPlans={recoveryPlans}
      notifications={notifications}
      inboxEmails={inboxEmails}
      sampleEmails={sampleEmails}
      graphData={graphData}
      latestImpactResult={latestImpactResult}
      onForwardEmail={handleForwardEmail}
      forwardingLoading={forwardingLoading}
      onSimulateDisruption={handleSimulateDisruption}
      simulationLoading={simulationLoading}
      onRefreshGraph={handleRefreshGraph}
      onRefresh={loadData}
      loading={loading}
      error={error}
    />
  );
}

export default App;
