import { ButtonItem, Navigation, PanelSection, PanelSectionRow } from "@decky/ui";
import { toaster } from "@decky/api";
import type { EmulatorSession } from "../types";

export function Documents({ documents }: { documents: EmulatorSession["documents"] }) {
  if (documents.length === 0) return null;

  const openDocument = (url: string) => {
    try {
      Navigation.NavigateToExternalWeb(url);
      Navigation.CloseSideMenus();
    } catch (error) {
      toaster.toast({ title: "Cannot open document", body: String(error) });
    }
  };

  return (
    <PanelSection title="Documents">
      {documents.map((document) => (
        <PanelSectionRow key={document.id}>
          <ButtonItem
            layout="below"
            description={document.format.toUpperCase()}
            onClick={() => openDocument(document.url)}
          >
            {document.title}
          </ButtonItem>
        </PanelSectionRow>
      ))}
    </PanelSection>
  );
}
