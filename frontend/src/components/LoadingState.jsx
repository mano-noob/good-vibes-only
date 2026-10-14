import { Box, Button, Grid, Skeleton, Stack, Typography } from "@mui/material";

function LoadingState({ loading, error, onRetry, children }) {
  if (loading) {
    return (
      <Box sx={{ py: 4 }}>
        <Stack spacing={2} sx={{ mb: 3 }}>
          <Skeleton variant="text" width="28%" height={34} />
          <Skeleton variant="text" width="18%" height={22} />
        </Stack>

        <Grid container spacing={2} sx={{ mb: 3 }}>
          {[1, 2, 3, 4].map((item) => (
            <Grid size={{ xs: 12, sm: 6, md: 3 }} key={item}>
              <Skeleton
                variant="rectangular"
                height={120}
                sx={{ borderRadius: 2 }}
              />
            </Grid>
          ))}
        </Grid>

        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Skeleton
              variant="rectangular"
              height={220}
              sx={{ borderRadius: 2 }}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Skeleton
              variant="rectangular"
              height={220}
              sx={{ borderRadius: 2 }}
            />
          </Grid>
        </Grid>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ py: 6, display: "flex", justifyContent: "center" }}>
        <Box
          sx={{
            maxWidth: 480,
            width: "100%",
            textAlign: "center",
            p: 3,
            borderRadius: 3,
            border: "1px solid rgba(255,255,255,0.08)",
            bgcolor: "background.paper",
          }}
        >
          <Typography variant="h6" gutterBottom>
            We could not load the dashboard right now.
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {error}
          </Typography>
          <Button variant="contained" onClick={onRetry}>
            Retry
          </Button>
        </Box>
      </Box>
    );
  }

  return children;
}

export default LoadingState;
