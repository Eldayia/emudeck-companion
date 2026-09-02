import { ButtonItem, Navigation, PanelSection, PanelSectionRow } from "@decky/ui";
import { toaster } from "@decky/api";
import { useState } from "react";
import { getDocumentUrl } from "../api/backend";
import type { EmulatorSession } from "../types";

export function Documents({ documents }: { documents: EmulatorSession["documents"] }) {
  const [opening, setOpening] = useState<string | null>(null);
  if (documents.length === 0) return null;

  const openDocument = async (id: string) => {
    if (opening !== null) return;
    setOpening(id);
    try {
      const url = await getDocumentUrl(id);
      if (!url) throw new Error("The document is no longer available");
      Navigation.NavigateToExternalWeb(url);
      Navigation.CloseSideMenus();
    } catch (error) {
      toaster.toast({ title: "Cannot open document", body: String(error) });
    } finally {
      setOpening(null);
    }
  };

  return (
    <PanelSection title="Documents">
      {documents.map((document) => (
        <PanelSectionRow key={document.id}>
          <ButtonItem
            layout="below"
            description={document.format.toUpperCase()}
            disabled={opening !== null}
            onClick={() => void openDocument(document.id)}
          >
            {opening === document.id ? "Opening…" : document.title}
          </ButtonItem>
        </PanelSectionRow>
      ))}
    </PanelSection>
  );
}
