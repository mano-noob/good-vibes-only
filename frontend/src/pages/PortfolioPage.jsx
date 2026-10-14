import { Alert, Box, Grid, Stack, Typography } from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import LoadingState from "../components/LoadingState";
import SummaryCard from "../components/cards/SummaryCard";
import PriorityChip from "../components/chips/PriorityChip";
import SignalChip from "../components/chips/SignalChip";
import usePortfolio from "../hooks/usePortfolio";

function PortfolioPage() {
  const { loading, error, rows, portfolio, portfolioPnl, pnlPercent, reload } =
    usePortfolio();
  const positionsCount = rows.length;
  const holdings = portfolio.positions || [];

  const columns = [
    {
      field: "symbol",
      headerName: "Symbol",
      minWidth: 130,
      flex: 1,
      sortable: true,
    },
    {
      field: "quantity",
      headerName: "Quantity",
      type: "number",
      minWidth: 110,
      flex: 0.8,
    },
    {
      field: "entry",
      headerName: "Entry",
      type: "number",
      minWidth: 120,
      flex: 1,
      valueFormatter: (params) =>
        `₹${Number(params.value || 0).toLocaleString()}`,
    },
    {
      field: "current",
      headerName: "Current",
      type: "number",
      minWidth: 120,
      flex: 1,
      valueFormatter: (params) =>
        `₹${Number(params.value || 0).toLocaleString()}`,
    },
    {
      field: "marketValue",
      headerName: "Market Value",
      type: "number",
      minWidth: 150,
      flex: 1.2,
      valueGetter: (value) => Number(value || 0),
      valueFormatter: (params) =>
        `₹${Number(params.value || 0).toLocaleString()}`,
      cellClassName: (params) =>
        params.value >= 0 ? "positive-value" : "negative-value",
    },
    {
      field: "pnl",
      headerName: "PnL",
      type: "number",
      minWidth: 120,
      flex: 1,
      valueGetter: (value) => Number(value || 0),
      valueFormatter: (params) =>
        `₹${Number(params.value || 0).toLocaleString()}`,
      cellClassName: (params) =>
        params.value >= 0 ? "positive-value" : "negative-value",
    },
    {
      field: "pnlPercent",
      headerName: "PnL %",
      type: "number",
      minWidth: 120,
      flex: 1,
      valueGetter: (value) => Number(value || 0),
      valueFormatter: (params) => `${Number(params.value || 0).toFixed(2)}%`,
      cellClassName: (params) =>
        params.value >= 0 ? "positive-value" : "negative-value",
    },
    {
      field: "decision",
      headerName: "Decision",
      minWidth: 120,
      flex: 1,
      renderCell: (params) => <SignalChip signal={params.value} />,
    },
    {
      field: "priority",
      headerName: "Priority",
      minWidth: 110,
      flex: 0.8,
      renderCell: (params) => <PriorityChip priority={params.value} />,
    },
  ];

  return (
    <LoadingState loading={loading} error={error} onRetry={reload}>
      <Stack spacing={3}>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 1,
          }}
        >
          <Typography variant="h4">Portfolio</Typography>
          <Typography variant="body2" color="text.secondary">
            {holdings.length} active positions
          </Typography>
        </Box>

        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <SummaryCard
              title="Net Worth"
              value={`₹${Number(portfolio.net_worth || 0).toLocaleString()}`}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <SummaryCard
              title="Cash"
              value={`₹${Number(portfolio.cash || 0).toLocaleString()}`}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <SummaryCard
              title="Invested"
              value={`₹${Number(portfolio.invested || 0).toLocaleString()}`}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <SummaryCard
              title="PnL"
              value={`₹${Number(portfolioPnl || portfolio.unrealized_pnl || 0).toLocaleString()}`}
              color={portfolioPnl >= 0 ? "success.main" : "error.main"}
              subtitle={`${pnlPercent.toFixed(2)}% overall`}
            />
          </Grid>
        </Grid>

        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <SummaryCard
              title="PnL %"
              value={`${pnlPercent.toFixed(2)}%`}
              color={pnlPercent >= 0 ? "success.main" : "error.main"}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <SummaryCard title="Positions" value={positionsCount} />
          </Grid>
        </Grid>

        {rows.length ? (
          <Box sx={{ height: 480, width: "100%" }}>
            <DataGrid
              rows={rows}
              columns={columns}
              initialState={{
                sorting: {
                  sortModel: [{ field: "marketValue", sort: "desc" }],
                },
                pagination: { paginationModel: { pageSize: 8 } },
              }}
              pageSizeOptions={[5, 8, 10, 20]}
              disableRowSelectionOnClick
              sortingOrder={["asc", "desc"]}
              sx={{
                bgcolor: "background.paper",
                borderRadius: 2,
                border: "1px solid rgba(255,255,255,0.08)",
                "& .MuiDataGrid-columnHeaders": {
                  backgroundColor: "#1e1e1e",
                  position: "sticky",
                  top: 0,
                  zIndex: 1,
                },
                "& .MuiDataGrid-row:nth-of-type(even)": {
                  backgroundColor: "rgba(255,255,255,0.02)",
                },
                "& .MuiDataGrid-cell": { color: "#fff" },
                "& .positive-value": {
                  color: "#4caf50 !important",
                  fontWeight: 700,
                },
                "& .negative-value": {
                  color: "#f44336 !important",
                  fontWeight: 700,
                },
              }}
              disableColumnMenu={false}
              pagination
            />
          </Box>
        ) : (
          <Alert severity="info">No portfolio holdings were found.</Alert>
        )}
      </Stack>
    </LoadingState>
  );
}

export default PortfolioPage;
