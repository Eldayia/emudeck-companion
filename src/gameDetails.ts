export interface GameDetailsData {
  rows: Array<[string, string]>;
  descriptionPages: string[];
  descriptionTruncated: boolean;
}

function text(value: unknown): string {
  if (typeof value !== "string") return "";
  const result = value.trim();
  return result.toLowerCase() === "unknown" ? "" : result;
}

function clip(value: string, length: number): string {
  const result = value.slice(0, length);
  return /[\uD800-\uDBFF]$/.test(result) ? result.slice(0, -1) : result;
}

export function releaseDate(value: unknown): string | null {
  const raw = text(value);
  // ES-DE's default date is a sentinel, not an actual release date.
  if (raw === "19700101T000000") return null;
  const match = /^(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2})(\d{2}))?$/.exec(raw)
    ?? /^(\d{4})-(\d{2})-(\d{2})$/.exec(raw);
  if (!match) return null;
  const [, year, month, day, hour = "0", minute = "0", second = "0"] = match;
  if (Number(hour) > 23 || Number(minute) > 59 || Number(second) > 59 || Number(year) === 0) return null;
  const date = new Date(`${year}-${month}-${day}T00:00:00Z`);
  if (date.getUTCFullYear() !== Number(year) || date.getUTCMonth() + 1 !== Number(month) || date.getUTCDate() !== Number(day)) return null;
  return `${year}-${month}-${day}`;
}

export function gameDetails(metadata: Record<string, unknown>): GameDetailsData {
  const rows: Array<[string, string]> = [];
  for (const [key, label] of [["genre", "Genre"], ["developer", "Developer"], ["publisher", "Publisher"], ["players", "Players"]]) {
    const value = text(metadata[key]);
    if (value) rows.push([label, value.length > 160 ? `${clip(value, 157)}…` : value]);
  }
  const date = releaseDate(metadata.releasedate);
  if (date) rows.push(["Release date", date]);
  const rawRating = text(metadata.rating);
  if (/^(?:\d+(?:\.\d+)?|\.\d+)$/.test(rawRating)) {
    const rating = Number(rawRating);
    // Zero is ES-DE's default/unrated value; don't display it as a bad review.
    if (rating > 0 && rating <= 1) rows.push(["ES-DE rating", `${Math.round(rating * 100)}%`]);
  }
  const description = text(metadata.desc);
  const descriptionTruncated = description.length > 12000;
  let remaining = clip(description, 12000);
  // Avoid cutting a UTF-16 surrogate pair at the safety limit or page boundary.
  const descriptionPages: string[] = [];
  while (remaining.length) {
    let end = Math.min(400, remaining.length);
    if (end < remaining.length) {
      const boundary = remaining.slice(0, end + 1).search(/\s\S*$/);
      if (boundary >= 200) end = boundary;
      if (/[\uD800-\uDBFF]/.test(remaining[end - 1])) end--;
    }
    descriptionPages.push(remaining.slice(0, end).trim());
    remaining = remaining.slice(end).trimStart();
  }
  return { rows, descriptionPages, descriptionTruncated };
}
