/**
 * Utility functions for handling API errors consistently across the application
 */

interface ValidationError {
  type: string;
  loc: string[];
  msg: string;
  input?: any;
}

/**
 * Extract a user-friendly error message from an API error response
 * Handles FastAPI error formats including validation errors
 */
export const getErrorMessage = (error: any, defaultMessage: string = 'An error occurred'): string => {
  // Check if error exists
  if (!error) {
    return defaultMessage;
  }

  // Handle axios error response
  if (error.response?.data) {
    const data = error.response.data;

    // FastAPI validation errors (array format)
    if (Array.isArray(data.detail)) {
      const validationErrors = data.detail
        .map((err: ValidationError) => {
          const field = err.loc.slice(1).join('.'); // Remove 'body' from location
          return `${field}: ${err.msg}`;
        })
        .join('; ');
      return validationErrors || defaultMessage;
    }

    // FastAPI single error (string format)
    if (typeof data.detail === 'string') {
      return data.detail;
    }

    // Legacy error format
    if (data.error?.message) {
      return data.error.message;
    }

    // Generic message field
    if (data.message) {
      return data.message;
    }
  }

  // Handle error message directly
  if (error.message) {
    return error.message;
  }

  // Network errors
  if (error.request && !error.response) {
    return 'Network error: Unable to reach the server';
  }

  return defaultMessage;
};

/**
 * Format validation errors for display
 */
export const formatValidationErrors = (errors: ValidationError[]): string => {
  return errors
    .map((err) => {
      const field = err.loc.slice(1).join('.').replace('_', ' ');
      const fieldName = field.charAt(0).toUpperCase() + field.slice(1);
      return `${fieldName}: ${err.msg}`;
    })
    .join('\n');
};

/**
 * Check if error is a validation error
 */
export const isValidationError = (error: any): boolean => {
  return error?.response?.status === 422 || 
         (Array.isArray(error?.response?.data?.detail) && 
          error.response.data.detail.length > 0);
};

/**
 * Check if error is an authentication error
 */
export const isAuthError = (error: any): boolean => {
  return error?.response?.status === 401 || error?.response?.status === 403;
};

/**
 * Check if error is a not found error
 */
export const isNotFoundError = (error: any): boolean => {
  return error?.response?.status === 404;
};

/**
 * Check if error is a conflict error (duplicate, etc.)
 */
export const isConflictError = (error: any): boolean => {
  return error?.response?.status === 409 || error?.response?.status === 400;
};
