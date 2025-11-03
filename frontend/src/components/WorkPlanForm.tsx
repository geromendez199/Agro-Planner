import React, { useState } from 'react';
import { Button, Card, CardContent, MenuItem, Snackbar, Stack, TextField, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';

interface WorkPlanFormProps {
  onCreated?: () => void;
}

const WorkPlanForm: React.FC<WorkPlanFormProps> = ({ onCreated }) => {
  const { t } = useTranslation();
  const [fieldId, setFieldId] = useState('');
  const [workType, setWorkType] = useState('SIEMBRA');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [status, setStatus] = useState('pending');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!fieldId || !startDate || !endDate) {
      setError(t('workPlan.required'));
      return;
    }
    if (new Date(startDate) > new Date(endDate)) {
      setError(t('workPlan.required'));
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('agroPlannerToken');
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/work-plans`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          field_id: fieldId,
          type: workType,
          start_date: startDate,
          end_date: endDate,
          status
        })
      });
      if (!response.ok) {
        throw new Error('Failed to create work plan');
      }
      setSuccess(true);
      setFieldId('');
      setStartDate('');
      setEndDate('');
      setStatus('pending');
      onCreated?.();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {t('dashboard.newPlan')}
        </Typography>
        <form onSubmit={handleSubmit}>
          <Stack spacing={2}>
            <TextField
              label={t('workPlan.field')}
              value={fieldId}
              onChange={(event) => setFieldId(event.target.value)}
              required
            />
            <TextField select label={t('workPlan.type')} value={workType} onChange={(event) => setWorkType(event.target.value)}>
              <MenuItem value="SIEMBRA">SIEMBRA</MenuItem>
              <MenuItem value="COSECHA">COSECHA</MenuItem>
              <MenuItem value="FERTILIZACION">FERTILIZACION</MenuItem>
            </TextField>
            <TextField
              label={t('workPlan.startDate')}
              type="date"
              InputLabelProps={{ shrink: true }}
              value={startDate}
              onChange={(event) => setStartDate(event.target.value)}
              required
            />
            <TextField
              label={t('workPlan.endDate')}
              type="date"
              InputLabelProps={{ shrink: true }}
              value={endDate}
              onChange={(event) => setEndDate(event.target.value)}
              required
            />
            <TextField label={t('workPlan.status')} value={status} onChange={(event) => setStatus(event.target.value)} />
            {error && <Typography color="error">{error}</Typography>}
            <Button type="submit" variant="contained" disabled={loading}>
              {t('workPlan.create')}
            </Button>
          </Stack>
        </form>
        <Snackbar open={success} autoHideDuration={3000} onClose={() => setSuccess(false)} message={t('workPlan.success')} />
      </CardContent>
    </Card>
  );
};

export default WorkPlanForm;
