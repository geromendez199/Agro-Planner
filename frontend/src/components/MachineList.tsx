import React from 'react';
import { Card, CardContent, CircularProgress, List, ListItem, ListItemText, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';

import { useMachines } from '../context/MachineContext';
import Alert from './Alert';

const MachineList: React.FC = () => {
  const { machines, loading, error, refresh } = useMachines();
  const { t } = useTranslation();

  if (loading) {
    return (
      <Card>
        <CardContent sx={{ display: 'flex', justifyContent: 'center' }}>
          <CircularProgress />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {t('dashboard.machines')}
        </Typography>
        <Alert message={error} onRetry={refresh} />
        {machines.length === 0 && !error ? (
          <Typography variant="body2">{t('dashboard.noMachines')}</Typography>
        ) : (
          <List>
            {machines.map((machine) => (
              <ListItem key={machine.id} divider>
                <ListItemText
                  primary={machine.name || machine.id}
                  secondary={`${machine.category ?? ''} ${machine.status ? `· ${machine.status}` : ''}`.trim()}
                />
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  );
};

export default MachineList;
