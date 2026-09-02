import { ButtonItem, PanelSection, PanelSectionRow } from "@decky/ui";
import { toaster } from "@decky/api";
import { exportDiagnostics } from "../api/backend";
import type { DiagnosticsData } from "../types";

export function Diagnostics({ data, onRefresh }: { data: DiagnosticsData; onRefresh: () => Promise<void> }) {
  const copyDiagnostics = async () => {
    try {
      if (!navigator.clipboard?.writeText) throw new Error("Clipboard API unavailable");
      await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
      toaster.toast({ title: "EmuDeck Companion", body: "Diagnostics copied" });
    } catch (error) {
      toaster.toast({ title: "Cannot copy diagnostics", body: String(error) });
    }
  };

  const saveDiagnostics = async () => {
    try {
      const result = await exportDiagnostics();
      toaster.toast({ title: "Diagnostics exported", body: result.path });
    } catch (error) {
      toaster.toast({ title: "Cannot export diagnostics", body: String(error) });
    }
  };

  const rows: Array<[string, string]> = [
    ["EmuDeck", data.emudeck.detected ? "Detected" : "Not detected"],
    ["ES-DE", data.emudeck.esde_detected ? "Detected" : "Not detected"],
    ["Emulator", data.session?.emulator_name ?? "None"],
    ["PID", data.session?.pid.toString() ?? "—"],
    ["Game", data.session?.game ?? "—"],
    ["ROM", data.session?.rom ?? "—"],
    ["Input backend", data.input_backend],
    [
      "Document server",
      data.document_server.running
        ? `Running on localhost:${data.document_server.port}`
        : "Stopped",
    ],
    ["Last action", data.last_action?.message ?? "None"],
  ];
  return (
    <PanelSection title="Diagnostics">
      {rows.map(([label, value]) => (
        <PanelSectionRow key={label}>
          <div style={{ width: "100%" }}>
            <div style={{ opacity: 0.55, fontSize: "12px" }}>{label}</div>
            <div style={{ overflowWrap: "anywhere" }}>{value}</div>
          </div>
        </PanelSectionRow>
      ))}
      <PanelSectionRow>
        <ButtonItem layout="below" onClick={() => void onRefresh()}>
          Refresh Detection
        </ButtonItem>
      </PanelSectionRow>
      <PanelSectionRow>
        <ButtonItem layout="below" onClick={() => void copyDiagnostics()}>
          Copy Diagnostics
        </ButtonItem>
      </PanelSectionRow>
      <PanelSectionRow>
        <ButtonItem layout="below" onClick={() => void saveDiagnostics()}>
          Export Diagnostics
        </ButtonItem>
      </PanelSectionRow>
    </PanelSection>
  );
}
