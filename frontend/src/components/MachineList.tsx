import React, { useEffect, useState } from 'react';
import axios from 'axios';

interface Machine {
  id: string;
  name?: string;
  category?: string;
  serial_number?: string;
  status?: string;
  latitude?: number;
  longitude?: number;
}

const MachineList: React.FC = () => {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    async function fetchMachines() {
      try {
        const response = await axios.get<Machine[]>('/api/machines');
        setMachines(response.data);
      } catch (err) {
        setError('No se pudo obtener la lista de máquinas');
      } finally {
        setLoading(false);
      }
    }
    fetchMachines();
  }, []);

  if (loading) return <p>Cargando máquinas…</p>;
  if (error) return <p>{error}</p>;

  return (
    <div>
      <h2>Maquinaria</h2>
      {machines.length === 0 && <p>No hay máquinas registradas.</p>}
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {machines.map((m) => (
          <li key={m.id} style={{ marginBottom: '0.5rem', borderBottom: '1px solid #ccc', paddingBottom: '0.5rem' }}>
            <strong>{m.name || m.id}</strong>
            {m.category && <span> • {m.category}</span>}
            {m.status && <span> • {m.status}</span>}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default MachineList;