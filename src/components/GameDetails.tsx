import { useMemo, useState } from "react";
import { ButtonItem, PanelSection, PanelSectionRow } from "@decky/ui";
import { gameDetails } from "../gameDetails";

export function GameDetails({ metadata }: { metadata: Record<string, string> }) {
  const [expanded, setExpanded] = useState(false);
  const [page, setPage] = useState(0);
  const details = useMemo(() => gameDetails(metadata), [metadata]);
  const current = Math.min(page, Math.max(0, details.descriptionPages.length - 1));
  if (!details.rows.length && !details.descriptionPages.length) return null;
  return (
    <PanelSection title="Game Details">
      <PanelSectionRow>
        <ButtonItem layout="below" onClick={() => { setExpanded((value) => !value); setPage(0); }}>
          {expanded ? "Hide Game Details" : "Show Game Details"}
        </ButtonItem>
      </PanelSectionRow>
      {expanded && <>
        {details.rows.map(([label, value]) => (
          <PanelSectionRow key={label}>
            <div style={{ width: "100%", overflowWrap: "anywhere" }}>
              <div style={{ opacity: 0.55, fontSize: "12px" }}>{label}</div>
              <div>{value}</div>
            </div>
          </PanelSectionRow>
        ))}
        {details.descriptionPages.length > 0 && <>
          <PanelSectionRow>
            <div style={{ fontSize: "12px", lineHeight: 1.4, whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
              {details.descriptionPages[current]}
            </div>
          </PanelSectionRow>
          {details.descriptionPages.length > 1 && <>
            <PanelSectionRow>Description — {current + 1} / {details.descriptionPages.length}</PanelSectionRow>
            <PanelSectionRow>
              <ButtonItem layout="below" disabled={current === 0} onClick={() => setPage(current - 1)}>Previous Page</ButtonItem>
            </PanelSectionRow>
            <PanelSectionRow>
              <ButtonItem layout="below" disabled={current >= details.descriptionPages.length - 1} onClick={() => setPage(current + 1)}>Next Page</ButtonItem>
            </PanelSectionRow>
          </>}
          {details.descriptionTruncated && <PanelSectionRow>Description limited to 12,000 characters.</PanelSectionRow>}
        </>}
        <PanelSectionRow><div style={{ opacity: 0.55, fontSize: "12px" }}>Source: local ES-DE metadata</div></PanelSectionRow>
      </>}
    </PanelSection>
  );
}
