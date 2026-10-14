import {
  Alert,
  Box,
  InputAdornment,
  Stack,
  TextField,
  Typography,
  Switch,
} from "@mui/material";
import SearchOutlinedIcon from "@mui/icons-material/SearchOutlined";
import { DataGrid } from "@mui/x-data-grid";
import LoadingState from "../components/LoadingState";
import PriorityChip from "../components/chips/PriorityChip";
import SignalChip from "../components/chips/SignalChip";
import useWatchlist from "../hooks/useWatchlist";

function WatchlistPage() {
  const {
    rows,
    setRows,
    query,
    setQuery,
    filteredRows,
    loading,
    error,
    reload,
  } = useWatchlist();

  const formatNumericValue = (value, decimals = 0) => {
    const numericValue = Number(value ?? 0);
    const safeValue = Number.isFinite(numericValue) ? numericValue : 0;

    if (decimals > 0) {
      return safeValue.toFixed(decimals);
    }

    return safeValue.toLocaleString();
  };

  const columns = [
    {
      field: "rank",
      headerName: "Rank",
      type: "number",
      minWidth: 80,
      flex: 0.5,
      sortable: true,
      filterable: true,
    },
    {
      field: "symbol",
      headerName: "Symbol",
      minWidth: 130,
      flex: 1,
      sortable: true,
      filterable: true,
    },
    {
      field: "priority",
      headerName: "Priority",
      minWidth: 110,
      flex: 0.8,
      sortable: true,
      filterable: true,
      renderCell: (params) => <PriorityChip priority={params.value} />,
    },
    {
      field: "signal",
      headerName: "Signal",
      minWidth: 150,
      flex: 1,
      sortable: true,
      filterable: true,
      renderCell: (params) => <SignalChip signal={params.value} />,
    },
    {
      field: "readiness",
      headerName: "Readiness",
      type: "number",
      minWidth: 110,
      flex: 0.8,
      sortable: true,
      filterable: true,
    },
    {
      field: "relativeStrength",
      headerName: "Relative Strength",
      type: "number",
      minWidth: 160,
      flex: 1,
      sortable: true,
      filterable: true,
      valueFormatter: (params) =>
        formatNumericValue(params?.value ?? params ?? 0, 1),
    },
    {
      field: "close",
      headerName: "Close",
      type: "number",
      minWidth: 120,
      flex: 1,
      sortable: true,
      filterable: true,
      valueFormatter: (params) =>
        `₹${formatNumericValue(params?.value ?? params ?? 0)}`,
    },
    {
      field: "ema20",
      headerName: "EMA20",
      type: "number",
      minWidth: 120,
      flex: 1,
      sortable: true,
      filterable: true,
      valueFormatter: (params) =>
        `₹${formatNumericValue(params?.value ?? params ?? 0)}`,
    },
    {
      field: "ema50",
      headerName: "EMA50",
      type: "number",
      minWidth: 120,
      flex: 1,
      sortable: true,
      filterable: true,
      valueFormatter: (params) =>
        `₹${formatNumericValue(params?.value ?? params ?? 0)}`,
    },
    {
      field: "ema200",
      headerName: "EMA200",
      type: "number",
      minWidth: 130,
      flex: 1,
      sortable: true,
      filterable: true,
      valueFormatter: (params) =>
        `₹${formatNumericValue(params?.value ?? params ?? 0)}`,
    },
    {
      field: "atr",
      headerName: "ATR",
      type: "number",
      minWidth: 100,
      flex: 0.8,
      sortable: true,
      filterable: true,
      valueFormatter: (params) =>
        formatNumericValue(params?.value ?? params ?? 0, 1),
    },
    {
      field: "rsi",
      headerName: "RSI",
      type: "number",
      minWidth: 100,
      flex: 0.8,
      sortable: true,
      filterable: true,
      valueFormatter: (params) =>
        formatNumericValue(params?.value ?? params ?? 0, 1),
    },
    {
      field: "explanation",
      headerName: "Explanation",
      minWidth: 220,
      flex: 1.8,
      sortable: true,
      filterable: true,
    },
    {
      field: "decision",
      headerName: "Decision",
      minWidth: 140,
      flex: 1,
      sortable: true,
      filterable: true,
      renderCell: (params) => <SignalChip signal={params.value} />,
    },
    {
      field: "enable",
      headerName: "Enable",
      type: "boolean",
      minWidth: 100,
      flex: 0.7,
      sortable: true,
      filterable: true,
      renderCell: (params) => (
        <Switch
          checked={Boolean(params.value)}
          onChange={(event) => {
            const nextValue = event.target.checked;
            setRows((currentRows) =>
              currentRows.map((row) =>
                row.id === params.id ? { ...row, enable: nextValue } : row,
              ),
            );
          }}
          size="small"
          color={Boolean(params.value) ? "success" : "default"}
        />
      ),
    },
  ];

  return (
    <LoadingState loading={loading} error={error} onRetry={reload}>
      <Stack spacing={3}>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={2}
          sx={{
            justifyContent: "space-between",
            alignItems: { xs: "flex-start", sm: "center" },
          }}
        >
          <Typography variant="h4">Watchlist</Typography>
          <TextField
            size="small"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Quick Search"
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchOutlinedIcon fontSize="small" />
                  </InputAdornment>
                ),
              },
            }}
            sx={{ width: { xs: "100%", sm: 280 } }}
          />
        </Stack>

        {!rows.length && !loading ? (
          <Alert severity="info">No watchlist items are available.</Alert>
        ) : (
          <Box sx={{ height: 620, width: "100%" }}>
            <DataGrid
              rows={filteredRows}
              columns={columns}
              checkboxSelection
              disableRowSelectionOnClick
              disableColumnMenu={false}
              disableColumnResize={false}
              pageSizeOptions={[5, 10, 20]}
              pagination
              sortingOrder={["asc", "desc"]}
              initialState={{
                pagination: { paginationModel: { pageSize: 10 } },
                sorting: { sortModel: [{ field: "rank", sort: "asc" }] },
                filter: { filterModel: { items: [] } },
              }}
              sx={{
                bgcolor: "background.paper",
                borderRadius: 2,
                border: "1px solid rgba(255,255,255,0.08)",
                "& .MuiDataGrid-columnHeaders": { backgroundColor: "#1b1b1b" },
                "& .MuiDataGrid-row:nth-of-type(even)": {
                  backgroundColor: "rgba(255,255,255,0.02)",
                },
                "& .MuiDataGrid-row:nth-of-type(odd)": {
                  backgroundColor: "rgba(12,12,12,0.6)",
                },
                "& .MuiDataGrid-cell": {
                  borderBottom: "1px solid rgba(255,255,255,0.06)",
                },
                "& .MuiDataGrid-virtualScroller": {
                  background: "rgba(10, 10, 10, 0.2)",
                },
              }}
            />
          </Box>
        )}
      </Stack>
    </LoadingState>
  );
}

export default WatchlistPage;
