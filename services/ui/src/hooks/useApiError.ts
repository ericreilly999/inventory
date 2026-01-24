import { useState, useCallback } from 'react';

interface ApiErrorState {
  error: any;
  requestPayload?: any;
  endpoint?: string;
  method?: string;
}

export const useApiError = () => {
  const [errorState, setErrorState] = useState<ApiErrorState | null>(null);

  const setError = useCallback((
    error: any,
    options?: {
      requestPayload?: any;
      endpoint?: string;
      method?: string;
    }
  ) => {
    setErrorState({
      error,
      requestPayload: options?.requestPayload,
      endpoint: options?.endpoint,
      method: options?.method,
    });
  }, []);

  const clearError = useCallback(() => {
    setErrorState(null);
  }, []);

  return {
    errorState,
    setError,
    clearError,
    hasError: errorState !== null,
  };
};
