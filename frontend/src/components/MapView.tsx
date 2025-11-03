import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';

// Fix icon issue in Leaflet when using Webpack/Vite
import L from 'leaflet';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

// Configure default icon
// @ts-ignore
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

interface MachinePosition {
  id: string;
  name?: string;
  latitude?: number;
  longitude?: number;
}

const MapView: React.FC = () => {
  const [machines, setMachines] = useState<MachinePosition[]>([]);

  useEffect(() => {
    async function loadPositions() {
      try {
        const response = await axios.get('/api/machines');
        setMachines(response.data);
      } catch (err) {
        console.error('Error al cargar posiciones');
      }
    }
    loadPositions();
  }, []);

  // Coordenadas aproximadas de Rafaela (Argentina) como centro inicial
  const center: [number, number] = [-31.2625, -61.4911];

  return (
    <div>
      <h2>Mapa de Maquinaria</h2>
      <MapContainer center={center} zoom={9} style={{ height: '400px', width: '100%' }}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="© OpenStreetMap contributors" />
        {machines
          .filter((m) => m.latitude !== undefined && m.longitude !== undefined)
          .map((m) => (
            <Marker key={m.id} position={[m.latitude as number, m.longitude as number]}>
              <Popup>
                <strong>{m.name || m.id}</strong>
                <br />
                Lat: {m.latitude?.toFixed(4)}
                <br />
                Lon: {m.longitude?.toFixed(4)}
              </Popup>
            </Marker>
          ))}
      </MapContainer>
    </div>
  );
};

export default MapView;