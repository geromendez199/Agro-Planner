import React, { useState } from 'react';
import { Container, Grid, Stack, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';

import MachineList from '../components/MachineList';
import MapView from '../components/MapView';
import WorkPlanForm from '../components/WorkPlanForm';
import WorkInProgressPanel from '../components/WorkInProgressPanel';

const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  const [reload, setReload] = useState(0);

  const handlePlanCreated = () => setReload((value) => value + 1);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={3}>
        <Typography variant="h4">{t('dashboard.title')}</Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Stack spacing={3}>
              <MachineList />
              <WorkPlanForm onCreated={handlePlanCreated} />
            </Stack>
          </Grid>
          <Grid item xs={12} md={8}>
            <MapView />
          </Grid>
        </Grid>
        <WorkInProgressPanel reload={reload} />
      </Stack>
    </Container>
  );
};

export default Dashboard;
