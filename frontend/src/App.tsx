import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { CssBaseline } from '@mui/material';

import Dashboard from './pages/Dashboard';
import { MachineProvider } from './context/MachineContext';

function App() {
  return (
    <MachineProvider>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<Dashboard />} />
        </Routes>
      </Router>
    </MachineProvider>
  );
}

export default App;
