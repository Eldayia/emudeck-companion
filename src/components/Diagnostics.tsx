import { ButtonItem, PanelSection, PanelSectionRow } from "@decky/ui";
import { toaster } from "@decky/api";
import { exportDiagnostics } from "../api/backend";
import type { DiagnosticsData } from "../types";

export function Diagnostics({ data, onRefresh, onUpdate }: {
  data: DiagnosticsData;
  onRefresh: () => Promise<void>;
  onUpdate: () => Promise<void>;
}) {
  const statusLabels = {
    pending: "Waiting for keyboard", sent: "Sent (unconfirmed)", failed: "Failed",
    unknown: "Delivery unknown", completed: "Local selection updated",
  };
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
    ["Plugin version", data.plugin_version ?? "unknown"],
    ["EmuDeck", data.emudeck.detected ? "Detected" : "Not detected"],
    ["ES-DE", data.emudeck.esde_detected ? "Detected" : "Not detected"],
    ["Emulator", data.session?.emulator_name ?? "None"],
    ["PID", data.session?.pid.toString() ?? "—"],
    ["Session ID", data.session?.session_id ?? "—"],
    ["Process start ticks", data.session?.process_started_ticks?.toString() ?? "—"],
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
  const hooks = data.esde_hooks;
  if (hooks) {
    rows.push(["ES-DE hooks", `${hooks.status} (${hooks.installed_hooks}/2 files)`]);
    rows.push(["ES-DE data folder", hooks.root ?? "Not detected"]);
    if (hooks.installed_hooks > 0) rows.push(["ES-DE script activation", hooks.activation]);
    if (hooks.last_event) {
      rows.push(["Last ES-DE event", `${hooks.last_event.event} — ${new Date(hooks.last_event.timestamp * 1000).toLocaleString()}`]);
      rows.push(["ES-DE event game", hooks.last_event.game]);
      rows.push(["ES-DE event ROM", hooks.last_event.rom]);
      rows.push(["ES-DE / process ROM", hooks.same_rom ? "Same path (not session confirmation)" : "Different path or no detected ROM"]);
    }
  }
  if (config?.status) {
    if (config.native_commands) {
      const native = config.native_commands;
      rows.push(["RetroArch native commands", `${native.status} — localhost:${native.port}${native.version ? ` — ${native.version}` : ""}`]);
      rows.push(["Native interface details", native.reason]);
      rows.push(["Network commands on disk", config.network_settings?.enabled_on_disk ? "Enabled (restart required after changes)" : "Disabled or absent; live endpoint checked separately"]);
    }
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
      {(data.action_history?.length ?? 0) > 0 && (
        <PanelSectionRow>
          <div style={{ width: "100%", fontSize: "12px", overflowWrap: "anywhere" }}>
            <div style={{ opacity: 0.55 }}>Recent actions — latest 5 of {data.action_history?.length} (export includes all)</div>
            {data.action_history?.slice(0, 5).map((entry) => (
              <div key={entry.id} style={{ marginTop: "10px" }}>
                <div>{new Date(entry.timestamp * 1000).toLocaleTimeString()} — {entry.action} — {statusLabels[entry.status]}</div>
                <div style={{ opacity: 0.7 }}>{[entry.emulator, entry.game, entry.dispatch].filter(Boolean).join(" • ")}</div>
                <div>{entry.message}</div>
              </div>
            ))}
          </div>
        </PanelSectionRow>
      )}
      <PanelSectionRow>
        <ButtonItem layout="below" onClick={() => void onUpdate()}>
          Refresh Diagnostics
        </ButtonItem>
      </PanelSectionRow>
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
