import React, { useEffect, useMemo, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, GeoJSON, Polyline } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { GeoJsonObject } from 'geojson';

import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

import { useMachines } from '../context/MachineContext';

// @ts-ignore
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow
});

interface FieldFeature {
  id: string;
  boundary?: GeoJsonObject;
  name: string;
}

const MapView: React.FC = () => {
  const { machines } = useMachines();
  const [fields, setFields] = useState<FieldFeature[]>([]);
  const [selectedMachine, setSelectedMachine] = useState<string | null>(null);

  useEffect(() => {
    async function loadFields() {
      try {
        const token = localStorage.getItem('agroPlannerToken');
        const headers: HeadersInit = {};
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/fields`, {
          headers,
          credentials: 'include'
        });
        if (!response.ok) {
          throw new Error('Unable to load fields');
        }
        const data = await response.json();
        setFields(data);
      } catch (error) {
        console.error('Error loading fields', error);
      }
    }
    loadFields();
  }, []);

  const center: [number, number] = [-31.2625, -61.4911];

  const machineHistory = useMemo(() => {
    if (!selectedMachine) {
      return [];
    }
    const machine = machines.find((m) => m.id === selectedMachine);
    if (!machine || !machine.latitude || !machine.longitude) {
      return [];
    }
    const { latitude, longitude } = machine;
    return [
      [latitude - 0.01, longitude - 0.01],
      [latitude - 0.005, longitude - 0.002],
      [latitude, longitude]
    ];
  }, [machines, selectedMachine]);

  return (
    <MapContainer center={center} zoom={8} style={{ height: '500px', width: '100%' }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="© OpenStreetMap contributors" />
      {fields
        .filter((field) => field.boundary)
        .map((field) => <GeoJSON key={field.id} data={field.boundary as GeoJsonObject} />)}
      <MarkerClusterGroup>
        {machines
          .filter((machine) => machine.latitude && machine.longitude)
          .map((machine) => (
            <Marker
              key={machine.id}
              position={[machine.latitude as number, machine.longitude as number]}
              eventHandlers={{
                click: () => setSelectedMachine(machine.id)
              }}
            >
              <Popup>
                <strong>{machine.name || machine.id}</strong>
                <br />
                {machine.status}
              </Popup>
            </Marker>
          ))}
      </MarkerClusterGroup>
      {machineHistory.length > 0 && <Polyline positions={machineHistory} color="green" />}
    </MapContainer>
  );
};

export default MapView;
