import { ButtonItem, PanelSection, PanelSectionRow } from "@decky/ui";
import type { DiagnosticsData } from "../types";

export function Diagnostics({ data, onRefresh }: { data: DiagnosticsData; onRefresh: () => Promise<void> }) {
  const rows: Array<[string, string]> = [
    ["EmuDeck", data.emudeck.detected ? "Detected" : "Not detected"],
    ["ES-DE", data.emudeck.esde_detected ? "Detected" : "Not detected"],
    ["Emulator", data.session?.emulator_name ?? "None"],
    ["PID", data.session?.pid.toString() ?? "—"],
    ["Game", data.session?.game ?? "—"],
    ["ROM", data.session?.rom ?? "—"],
    ["Input backend", data.input_backend],
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
    </PanelSection>
  );
}
