import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Alert from '../components/Alert';
import '../i18n';

describe('Alert component', () => {
  it('renders message and handles retry', () => {
    const onRetry = jest.fn();
    render(<Alert message="Error" onRetry={onRetry} />);
    expect(screen.getByText('Error')).toBeInTheDocument();
    const button = screen.getByRole('button');
    fireEvent.click(button);
    expect(onRetry).toHaveBeenCalled();
  });
});
