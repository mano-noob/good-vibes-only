import { Alert, Box, Button, Typography } from "@mui/material";

function ErrorBoundary({ error, onRetry }) {
  return (
    <Box sx={{ py: 4 }}>
      <Alert severity="error" sx={{ mb: 2 }}>
        <Typography variant="h6">Something went wrong</Typography>
        <Typography variant="body2">
          {error || "Unexpected error occurred."}
        </Typography>
      </Alert>
      {onRetry && (
        <Button variant="contained" onClick={onRetry}>
          Retry
        </Button>
      )}
    </Box>
  );
}

export default ErrorBoundary;
