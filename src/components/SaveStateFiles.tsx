import { useEffect, useMemo, useState } from "react";
import { ButtonItem, PanelSection, PanelSectionRow } from "@decky/ui";
import { stateFilePage, stateFileSize } from "../saveStateFiles";
import type { EmulatorSession } from "../types";

export function SaveStateFiles({ session }: { session: EmulatorSession }) {
  const [expanded, setExpanded] = useState(false);
  const [page, setPage] = useState(0);
  const files = useMemo(() => stateFilePage(session.savestates, page), [session.savestates, page]);
  useEffect(() => { if (page !== files.page) setPage(files.page); }, [page, files.page]);
  if (!session.rom || (!files.total && !session.capabilities.some((action) => action === "save_state" || action === "load_state"))) return null;
  return (
    <PanelSection title="Detected Save Files">
      <PanelSectionRow>
        <ButtonItem layout="below" onClick={() => { setExpanded((value) => !value); setPage(0); }}>
          {expanded ? "Hide Save Files" : `Show Save Files (${files.total})`}
        </ButtonItem>
      </PanelSectionRow>
      {expanded && <>
        <PanelSectionRow>
          <div style={{ fontSize: "12px", opacity: 0.7 }}>
            Read-only file inventory. Slots are inferred from filenames, not synchronized with the emulator.
          </div>
        </PanelSectionRow>
        {!files.total && <PanelSectionRow>
          <div style={{ fontSize: "12px" }}>No matching files found in configured locations. This does not mean your slots are empty or Save/Load is unavailable.</div>
        </PanelSectionRow>}
        {files.items.map((file) => (
          <PanelSectionRow key={file.path}>
            <div style={{ width: "100%", overflowWrap: "anywhere" }}>
              <div>{file.slot === null ? "Slot unknown" : `File slot ${file.slot}`}</div>
              <div style={{ fontSize: "12px" }}>{file.name}</div>
              <div style={{ fontSize: "12px", opacity: 0.7 }}>
                {file.modifiedAt === null ? "Date unknown" : new Date(file.modifiedAt * 1000).toLocaleString()} • {stateFileSize(file.size)}
              </div>
            </div>
          </PanelSectionRow>
        ))}
        {files.total > 0 && <PanelSectionRow><div style={{ fontSize: "12px" }}>
          Newest first — {files.total} files — page {files.page + 1} / {files.pages}
        </div></PanelSectionRow>}
        {files.pages > 1 && <>
          <PanelSectionRow><ButtonItem layout="below" disabled={files.page === 0} onClick={() => setPage(files.page - 1)}>Previous Page</ButtonItem></PanelSectionRow>
          <PanelSectionRow><ButtonItem layout="below" disabled={files.page === files.pages - 1} onClick={() => setPage(files.page + 1)}>Next Page</ButtonItem></PanelSectionRow>
        </>}
      </>}
    </PanelSection>
  );
}
