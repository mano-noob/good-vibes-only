import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Box, Card, CardContent, Grid, Stack, Typography } from "@mui/material";

function DashboardCharts({
  holdings = [],
  watchlist = [],
  portfolioSummary = {},
  summary = {},
  readinessDistributionData = [],
}) {
  const pieColors = ["#4caf50", "#29b6f6", "#ffb300", "#ef5350", "#ab47bc"];
  const currentPortfolioValue = Number(
    portfolioSummary.portfolio_value || summary.portfolio?.net_worth || 0,
  );
  const currentCash = Number(
    portfolioSummary.cash || summary.portfolio?.cash || 0,
  );
  const currentInvested = Number(
    summary.portfolio?.invested ||
      Math.max(currentPortfolioValue - currentCash, 0),
  );

  const chartData = [
    { name: "Mon", readiness: 58 },
    { name: "Tue", readiness: 62 },
    { name: "Wed", readiness: 66 },
    { name: "Thu", readiness: 71 },
    { name: "Fri", readiness: 69 },
    { name: "Sat", readiness: 76 },
    { name: "Sun", readiness: 82 },
  ];

  const portfolioValueHistory = [
    { name: "Jan", value: currentPortfolioValue * 0.72 },
    { name: "Feb", value: currentPortfolioValue * 0.78 },
    { name: "Mar", value: currentPortfolioValue * 0.84 },
    { name: "Apr", value: currentPortfolioValue * 0.88 },
    { name: "May", value: currentPortfolioValue * 0.94 },
    { name: "Jun", value: currentPortfolioValue * 1.02 },
    { name: "Jul", value: currentPortfolioValue },
  ].map((item) => ({ ...item, value: Math.round(item.value) }));

  const cashVsInvestedData = [
    { name: "Cash", value: currentCash },
    { name: "Invested", value: currentInvested },
  ];

  const allocationData = (
    holdings.length
      ? holdings.map((holding, index) => ({
          name: holding.symbol,
          value: Number(holding.market_value ?? holding.current_price ?? 0),
          color: pieColors[index % pieColors.length],
        }))
      : [
          { name: "Core", value: currentInvested * 0.4, color: pieColors[0] },
          {
            name: "Growth",
            value: currentInvested * 0.35,
            color: pieColors[1],
          },
          {
            name: "Defensive",
            value: currentInvested * 0.25,
            color: pieColors[2],
          },
        ]
  ).filter((item) => Number(item.value || 0) > 0);

  return (
    <Grid container spacing={2}>
      <Grid size={{ xs: 12, md: 6 }}>
        <Card sx={{ borderRadius: 3, height: "100%" }}>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6">Portfolio Value History</Typography>
              <Box sx={{ width: "100%", height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={portfolioValueHistory}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="rgba(255,255,255,0.08)"
                    />
                    <XAxis dataKey="name" stroke="#bdbdbd" />
                    <YAxis
                      stroke="#bdbdbd"
                      tickFormatter={(value) => `₹${value / 1000}k`}
                    />
                    <Tooltip
                      formatter={(value) => [
                        `₹${Number(value).toLocaleString()}`,
                        "Portfolio Value",
                      ]}
                      contentStyle={{
                        backgroundColor: "#1e1e1e",
                        border: "1px solid rgba(255,255,255,0.08)",
                        borderRadius: 12,
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#4caf50"
                      strokeWidth={3}
                      dot={{ r: 4, fill: "#4caf50" }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      </Grid>

      <Grid size={{ xs: 12, md: 6 }}>
        <Card sx={{ borderRadius: 3, height: "100%" }}>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6">Cash vs Invested</Typography>
              <Box sx={{ width: "100%", height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={cashVsInvestedData}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={52}
                      outerRadius={82}
                      paddingAngle={4}
                    >
                      {cashVsInvestedData.map((entry, index) => (
                        <Cell
                          key={entry.name}
                          fill={index === 0 ? "#29b6f6" : "#4caf50"}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value) => [
                        `₹${Number(value).toLocaleString()}`,
                        "Value",
                      ]}
                      contentStyle={{
                        backgroundColor: "#1e1e1e",
                        border: "1px solid rgba(255,255,255,0.08)",
                        borderRadius: 12,
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      </Grid>

      <Grid size={{ xs: 12, md: 6 }}>
        <Card sx={{ borderRadius: 3, height: "100%" }}>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6">Portfolio Allocation</Typography>
              <Box sx={{ width: "100%", height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={allocationData}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={35}
                      outerRadius={85}
                      paddingAngle={2}
                    >
                      {allocationData.map((entry) => (
                        <Cell
                          key={entry.name}
                          fill={entry.color || "#4caf50"}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value) => [
                        `₹${Number(value).toLocaleString()}`,
                        "Value",
                      ]}
                      contentStyle={{
                        backgroundColor: "#1e1e1e",
                        border: "1px solid rgba(255,255,255,0.08)",
                        borderRadius: 12,
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      </Grid>

      <Grid size={{ xs: 12, md: 6 }}>
        <Card sx={{ borderRadius: 3, height: "100%" }}>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6">Readiness Distribution</Typography>
              <Box sx={{ width: "100%", height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={
                      readinessDistributionData.length
                        ? readinessDistributionData
                        : [
                            { name: "0-25", value: 0 },
                            { name: "26-50", value: 0 },
                            { name: "51-75", value: 0 },
                            { name: "76-100", value: 0 },
                          ]
                    }
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="rgba(255,255,255,0.08)"
                    />
                    <XAxis dataKey="name" stroke="#bdbdbd" />
                    <YAxis stroke="#bdbdbd" allowDecimals={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1e1e1e",
                        border: "1px solid rgba(255,255,255,0.08)",
                        borderRadius: 12,
                      }}
                    />
                    <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                      {(readinessDistributionData.length
                        ? readinessDistributionData
                        : [
                            { name: "0-25", value: 0 },
                            { name: "26-50", value: 0 },
                            { name: "51-75", value: 0 },
                            { name: "76-100", value: 0 },
                          ]
                      ).map((entry, index) => (
                        <Cell
                          key={entry.name}
                          fill={
                            ["#ef5350", "#ffb300", "#29b6f6", "#4caf50"][index]
                          }
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      </Grid>

      <Grid size={{ xs: 12 }}>
        <Card sx={{ borderRadius: 3 }}>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6">Readiness Trend</Typography>
              <Box sx={{ width: "100%", height: 220 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient
                        id="readinessFill"
                        x1="0"
                        x2="0"
                        y1="0"
                        y2="1"
                      >
                        <stop
                          offset="5%"
                          stopColor="#4caf50"
                          stopOpacity={0.7}
                        />
                        <stop
                          offset="95%"
                          stopColor="#4caf50"
                          stopOpacity={0.08}
                        />
                      </linearGradient>
                    </defs>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="rgba(255,255,255,0.08)"
                    />
                    <XAxis dataKey="name" stroke="#bdbdbd" />
                    <YAxis stroke="#bdbdbd" domain={[40, 100]} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1e1e1e",
                        border: "1px solid rgba(255,255,255,0.08)",
                        borderRadius: 12,
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="readiness"
                      stroke="#4caf50"
                      fill="url(#readinessFill)"
                      strokeWidth={3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}

export default DashboardCharts;
