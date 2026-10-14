import { CssBaseline, ThemeProvider } from "@mui/material";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import DashboardLayout from "./layouts/DashboardLayout";
import DashboardPage from "./pages/DashboardPage";
import JournalPage from "./pages/JournalPage";
import NotFoundPage from "./pages/NotFoundPage";
import PortfolioPage from "./pages/PortfolioPage";
import SettingsPage from "./pages/SettingsPage";
import WatchlistPage from "./pages/WatchlistPage";
import darkTheme from "./theme/darkTheme";

function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <BrowserRouter>
        <Routes>
          <Route element={<DashboardLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/portfolio" element={<PortfolioPage />} />
            <Route path="/watchlist" element={<WatchlistPage />} />
            <Route path="/journal" element={<JournalPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/404" element={<NotFoundPage />} />
            <Route path="*" element={<Navigate to="/404" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
