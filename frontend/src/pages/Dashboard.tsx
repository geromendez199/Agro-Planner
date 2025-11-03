import React from 'react';
import MachineList from '../components/MachineList';
import MapView from '../components/MapView';

const Dashboard: React.FC = () => {
  return (
    <div style={{ padding: '1rem' }}>
      <h1>Panel de Control</h1>
      <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
        <div style={{ flex: '1 1 300px', minWidth: '300px' }}>
          <MachineList />
        </div>
        <div style={{ flex: '2 1 500px', minWidth: '500px' }}>
          <MapView />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;