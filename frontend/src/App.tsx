/**
 * Main App component with routing.
 */

import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Navigation } from './components/Navigation';
import { ChatButton } from './components/Chat/ChatButton';
import { OrdersDashboard } from './pages/OrdersDashboard';
import { CampaignsDashboard } from './pages/CampaignsDashboard';
import { CustomersDashboard } from './pages/CustomersDashboard';

function App() {
  return (
    <HashRouter>
      <div style={{ minHeight: '100vh', backgroundColor: 'var(--off-white)' }}>
        <Navigation />
        <Routes>
          <Route path="/" element={<Navigate to="/orders" replace />} />
          <Route path="/orders" element={<OrdersDashboard />} />
          <Route path="/campaigns" element={<CampaignsDashboard />} />
          <Route path="/customers" element={<CustomersDashboard />} />
          <Route path="*" element={<Navigate to="/orders" replace />} />
        </Routes>
        <ChatButton />
      </div>
    </HashRouter>
  );
}

export default App;
