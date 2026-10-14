import { createTheme } from "@mui/material/styles";

export const darkTheme = createTheme({
  palette: {
    mode: "dark",
    primary: {
      main: "#4caf50",
      light: "#81c784",
      dark: "#2e7d32",
    },
    secondary: {
      main: "#ff9800",
      light: "#ffb74d",
      dark: "#ef6c00",
    },
    success: {
      main: "#4caf50",
    },
    info: {
      main: "#29b6f6",
    },
    warning: {
      main: "#ffb300",
    },
    error: {
      main: "#f44336",
    },
    background: {
      default: "#121212",
      paper: "#1e1e1e",
    },
    text: {
      primary: "#ffffff",
      secondary: "#d0d0d0",
    },
  },
  shape: {
    borderRadius: 14,
  },
  shadows: [
    "none",
    "0 1px 2px rgba(0,0,0,0.18)",
    "0 4px 12px rgba(0,0,0,0.22)",
    "0 8px 18px rgba(0,0,0,0.24)",
    "0 12px 22px rgba(0,0,0,0.28)",
    "0 16px 26px rgba(0,0,0,0.30)",
    "0 20px 30px rgba(0,0,0,0.32)",
    "0 24px 32px rgba(0,0,0,0.34)",
    "0 28px 34px rgba(0,0,0,0.36)",
    "0 32px 36px rgba(0,0,0,0.38)",
    "0 36px 40px rgba(0,0,0,0.40)",
    "0 40px 44px rgba(0,0,0,0.42)",
    "0 44px 48px rgba(0,0,0,0.44)",
    "0 48px 52px rgba(0,0,0,0.46)",
    "0 52px 56px rgba(0,0,0,0.48)",
    "0 56px 60px rgba(0,0,0,0.50)",
    "0 60px 64px rgba(0,0,0,0.52)",
    "0 64px 68px rgba(0,0,0,0.54)",
    "0 68px 72px rgba(0,0,0,0.56)",
    "0 72px 76px rgba(0,0,0,0.58)",
    "0 76px 80px rgba(0,0,0,0.60)",
    "0 80px 84px rgba(0,0,0,0.62)",
    "0 84px 88px rgba(0,0,0,0.64)",
    "0 88px 92px rgba(0,0,0,0.66)",
  ],
  typography: {
    fontFamily: "Inter, Roboto, sans-serif",
    h1: { fontWeight: 700 },
    h2: { fontWeight: 700 },
    h3: { fontWeight: 600 },
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
          border: "1px solid rgba(255,255,255,0.06)",
          boxShadow: "0 8px 24px rgba(0,0,0,0.24)",
          transition:
            "transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease",
          overflow: "hidden",
          "&:hover": {
            transform: "translateY(-2px)",
            boxShadow: "0 16px 32px rgba(0,0,0,0.32)",
            borderColor: "rgba(76,175,80,0.28)",
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 999,
          fontWeight: 700,
          letterSpacing: "0.02em",
          transition: "all 0.2s ease",
        },
        sizeSmall: {
          height: 26,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          transition: "all 0.2s ease",
          "&.active": {
            backgroundColor: "rgba(76,175,80,0.12)",
          },
        },
      },
    },
  },
});

export default darkTheme;
