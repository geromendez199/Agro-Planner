import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

export interface Machine {
  id: string;
  name?: string;
  category?: string;
  serial_number?: string;
  status?: string;
  latitude?: number;
  longitude?: number;
}

interface MachineContextState {
  machines: Machine[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

const MachineContext = createContext<MachineContextState | undefined>(undefined);

interface ProviderProps {
  children: React.ReactNode;
}

export const MachineProvider: React.FC<ProviderProps> = ({ children }) => {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('agroPlannerToken');
      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/machines`, {
        headers,
        credentials: 'include'
      });
      if (!response.ok) {
        throw new Error('Failed to load machines');
      }
      const data: Machine[] = await response.json();
      setMachines(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  const value = useMemo(
    () => ({ machines, loading, error, refresh }),
    [machines, loading, error, refresh]
  );

  useEffect(() => {
    refresh();
  }, [refresh]);

  return <MachineContext.Provider value={value}>{children}</MachineContext.Provider>;
};

export const useMachines = (): MachineContextState => {
  const context = useContext(MachineContext);
  if (!context) {
    throw new Error('useMachines must be used within a MachineProvider');
  }
  return context;
};
