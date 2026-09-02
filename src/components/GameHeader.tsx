import type { EmulatorSession } from "../types";

function elapsed(startedAt: number): string {
  const seconds = Math.max(0, Math.floor(Date.now() / 1000 - startedAt));
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const rest = seconds % 60;
  return [hours, minutes, rest].map((value) => value.toString().padStart(2, "0")).join(":");
}
export function GameHeader({ session }: { session: EmulatorSession }) {
  return (
    <div style={{ padding: "4px 0 12px" }}>
      <div style={{ fontSize: "20px", fontWeight: 700, lineHeight: 1.2 }}>
        {session.game ?? "Unknown game"}
      </div>
      <div style={{ opacity: 0.72, marginTop: "5px" }}>
        {[session.platform, session.emulator_name].filter(Boolean).join(" • ")}
      </div>
      <div style={{ opacity: 0.55, fontVariantNumeric: "tabular-nums", marginTop: "3px" }}>
        {elapsed(session.started_at)}
      </div>
    </div>
  );
}
