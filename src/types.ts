export interface ActionDefinition {
  label: string;
  method: string;
  keys?: string[];
  mode?: "toggle" | "hold";
  binding_source?: string;
}
export interface EmulatorSession {
  emulator: string;
  emulator_name: string;
  pid: number;
  argv: string[];
  rom: string | null;
  game_key: string | null;
  game: string | null;
  platform: string | null;
  capabilities: string[];
  available_capabilities: string[];
  hotkey_config?: {
    status?: string;
    path?: string;
    paths?: string[];
    network_settings?: { enabled_on_disk: boolean; port: number };
    native_commands?: { status: string; port: number; version?: string; reason: string };
    overrides?: {
      status: string;
      reason?: string;
      core?: string;
      directory?: string;
      layers?: { level: string; path: string }[];
    };
    scope?: string;
    disabled_actions?: Record<string, string>;
  };
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
  documents: Array<{
    id: string;
    title: string;
    path: string;
    format: string;
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
  compact_actions: boolean;
  settings_version: number;
  detection_interval_ms: number;
  show_platform: boolean;
  show_emulator: boolean;
  show_session_time: boolean;
  notifications: boolean;
  favorites: Record<string, string[]>;
  game_overrides: Record<string, GameOverride>;
}

export interface GameOverride {
  hidden_actions?: string[];
  favorites?: string[];
}

export interface DiagnosticsData {
  timestamp: number;
  system: string;
  emudeck: EmuDeckStatus;
  session: EmulatorSession | null;
  input_backend: string;
  last_action: ActionResult | null;
  document_server: {
    running: boolean;
    port: number | null;
    registered_documents: number;
  };
}
