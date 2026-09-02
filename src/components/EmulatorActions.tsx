import { ButtonItem, PanelSection, PanelSectionRow } from "@decky/ui";
import type { EmulatorSession } from "../types";

const groups: Array<{ title: string; actions: string[] }> = [
  { title: "Save States", actions: ["save_state", "load_state"] },
  { title: "Emulation", actions: ["pause", "fast_forward", "rewind"] },
  { title: "Display", actions: ["swap_screen", "fullscreen"] },
  { title: "Disc", actions: ["previous_disc", "next_disc"] },
  { title: "Other", actions: ["screenshot", "emulator_menu"] },
  { title: "Session", actions: ["quit"] },
];

interface Props {
  session: EmulatorSession;
  busyAction: string | null;
  onAction: (action: string) => Promise<void>;
}

function stateTimestamp(timestamp: number): string {
  const date = new Date(timestamp * 1000);
  const today = new Date();
  const sameDay = date.toDateString() === today.toDateString();
  return sameDay
    ? date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : date.toLocaleDateString([], { month: "short", day: "numeric" });
}

export function EmulatorActions({ session, busyAction, onAction }: Props) {
  const supported = new Set(session.capabilities);
  const hasSlots = supported.has("slot_previous") && supported.has("slot_next");

  return (
    <>
      {groups.map((group) => {
        const actions = group.actions.filter((action) => supported.has(action) && session.actions[action]);
        if (actions.length === 0) return null;
        return (
          <PanelSection title={group.title} key={group.title}>
            {group.title === "Save States" && hasSlots && (
              <>
                <PanelSectionRow>
                  <div style={{ width: "100%", textAlign: "center", opacity: 0.8 }}>
                    Current slot: <b>{session.slot}</b>
                  </div>
                </PanelSectionRow>
                {session.savestates.slice(0, 5).map((state) => (
                  <PanelSectionRow key={state.path}>
                    <div style={{ width: "100%", display: "flex", justifyContent: "space-between", opacity: 0.68, fontSize: "12px" }}>
                      <span>{state.slot === null ? "State" : `Slot ${state.slot}`}</span>
                      <span>{stateTimestamp(state.modified_at)}</span>
                    </div>
                  </PanelSectionRow>
                ))}
              </>
            )}
            {actions.map((action) => {
              const definition = session.actions[action];
              const active = session.toggles[action];
              return (
                <PanelSectionRow key={action}>
                  <ButtonItem
                    layout="below"
                    disabled={busyAction !== null}
                    onClick={() => void onAction(action)}
                  >
                    {busyAction === action ? "Working…" : `${definition.label}${active ? " — ON" : ""}`}
                  </ButtonItem>
                </PanelSectionRow>
              );
            })}
            {group.title === "Save States" && hasSlots && (
              <>
                <PanelSectionRow>
                  <ButtonItem
                    layout="below"
                    disabled={busyAction !== null}
                    onClick={() => void onAction("slot_previous")}
                  >
                    Previous Slot
                  </ButtonItem>
                </PanelSectionRow>
                <PanelSectionRow>
                  <ButtonItem
                    layout="below"
                    disabled={busyAction !== null}
                    onClick={() => void onAction("slot_next")}
                  >
                    Next Slot
                  </ButtonItem>
                </PanelSectionRow>
              </>
            )}
          </PanelSection>
        );
      })}
    </>
  );
}
