import type { CompanionSettings, EmulatorSession } from "../types";

function elapsed(startedAt: number): string {
  const seconds = Math.max(0, Math.floor(Date.now() / 1000 - startedAt));
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const rest = seconds % 60;
  return [hours, minutes, rest].map((value) => value.toString().padStart(2, "0")).join(":");
}
export function GameHeader({
  session,
  artwork,
  settings,
}: {
  session: EmulatorSession;
  artwork: string | null;
  settings: CompanionSettings | null;
}) {
  const details = [
    settings?.show_platform !== false ? session.platform : null,
    settings?.show_emulator !== false ? session.emulator_name : null,
  ].filter(Boolean);
  return (
    <div style={{ padding: "4px 0 12px" }}>
      {artwork && (
        <img
          src={artwork}
          alt=""
          style={{ width: "100%", maxHeight: "180px", objectFit: "cover", borderRadius: "6px", marginBottom: "10px" }}
        />
      )}
      <div style={{ fontSize: "20px", fontWeight: 700, lineHeight: 1.2 }}>
        {session.game ?? "Unknown game"}
      </div>
      {details.length > 0 && (
        <div style={{ opacity: 0.72, marginTop: "5px" }}>{details.join(" • ")}</div>
      )}
      {settings?.show_session_time !== false && (
        <div style={{ opacity: 0.55, fontVariantNumeric: "tabular-nums", marginTop: "3px" }}>
          {elapsed(session.started_at)}
        </div>
      )}
      {session.metadata.desc && (
        <div style={{ opacity: 0.72, fontSize: "12px", lineHeight: 1.35, marginTop: "8px" }}>
          {session.metadata.desc.length > 220 ? `${session.metadata.desc.slice(0, 217)}…` : session.metadata.desc}
        </div>
      )}
      {(session.metadata.manual || session.discs.length > 1) && (
        <div style={{ opacity: 0.6, fontSize: "12px", marginTop: "7px" }}>
          {[session.metadata.manual ? "Manual available" : null, session.discs.length > 1 ? `${session.discs.length} discs` : null]
            .filter(Boolean).join(" • ")}
        </div>
      )}
    </div>
  );
}
