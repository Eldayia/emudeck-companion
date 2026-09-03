export interface StateFile {
  path: string;
  name: string;
  slot: number | null;
  modifiedAt: number | null;
  size: number | null;
}

export function stateFilePage(input: unknown, requestedPage: number) {
  const files = new Map<string, StateFile>();
  for (const value of Array.isArray(input) ? input : []) {
    if (!value || typeof value !== "object" || typeof value.path !== "string" || !value.path.trim()) continue;
    const path = value.path;
    const file: StateFile = {
      path,
      name: path.replace(/\\/g, "/").split("/").pop() || path,
      slot: Number.isSafeInteger(value.slot) && value.slot >= 0 ? value.slot : null,
      modifiedAt: typeof value.modified_at === "number" && Number.isFinite(value.modified_at)
        && value.modified_at > 0 && value.modified_at <= 8640000000000 ? value.modified_at : null,
      size: Number.isSafeInteger(value.size) && value.size >= 0 ? value.size : null,
    };
    // Keep the most recent observation if overlapping scan paths repeated a file.
    if (!files.has(path) || (files.get(path)?.modifiedAt ?? 0) < (file.modifiedAt ?? 0)) files.set(path, file);
  }
  const sorted = [...files.values()].sort((a, b) =>
    (b.modifiedAt ?? 0) - (a.modifiedAt ?? 0) || (a.path < b.path ? -1 : a.path > b.path ? 1 : 0),
  );
  const pages = Math.max(1, Math.ceil(sorted.length / 5));
  const page = Math.min(pages - 1, Math.max(0, Number.isFinite(requestedPage) ? Math.floor(requestedPage) : 0));
  return { items: sorted.slice(page * 5, page * 5 + 5), page, pages, total: sorted.length };
}

export function stateFileSize(bytes: number | null): string {
  if (bytes === null || !Number.isSafeInteger(bytes) || bytes < 0) return "Size unknown";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KiB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MiB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GiB`;
}
