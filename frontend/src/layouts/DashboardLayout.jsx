import {
  AppBar,
  Box,
  CssBaseline,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Toolbar,
  Typography,
} from "@mui/material";
import {
  Article as JournalIcon,
  BarChart as BarChartIcon,
  Dashboard as DashboardIcon,
  ListAlt as WatchlistIcon,
  Menu as MenuIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Wallet as PortfolioIcon,
} from "@mui/icons-material";
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

const drawerWidth = 240;

const navItems = [
  { label: "Dashboard", to: "/", icon: DashboardIcon },
  { label: "Portfolio", to: "/portfolio", icon: PortfolioIcon },
  { label: "Watchlist", to: "/watchlist", icon: WatchlistIcon },
  { label: "Journal", to: "/journal", icon: JournalIcon },
  { label: "Settings", to: "/settings", icon: SettingsIcon },
];

function DashboardLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState(
    new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
  );
  const marketRegime = "Bearish";

  const handleRefresh = () => {
    setCurrentTime(
      new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    );
  };

  const drawer = (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" sx={{ mb: 2, fontWeight: 700 }}>
        Good Vibes
      </Typography>
      <Divider sx={{ mb: 2 }} />
      <List sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
        {navItems.map((item) => {
          const Icon = item.icon;

          return (
            <ListItem key={item.to} disablePadding>
              <ListItemButton
                component={NavLink}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) => (isActive ? "active" : "")}
                sx={{
                  px: 1.5,
                  py: 1,
                  color: "text.secondary",
                  "&.active": {
                    backgroundColor: "rgba(76,175,80,0.12)",
                    color: "primary.main",
                    ".MuiListItemIcon-root": {
                      color: "primary.main",
                    },
                  },
                  ":hover": {
                    backgroundColor: "rgba(255,255,255,0.04)",
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 32, color: "inherit" }}>
                  <Icon fontSize="small" />
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  sx={{ "& .MuiListItemText-primary": { fontWeight: 600 } }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
    </Box>
  );

  return (
    <Box
      sx={{
        display: "flex",
        minHeight: "100vh",
        bgcolor: "background.default",
      }}
    >
      <CssBaseline />
      <Box
        component="nav"
        sx={{ width: { xs: 0, md: drawerWidth }, flexShrink: 0 }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: "block", md: "none" },
            "& .MuiDrawer-paper": {
              boxSizing: "border-box",
              width: drawerWidth,
            },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: "none", md: "block" },
            "& .MuiDrawer-paper": {
              boxSizing: "border-box",
              width: drawerWidth,
              borderRight: "1px solid rgba(255,255,255,0.08)",
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      <Box sx={{ flexGrow: 1, display: "flex", flexDirection: "column" }}>
        <AppBar
          position="sticky"
          color="transparent"
          elevation={0}
          sx={{
            borderBottom: "1px solid rgba(255,255,255,0.08)",
            backdropFilter: "blur(12px)",
          }}
        >
          <Toolbar sx={{ justifyContent: "space-between", minHeight: 72 }}>
            <Stack direction="row" spacing={2} sx={{ alignItems: "center" }}>
              <IconButton
                edge="start"
                color="inherit"
                sx={{ display: { md: "none" } }}
                onClick={() => setMobileOpen(true)}
              >
                <MenuIcon />
              </IconButton>
              <Typography variant="subtitle1" color="text.secondary">
                Current Time
              </Typography>
              <Typography variant="body1" fontWeight={600}>
                {currentTime}
              </Typography>
            </Stack>

            <Stack direction="row" spacing={2} sx={{ alignItems: "center" }}>
              <Typography variant="subtitle2" color="text.secondary">
                Market Regime
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  color:
                    marketRegime === "Bullish"
                      ? "primary.main"
                      : "warning.main",
                  fontWeight: 700,
                }}
              >
                {marketRegime}
              </Typography>
              <IconButton
                color="inherit"
                onClick={handleRefresh}
                aria-label="refresh"
              >
                <RefreshIcon />
              </IconButton>
            </Stack>
          </Toolbar>
        </AppBar>

        <Box component="main" sx={{ flexGrow: 1, p: { xs: 2, md: 3 } }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}

export default DashboardLayout;
