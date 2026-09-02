import { callable } from "@decky/api";
import type { ActionResult, DiagnosticsData, EmulatorSession } from "../types";

export const getCurrentSession = callable<[], EmulatorSession | null>("get_current_session");
export const getArtwork = callable<[], string | null>("get_artwork");
export const executeAction = callable<[action: string], ActionResult>("execute_action");
export const refreshDetection = callable<[], EmulatorSession | null>("refresh_detection");
export const getDiagnostics = callable<[], DiagnosticsData>("get_diagnostics");
export const reloadProfiles = callable<[], { ok: boolean; count: number }>("reload_profiles");
