import React, { useState } from 'react';
import {
  Alert,
  AlertTitle,
  Collapse,
  IconButton,
  Box,
  Typography,
  Divider,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  ContentCopy as ContentCopyIcon,
} from '@mui/icons-material';
import { getErrorMessage } from '../utils/errorHandler';

interface ErrorDetailsProps {
  error: any;
  message?: string;
  requestPayload?: any;
  endpoint?: string;
  method?: string;
  onClose?: () => void;
}

const ErrorDetails: React.FC<ErrorDetailsProps> = ({
  error,
  message,
  requestPayload,
  endpoint,
  method,
  onClose,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  // Use provided message or extract from error
  const errorMessage = message || getErrorMessage(error, 'An unknown error occurred');
  
  const statusCode = error?.response?.status;
  const statusText = error?.response?.statusText;
  const timestamp = new Date().toISOString();

  // Build detailed error object
  const errorDetails = {
    timestamp,
    message: errorMessage,
    statusCode,
    statusText,
    method,
    endpoint,
    requestPayload,
    responseData: error?.response?.data,
    stack: error?.stack,
  };

  const handleCopy = () => {
    const errorText = JSON.stringify(errorDetails, null, 2);
    navigator.clipboard.writeText(errorText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Alert 
      severity="error" 
      onClose={onClose}
      sx={{ mb: 2 }}
    >
      <AlertTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <span>Error</span>
          {statusCode && (
            <Typography variant="caption" sx={{ opacity: 0.7 }}>
              ({statusCode} {statusText})
            </Typography>
          )}
        </Box>
        <Box>
          <IconButton
            size="small"
            onClick={handleCopy}
            title={copied ? 'Copied!' : 'Copy error details'}
            sx={{ mr: 1 }}
          >
            <ContentCopyIcon fontSize="small" />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => setExpanded(!expanded)}
            title={expanded ? 'Hide details' : 'Show details'}
          >
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>
      </AlertTitle>
      
      <Typography variant="body2" sx={{ mb: 1 }}>
        {errorMessage}
      </Typography>

      <Collapse in={expanded}>
        <Divider sx={{ my: 1 }} />
        
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Error Details
          </Typography>
          
          {method && endpoint && (
            <Box sx={{ mb: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Request:
              </Typography>
              <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                {method} {endpoint}
              </Typography>
            </Box>
          )}

          {requestPayload && (
            <Box sx={{ mb: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Request Payload:
              </Typography>
              <Box
                sx={{
                  backgroundColor: 'rgba(0, 0, 0, 0.05)',
                  p: 1,
                  borderRadius: 1,
                  overflow: 'auto',
                  maxHeight: '200px',
                }}
              >
                <pre style={{ margin: 0, fontSize: '0.75rem' }}>
                  {JSON.stringify(requestPayload, null, 2)}
                </pre>
              </Box>
            </Box>
          )}

          {error?.response?.data && (
            <Box sx={{ mb: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Response Data:
              </Typography>
              <Box
                sx={{
                  backgroundColor: 'rgba(0, 0, 0, 0.05)',
                  p: 1,
                  borderRadius: 1,
                  overflow: 'auto',
                  maxHeight: '200px',
                }}
              >
                <pre style={{ margin: 0, fontSize: '0.75rem' }}>
                  {JSON.stringify(error.response.data, null, 2)}
                </pre>
              </Box>
            </Box>
          )}

          <Box sx={{ mb: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Timestamp:
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
              {timestamp}
            </Typography>
          </Box>

          {error?.stack && (
            <Box>
              <Typography variant="caption" color="text.secondary">
                Stack Trace:
              </Typography>
              <Box
                sx={{
                  backgroundColor: 'rgba(0, 0, 0, 0.05)',
                  p: 1,
                  borderRadius: 1,
                  overflow: 'auto',
                  maxHeight: '150px',
                }}
              >
                <pre style={{ margin: 0, fontSize: '0.7rem' }}>
                  {error.stack}
                </pre>
              </Box>
            </Box>
          )}
        </Box>
      </Collapse>
    </Alert>
  );
};

export default ErrorDetails;
