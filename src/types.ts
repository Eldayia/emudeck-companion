export interface ActionDefinition {
  label: string;
  method: string;
  keys?: string[];
  mode?: "toggle" | "hold";
}
export interface EmulatorSession {
  emulator: string;
  emulator_name: string;
  pid: number;
  argv: string[];
  rom: string | null;
  game: string | null;
  platform: string | null;
  capabilities: string[];
  actions: Record<string, ActionDefinition>;
  started_at: number;
  slot: number;
  toggles: Record<string, boolean>;
  metadata: Record<string, string>;
  discs: string[];
  current_disc: number | null;
  savestates: Array<{
    slot: number | null;
    path: string;
    modified_at: number;
    size: number;
  }>;
}

export interface ActionResult {
  ok: boolean;
  action: string;
  message: string;
  slot: number | null;
  active: boolean | null;
  keys: string[] | null;
  dispatch: "steam_input" | "signal" | "none" | string;
}

export interface EmuDeckStatus {
  detected: boolean;
  root: string | null;
  esde_detected: boolean;
  esde_root: string | null;
}

export interface CompanionSettings {
  settings_version: number;
  detection_interval_ms: number;
  show_platform: boolean;
  show_emulator: boolean;
  show_session_time: boolean;
  notifications: boolean;
  favorites: Record<string, string[]>;
}

export interface DiagnosticsData {
  timestamp: number;
  system: string;
  emudeck: EmuDeckStatus;
  session: EmulatorSession | null;
  input_backend: string;
  last_action: ActionResult | null;
}
