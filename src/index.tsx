import { ButtonItem, Navigation, PanelSection, PanelSectionRow, staticClasses } from "@decky/ui";
import { definePlugin, toaster } from "@decky/api";
import { useCallback, useEffect, useState } from "react";
import { FaGamepad } from "react-icons/fa";
import {
  executeAction,
  getArtwork,
  getCurrentSession,
  getDiagnostics,
  getSettings,
  refreshDetection,
  updateSettings,
} from "./api/backend";
import { Diagnostics } from "./components/Diagnostics";
import { Documents } from "./components/Documents";
import { EmulatorActions } from "./components/EmulatorActions";
import { GameHeader } from "./components/GameHeader";
import { Hotkeys } from "./components/Hotkeys";
import { Settings } from "./components/Settings";
import { pressHotkeys } from "./hotkey";
import type { CompanionSettings, DiagnosticsData, EmulatorSession } from "./types";

function Content() {
  const [session, setSession] = useState<EmulatorSession | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [showDiagnostics, setShowDiagnostics] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [diagnostics, setDiagnostics] = useState<DiagnosticsData | null>(null);
  const [artwork, setArtwork] = useState<string | null>(null);
  const [settings, setSettings] = useState<CompanionSettings | null>(null);

  const updateSession = useCallback(async () => {
    try {
      setSession(await getCurrentSession());
    } catch (error) {
      console.error("EmuDeck Companion session refresh failed", error);
    } finally {
      setLoaded(true);
    }
  }, []);

  const updateDiagnostics = useCallback(async () => {
    try {
      setDiagnostics(await getDiagnostics());
    } catch (error) {
      toaster.toast({ title: "EmuDeck Companion", body: String(error) });
    }
  }, []);

  useEffect(() => {
    void getSettings()
      .then(setSettings)
      .catch((error) => toaster.toast({ title: "Settings unavailable", body: String(error) }));
  }, []);

  useEffect(() => {
    let disposed = false;
    const poll = async () => {
      if (!disposed) await updateSession();
    };
    void poll();
    const timer = window.setInterval(() => void poll(), settings?.detection_interval_ms ?? 1500);
    return () => {
      disposed = true;
      window.clearInterval(timer);
    };
  }, [settings?.detection_interval_ms, updateSession]);

  useEffect(() => {
    let disposed = false;
    setArtwork(null);
    if (session?.metadata.image) {
      void getArtwork().then((value) => {
        if (!disposed) setArtwork(value);
      }).catch((error) => console.error("Artwork loading failed", error));
    }
    return () => { disposed = true; };
  }, [session?.rom, session?.metadata.image]);

  useEffect(() => {
    if (showDiagnostics) void updateDiagnostics();
  }, [showDiagnostics, updateDiagnostics]);

  const onAction = useCallback(async (action: string) => {
    if (busyAction !== null) return;
    setBusyAction(action);
    try {
      const result = await executeAction(action);
      if (result.ok && result.dispatch === "steam_input" && result.keys) {
        Navigation.CloseSideMenus();
        window.setTimeout(() => {
          try {
            pressHotkeys(result.keys ?? []);
            if (settings?.notifications !== false) {
              toaster.toast({ title: "EmuDeck Companion", body: result.message });
            }
          } catch (error) {
            toaster.toast({ title: "Action failed", body: String(error) });
          }
        }, 200);
      } else {
        if (!result.ok || settings?.notifications !== false) {
          toaster.toast({
            title: result.ok ? "EmuDeck Companion" : "Action failed",
            body: result.message,
          });
        }
        await updateSession();
      }
    } catch (error) {
      toaster.toast({ title: "Action failed", body: String(error) });
    } finally {
      setBusyAction(null);
    }
  }, [busyAction, settings?.notifications, updateSession]);

  const saveSettings = useCallback(async (changes: Partial<CompanionSettings>) => {
    try {
      setSettings(await updateSettings(changes));
    } catch (error) {
      toaster.toast({ title: "Settings update failed", body: String(error) });
    }
  }, []);

  const manualRefresh = useCallback(async () => {
    setSession(await refreshDetection());
    if (showDiagnostics) await updateDiagnostics();
  }, [showDiagnostics, updateDiagnostics]);

  const activeFavorites = session && settings
    ? settings.game_overrides[session.game_key ?? ""]?.favorites
      ?? settings.favorites[session.emulator]
      ?? []
    : [];

  if (!loaded) {
    return <PanelSection><PanelSectionRow>Detecting active emulator…</PanelSectionRow></PanelSection>;
  }

  return (
    <>
      {session ? (
        <>
          <PanelSection>
            <PanelSectionRow>
              <GameHeader session={session} artwork={artwork} settings={settings} />
            </PanelSectionRow>
          </PanelSection>
          <EmulatorActions
            session={session}
            favorites={activeFavorites}
            busyAction={busyAction}
            onAction={onAction}
          />
          <Documents documents={session.documents} />
          <Hotkeys session={session} />
        </>
      ) : (
        <PanelSection title="EmuDeck Companion">
          <PanelSectionRow>
            <div style={{ width: "100%", padding: "8px 0", opacity: 0.72 }}>
              No active emulation session
            </div>
          </PanelSectionRow>
          <PanelSectionRow>
            <ButtonItem layout="below" onClick={() => void manualRefresh()}>
              Refresh Detection
            </ButtonItem>
          </PanelSectionRow>
        </PanelSection>
      )}
      <PanelSection>
        <PanelSectionRow>
          <ButtonItem layout="below" onClick={() => setShowSettings((value) => !value)}>
            {showSettings ? "Hide Settings" : "Show Settings"}
          </ButtonItem>
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem layout="below" onClick={() => setShowDiagnostics((value) => !value)}>
            {showDiagnostics ? "Hide Diagnostics" : "Show Diagnostics"}
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>
      {showSettings && settings && (
        <Settings settings={settings} session={session} onChange={saveSettings} />
      )}
      {showDiagnostics && diagnostics && <Diagnostics data={diagnostics} onRefresh={manualRefresh} />}
    </>
  );
}

export default definePlugin(() => ({
  name: "EmuDeck Companion",
  titleView: <div className={staticClasses.Title}>EmuDeck Companion</div>,
  content: <Content />,
  icon: <FaGamepad />,
  onDismount() {
    console.log("EmuDeck Companion unloaded");
  },
}));
