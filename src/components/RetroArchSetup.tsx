import { useState } from "react";
import { ButtonItem, PanelSection, PanelSectionRow } from "@decky/ui";
import { toaster } from "@decky/api";
import { configureRetroArchNetwork } from "../api/backend";

export function RetroArchSetup() {
  const [confirmation, setConfirmation] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState("");

  const configure = async (enabled: boolean) => {
    setBusy(true);
    try {
      const response = await configureRetroArchNetwork(enabled);
      setResult(`${response.message}${response.backup ? ` Backup: ${response.backup}` : ""}`);
      toaster.toast({ title: response.ok ? "RetroArch configuration" : "Cannot configure RetroArch", body: response.message });
    } catch (error) {
      setResult(String(error));
      toaster.toast({ title: "Cannot configure RetroArch", body: String(error) });
    } finally {
      setBusy(false);
      setConfirmation(null);
    }
  };

  return (
    <PanelSection title="RetroArch Native Commands">
      <PanelSectionRow>
        <div style={{ fontSize: "12px", overflowWrap: "anywhere" }}>
          Close RetroArch completely first. This changes only network_cmd_enable in the standard
          RetroArch Flatpak configuration, with a backup. Controller and keyboard binds stay unchanged.
          Relaunch RetroArch afterwards (version 1.19+).
        </div>
      </PanelSectionRow>
      <PanelSectionRow>
        <div style={{ fontSize: "12px" }}>
          Security: RetroArch's command port has no authentication and may be reachable from your
          local network. Companion sends only to localhost but does not restrict incoming connections
          or change your firewall. Enable only on a trusted network.
        </div>
      </PanelSectionRow>
      {confirmation === null ? (
        <>
          <PanelSectionRow>
            <ButtonItem layout="below" disabled={busy} onClick={() => setConfirmation(true)}>
              Enable Native Commands…
            </ButtonItem>
          </PanelSectionRow>
          <PanelSectionRow>
            <ButtonItem layout="below" disabled={busy} onClick={() => setConfirmation(false)}>
              Disable Native Commands…
            </ButtonItem>
          </PanelSectionRow>
        </>
      ) : (
        <>
          <PanelSectionRow>
            <ButtonItem layout="below" disabled={busy} onClick={() => void configure(confirmation)}>
              {busy ? "Working…" : `Confirm ${confirmation ? "Enable" : "Disable"} Native Commands`}
            </ButtonItem>
          </PanelSectionRow>
          <PanelSectionRow>
            <ButtonItem layout="below" disabled={busy} onClick={() => setConfirmation(null)}>Cancel</ButtonItem>
          </PanelSectionRow>
        </>
      )}
      {result && <PanelSectionRow><div style={{ fontSize: "12px", overflowWrap: "anywhere" }}>{result}</div></PanelSectionRow>}
    </PanelSection>
  );
}
