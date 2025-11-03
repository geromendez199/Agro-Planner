import React from 'react';
import { Alert as MuiAlert, AlertTitle, Button, Stack } from '@mui/material';
import { useTranslation } from 'react-i18next';

interface AlertProps {
  message?: string | null;
  onRetry?: () => void;
}

const Alert: React.FC<AlertProps> = ({ message, onRetry }) => {
  const { t } = useTranslation();
  if (!message) {
    return null;
  }

  return (
    <MuiAlert severity="error" action={onRetry && <Button color="inherit" onClick={onRetry}>{t('dashboard.retry')}</Button>}>
      <Stack spacing={1}>
        <AlertTitle>{t('alerts.error')}</AlertTitle>
        <span>{message}</span>
      </Stack>
    </MuiAlert>
  );
};

export default Alert;
