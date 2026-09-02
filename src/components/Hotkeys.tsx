import { ButtonItem, PanelSection, PanelSectionRow } from "@decky/ui";
import { useState } from "react";
import type { EmulatorSession } from "../types";

const keyLabels: Record<string, string> = {
  leftalt: "Alt",
  leftctrl: "Ctrl",
  leftshift: "Shift",
  enter: "Enter",
  esc: "Esc",
  tab: "Tab",
  space: "Space",
  insert: "Insert",
  home: "Home",
  pageup: "Page Up",
  pagedown: "Page Down",
  delete: "Delete",
  backspace: "Backspace",
  up: "Up",
  down: "Down",
  left: "Left",
  right: "Right",
  end: "End",
};

function formatKey(key: string, slot: number): string {
  const resolved = key.replace("{slot}", slot.toString()).toLowerCase();
  if (keyLabels[resolved]) return keyLabels[resolved];
  if (/^f\d{1,2}$/.test(resolved)) return resolved.toUpperCase();
  if (resolved.length === 1) return resolved.toUpperCase();
  return resolved;
}

export function Hotkeys({ session }: { session: EmulatorSession }) {
  const [expanded, setExpanded] = useState(false);
  const entries = session.capabilities.flatMap((action) => {
    const definition = session.actions[action];
    if (definition?.method !== "hotkey" || !definition.keys?.length) return [];
    return [{ action, definition }];
  });

  if (entries.length === 0) return null;

  return (
    <PanelSection title="Hotkeys">
      <PanelSectionRow>
        <ButtonItem layout="below" onClick={() => setExpanded((value) => !value)}>
          {expanded ? "Hide Keyboard Shortcuts" : "Show Keyboard Shortcuts"}
        </ButtonItem>
      </PanelSectionRow>
      {expanded && (
        <>
          <PanelSectionRow>
            <div style={{ width: "100%", opacity: 0.58, fontSize: "12px" }}>
              Keyboard shortcuts sent by Companion to {session.emulator_name}
            </div>
          </PanelSectionRow>
          {entries.map(({ action, definition }) => (
            <PanelSectionRow key={action}>
              <div
                style={{
                  width: "100%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "12px",
                }}
              >
                <span>
                  {definition.label}
                  {definition.binding_source && (
                    <div style={{ opacity: 0.55, fontSize: "11px" }}>{definition.binding_source}</div>
                  )}
                </span>
                <span style={{ opacity: 0.72, whiteSpace: "nowrap" }}>
                  {definition.keys?.map((key) => formatKey(key, session.slot)).join(" + ")}
                </span>
              </div>
            </PanelSectionRow>
          ))}
        </>
      )}
    </PanelSection>
  );
}
