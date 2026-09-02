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
  const config = data.session?.hotkey_config;
  if (config?.status) {
    rows.push(["Hotkey configuration", `${config.status} — ${config.path ?? ""}`]);
    rows.push(["Hotkey scope", config.scope ?? "Global settings"]);
    if (config.paths && config.paths.length > 1) {
      rows.push(["Hotkey files", config.paths.join(" → ")]);
    }
    if (config.overrides) {
      rows.push(["RetroArch overrides", `${config.overrides.status} — ${config.overrides.reason ?? ""}`]);
      if (config.overrides.core) rows.push(["Override core", config.overrides.core]);
      if (config.overrides.directory) rows.push(["Override directory", config.overrides.directory]);
      for (const layer of config.overrides.layers ?? []) {
        rows.push([`Override: ${layer.level}`, layer.path]);
      }
    }
    for (const [action, reason] of Object.entries(config.disabled_actions ?? {})) {
      rows.push([data.session?.actions[action]?.label ?? action, reason]);
    }
  }
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
