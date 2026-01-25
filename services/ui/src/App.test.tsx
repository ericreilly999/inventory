import React from 'react';
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import App from './App';
import { AuthProvider } from './contexts/AuthContext';

test('renders without crashing', () => {
  const { container } = render(
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  );
  // Basic smoke test - just ensure the app renders
  expect(container).toBeInTheDocument();
});
