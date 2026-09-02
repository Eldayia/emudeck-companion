import { callable } from "@decky/api";
import type { ActionResult, CompanionSettings, DiagnosticsData, EmulatorSession } from "../types";

export const getCurrentSession = callable<[], EmulatorSession | null>("get_current_session");
export const getArtwork = callable<[], string | null>("get_artwork");
export const getDocumentUrl = callable<[documentId: string], string | null>("get_document_url");
export const executeAction = callable<[action: string], ActionResult>("execute_action");
export const reportKeyboardDelivery = callable<
  [requestId: string, delivered: boolean, error: string], { ok: boolean }
>("report_keyboard_delivery");
export const refreshDetection = callable<[], EmulatorSession | null>("refresh_detection");
export const getDiagnostics = callable<[], DiagnosticsData>("get_diagnostics");
export const exportDiagnostics = callable<[], { ok: boolean; path: string }>("export_diagnostics");
export const reloadProfiles = callable<[], { ok: boolean; count: number }>("reload_profiles");
export const getSettings = callable<[], CompanionSettings>("get_settings");
export const updateSettings = callable<[changes: Partial<CompanionSettings>], CompanionSettings>("update_settings");
export const configureRetroArchNetwork = callable<
  [enabled: boolean], { ok: boolean; message: string; path?: string; backup?: string }
>("configure_retroarch_network");
