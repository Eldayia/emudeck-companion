import { ButtonItem, PanelSection, PanelSectionRow, staticClasses } from "@decky/ui";
import { definePlugin, toaster } from "@decky/api";
import { useCallback, useEffect, useState } from "react";
import { FaGamepad } from "react-icons/fa";
import { executeAction, getCurrentSession, getDiagnostics, refreshDetection } from "./api/backend";
import { Diagnostics } from "./components/Diagnostics";
import { EmulatorActions } from "./components/EmulatorActions";
import { GameHeader } from "./components/GameHeader";
import type { DiagnosticsData, EmulatorSession } from "./types";

function Content() {
  const [session, setSession] = useState<EmulatorSession | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [showDiagnostics, setShowDiagnostics] = useState(false);
  const [diagnostics, setDiagnostics] = useState<DiagnosticsData | null>(null);

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
    let disposed = false;
    const poll = async () => {
      if (!disposed) await updateSession();
    };
    void poll();
    const timer = window.setInterval(() => void poll(), 1500);
    return () => {
      disposed = true;
      window.clearInterval(timer);
    };
  }, [updateSession]);

  useEffect(() => {
    if (showDiagnostics) void updateDiagnostics();
  }, [showDiagnostics, updateDiagnostics]);

  const onAction = useCallback(async (action: string) => {
    if (busyAction !== null) return;
    setBusyAction(action);
    try {
      const result = await executeAction(action);
      toaster.toast({
        title: result.ok ? "EmuDeck Companion" : "Action failed",
        body: result.message,
      });
      await updateSession();
    } catch (error) {
      toaster.toast({ title: "Action failed", body: String(error) });
    } finally {
      setBusyAction(null);
    }
  }, [busyAction, updateSession]);

  const manualRefresh = useCallback(async () => {
    setSession(await refreshDetection());
    if (showDiagnostics) await updateDiagnostics();
  }, [showDiagnostics, updateDiagnostics]);

  if (!loaded) {
    return <PanelSection><PanelSectionRow>Detecting active emulator…</PanelSectionRow></PanelSection>;
  }

  return (
    <>
      {session ? (
        <>
          <PanelSection>
            <PanelSectionRow><GameHeader session={session} /></PanelSectionRow>
          </PanelSection>
          <EmulatorActions session={session} busyAction={busyAction} onAction={onAction} />
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
          <ButtonItem layout="below" onClick={() => setShowDiagnostics((value) => !value)}>
            {showDiagnostics ? "Hide Diagnostics" : "Show Diagnostics"}
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>
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
