import React, { useEffect, useState } from "react";
import "./SettingsPage.css";
import { fetchSettings, updateSettings } from "../api";

export default function SettingsPage() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const data = await fetchSettings();
        setSettings(data);
      } catch (err) {
        setError("Unable to load settings.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleSave = async () => {
    if (!settings) return;
    setError("");
    setSuccess("");
    try {
      const payload = {
        challenge_visibility: settings.challenge_visibility,
        allow_incoming_challenges: settings.allow_incoming_challenges,
        allowed_sender_user_ids: settings.allowed_sender_user_ids || [],
        theme: settings.theme,
      };
      const data = await updateSettings(payload);
      setSettings(data);
      setSuccess("Settings saved.");
    } catch (err) {
      setError("Failed to save settings.");
    }
  };

  const updateField = (field, value) => {
    setSettings((prev) => ({ ...prev, [field]: value }));
  };

  if (loading) return <div className="page">Loading...</div>;
  if (!settings) return <div className="page error">{error || "No settings found."}</div>;

  return (
    <div className="page">
      <h2>Settings</h2>
      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}
      <div className="settings-grid">
        <div className="settings-card">
          <h4>Theme</h4>
          <select
            value={settings.theme}
            onChange={(e) => updateField("theme", e.target.value)}
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="high-contrast">High Contrast</option>
          </select>
        </div>
        <div className="settings-card">
          <h4>Challenge Privacy</h4>
          <label>
            Visibility
            <select
              value={settings.challenge_visibility}
              onChange={(e) => updateField("challenge_visibility", e.target.value)}
            >
              <option value="everyone">Everyone</option>
              <option value="no-one">No one</option>
            </select>
          </label>
          <label className="row">
            <input
              type="checkbox"
              checked={settings.allow_incoming_challenges}
              onChange={(e) => updateField("allow_incoming_challenges", e.target.checked)}
            />
            Allow incoming challenges
          </label>
          <label>
            Allowed Sender User IDs (comma separated)
            <input
              type="text"
              value={(settings.allowed_sender_user_ids || []).join(",")}
              onChange={(e) =>
                updateField(
                  "allowed_sender_user_ids",
                  e.target.value
                    .split(",")
                    .map((v) => v.trim())
                    .filter(Boolean)
                )
              }
            />
          </label>
        </div>
      </div>
      <button onClick={handleSave}>Save Settings</button>
    </div>
  );
}
