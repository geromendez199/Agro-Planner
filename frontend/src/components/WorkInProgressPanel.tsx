import React, { useEffect, useState } from 'react';
import { Card, CardContent, LinearProgress, List, ListItem, ListItemText, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';

interface WorkPlan {
  id: number;
  field_id: string;
  type: string;
  start_date: string;
  end_date: string;
  status: string;
}

const statusProgress = (status: string): number => {
  switch (status.toLowerCase()) {
    case 'completed':
      return 100;
    case 'in_progress':
      return 60;
    default:
      return 20;
  }
};

interface WorkInProgressPanelProps {
  reload: number;
}

const WorkInProgressPanel: React.FC<WorkInProgressPanelProps> = ({ reload }) => {
  const { t } = useTranslation();
  const [plans, setPlans] = useState<WorkPlan[]>([]);

  useEffect(() => {
    async function fetchPlans() {
      try {
        const token = localStorage.getItem('agroPlannerToken');
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/work-plans`, {
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {})
          }
        });
        if (response.ok) {
          const data = await response.json();
          setPlans(data);
        }
      } catch (error) {
        console.error('Error loading work plans', error);
      }
    }
    fetchPlans();
  }, [reload]);

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {t('dashboard.activeWork')}
        </Typography>
        <List>
          {plans.map((plan) => (
            <ListItem key={plan.id} divider>
              <ListItemText
                primary={`${plan.field_id} · ${plan.type}`}
                secondary={`${t('dashboard.status')}: ${plan.status}`}
              />
              <LinearProgress
                variant="determinate"
                value={statusProgress(plan.status)}
                sx={{ width: 160, ml: 2 }}
              />
            </ListItem>
          ))}
          {plans.length === 0 && (
            <Typography variant="body2">{t('dashboard.noWork')}</Typography>
          )}
        </List>
      </CardContent>
    </Card>
  );
};

export default WorkInProgressPanel;
