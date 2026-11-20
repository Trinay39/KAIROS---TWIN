import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { DemoProvider } from './context/DemoContext';
import Layout from './layouts/Layout';
import CommandCenter from './pages/CommandCenter';
import DigitalTwin from './pages/DigitalTwin';
import RiskIntelligence from './pages/RiskIntelligence';
import WhatIfLab from './pages/WhatIfLab';
import AgentControl from './pages/AgentControl';
import FacultyView from './pages/FacultyView';
import Recommendations from './pages/Recommendations';
import StudentHistory from './pages/StudentHistory';

export default function App() {
  return (
    <BrowserRouter>
      <DemoProvider>
        <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<CommandCenter />} />
          <Route path="twin" element={<DigitalTwin />} />
          <Route path="risk" element={<RiskIntelligence />} />
          <Route path="whatif" element={<WhatIfLab />} />
          <Route path="agents" element={<AgentControl />} />
          <Route path="history" element={<StudentHistory />} />
          <Route path="faculty" element={<FacultyView />} />
          <Route path="recommend" element={<Recommendations />} />
        </Route>
      </Routes>
      </DemoProvider>
    </BrowserRouter>
  );
}
