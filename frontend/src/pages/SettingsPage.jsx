import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Select,
  Slider,
  Stack,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import { apiClient } from "../api/client";

const defaultSettings = {
  capital: 100000,
  watchlist_size: 10,
  scheduler_time: "09:30",
  market_filter: "Bullish",
  risk_percent: 2,
  max_positions: 8,
  atr_multiplier: 2,
  rsi_buy_threshold: 55,
  auto_update_stop: true,
  use_live_market_data: true,
  theme_mode: "dark",
  notification_email: true,
  alert_sound: true,
  app_version: "1.0.0",
};

const fieldConfig = {
  capital: { label: "Initial Capital", type: "number", section: "trading" },
  watchlist_size: {
    label: "Watchlist Size",
    type: "number",
    section: "trading",
  },
  scheduler_time: { label: "Scheduler Time", type: "time", section: "trading" },
  risk_percent: { label: "Risk Percent", type: "slider", section: "risk" },
  max_positions: { label: "Max Positions", type: "number", section: "risk" },
  atr_multiplier: { label: "ATR Multiplier", type: "slider", section: "risk" },
  rsi_buy_threshold: {
    label: "RSI Buy Threshold",
    type: "slider",
    section: "risk",
  },
  market_filter: { label: "Market Filter", type: "select", section: "market" },
  use_live_market_data: {
    label: "Live Market Data",
    type: "switch",
    section: "market",
  },
  theme_mode: { label: "Appearance", type: "select", section: "appearance" },
  auto_update_stop: {
    label: "Auto Update Stop Loss",
    type: "switch",
    section: "appearance",
  },
  notification_email: {
    label: "Email Notifications",
    type: "switch",
    section: "appearance",
  },
  alert_sound: { label: "Alert Sound", type: "switch", section: "appearance" },
};

function SettingsPage() {
  const [settings, setSettings] = useState(defaultSettings);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const response = await apiClient.get("/settings");
        const payload = response?.data?.data || response?.data || {};
        setSettings({ ...defaultSettings, ...payload });
      } catch (error) {
        setMessage("Unable to load settings from the backend.");
      } finally {
        setLoading(false);
      }
    };

    loadSettings();
  }, []);

  const sections = useMemo(
    () => ({
      trading: [
        { name: "capital", ...fieldConfig.capital },
        { name: "watchlist_size", ...fieldConfig.watchlist_size },
        { name: "scheduler_time", ...fieldConfig.scheduler_time },
      ],
      risk: [
        { name: "risk_percent", ...fieldConfig.risk_percent },
        { name: "max_positions", ...fieldConfig.max_positions },
        { name: "atr_multiplier", ...fieldConfig.atr_multiplier },
        { name: "rsi_buy_threshold", ...fieldConfig.rsi_buy_threshold },
      ],
      market: [
        { name: "market_filter", ...fieldConfig.market_filter },
        { name: "use_live_market_data", ...fieldConfig.use_live_market_data },
      ],
      appearance: [
        { name: "theme_mode", ...fieldConfig.theme_mode },
        { name: "auto_update_stop", ...fieldConfig.auto_update_stop },
        { name: "notification_email", ...fieldConfig.notification_email },
        { name: "alert_sound", ...fieldConfig.alert_sound },
      ],
    }),
    [],
  );

  const handleFieldChange = (event) => {
    const { name, value, type, checked } = event.target;
    setSettings((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSliderChange = (name) => (_event, value) => {
    setSettings((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await apiClient.post("/settings", settings);
      const payload = response?.data?.data || settings;
      setSettings({ ...defaultSettings, ...payload });
      setMessage("Settings saved successfully.");
    } catch (error) {
      setMessage("Failed to save settings. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    setSettings(defaultSettings);
    try {
      const response = await apiClient.post("/settings", defaultSettings);
      const payload = response?.data?.data || defaultSettings;
      setSettings({ ...defaultSettings, ...payload });
      setMessage("Settings reset to default values.");
    } catch (error) {
      setMessage(
        "Defaults were restored locally, but the backend update failed.",
      );
    }
  };

  const renderSection = (title, fields) => (
    <Card
      key={title}
      sx={{
        bgcolor: "background.paper",
        border: "1px solid rgba(255,255,255,0.08)",
      }}
    >
      <CardContent>
        <Stack spacing={3}>
          <Typography variant="h6">{title}</Typography>
          {fields.map((field) => {
            const value = settings[field.name];

            if (field.type === "switch") {
              return (
                <FormControlLabel
                  key={field.name}
                  control={
                    <Switch
                      checked={Boolean(value)}
                      name={field.name}
                      onChange={handleFieldChange}
                    />
                  }
                  label={field.label}
                />
              );
            }

            if (field.type === "select") {
              return (
                <FormControl key={field.name} fullWidth>
                  <InputLabel>{field.label}</InputLabel>
                  <Select
                    name={field.name}
                    value={value ?? ""}
                    label={field.label}
                    onChange={handleFieldChange}
                  >
                    {field.name === "market_filter"
                      ? ["Bullish", "Bearish", "Neutral"].map((option) => (
                          <MenuItem key={option} value={option}>
                            {option}
                          </MenuItem>
                        ))
                      : ["dark", "light"].map((option) => (
                          <MenuItem key={option} value={option}>
                            {option}
                          </MenuItem>
                        ))}
                  </Select>
                </FormControl>
              );
            }

            if (field.type === "slider") {
              return (
                <Box key={field.name} sx={{ px: 1 }}>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    {field.label}
                  </Typography>
                  <Slider
                    value={Number(value ?? 0)}
                    min={field.name === "rsi_buy_threshold" ? 30 : 1}
                    max={
                      field.name === "risk_percent"
                        ? 10
                        : field.name === "atr_multiplier"
                          ? 5
                          : 100
                    }
                    step={field.name === "risk_percent" ? 0.5 : 1}
                    valueLabelDisplay="auto"
                    onChange={handleSliderChange(field.name)}
                  />
                </Box>
              );
            }

            return (
              <TextField
                key={field.name}
                label={field.label}
                name={field.name}
                type={field.type === "number" ? "number" : "time"}
                value={value ?? ""}
                onChange={handleFieldChange}
                fullWidth
              />
            );
          })}
        </Stack>
      </CardContent>
    </Card>
  );

  return (
    <Stack spacing={3}>
      <Stack
        direction="row"
        spacing={2}
        sx={{ justifyContent: "space-between", alignItems: "center" }}
      >
        <Typography variant="h4">Settings</Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="contained"
            onClick={handleSave}
            disabled={loading || saving}
          >
            Save
          </Button>
          <Button variant="outlined" onClick={handleReset}>
            Reset
          </Button>
        </Stack>
      </Stack>

      {message && (
        <Alert
          severity={
            message.includes("success") || message.includes("default")
              ? "success"
              : "error"
          }
        >
          {message}
        </Alert>
      )}

      <Stack spacing={3}>
        {renderSection("Trading Settings", sections.trading)}
        <Divider />
        {renderSection("Risk Settings", sections.risk)}
        <Divider />
        {renderSection("Market Data", sections.market)}
        <Divider />
        {renderSection("Appearance", sections.appearance)}
        <Divider />
        <Card
          sx={{
            bgcolor: "background.paper",
            border: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              About
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Trading Agent settings are stored in the backend config file and
              synced with the app on save.
            </Typography>
            <Typography variant="caption" display="block" sx={{ mt: 2 }}>
              Version: {settings.app_version || "1.0.0"}
            </Typography>
          </CardContent>
        </Card>
      </Stack>
    </Stack>
  );
}

export default SettingsPage;
