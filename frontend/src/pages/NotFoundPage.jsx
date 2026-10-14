import { Box, Typography } from "@mui/material";

function NotFoundPage() {
  return (
    <Box sx={{ py: 8, textAlign: "center" }}>
      <Typography variant="h3">404</Typography>
      <Typography variant="body1" color="text.secondary">
        The page you requested does not exist.
      </Typography>
    </Box>
  );
}

export default NotFoundPage;
