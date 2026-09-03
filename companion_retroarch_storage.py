"""Conservative, read-only savestate search paths from the resolved disk config."""
from pathlib import Path

STORAGE_KEYS = {
    "savestate_directory", "sort_savestates_enable",
    "sort_savestates_by_content_enable", "savestates_in_content_dir",
}


def storage_search(values, process, home, core, proc_root, rom, config_path=None):
    report = {"status": "not_resolved", "paths": [], "reason": "Savestate directory or sorting flags not recorded"}
    try:
        args = process.argv[1:]
        if any(arg == "--savestate" or arg.startswith("--savestate=") or arg.startswith("-S") or arg == "--subsystem" for arg in args):
            report["reason"] = "CLI savestate/subsystem override not supported for file discovery"
            return report
        if not rom or "#" in rom or "\0" in rom:
            report["reason"] = "Launch ROM missing or archive-member syntax unsupported"
            return report
        # This is an inventory candidate, not a claim about RetroArch's live
        # output path. EmuDeck's recorded directory can differ from the one
        # currently shown by RetroArch. Limit discovery to the selected standard
        # config folder (native or Flatpak), not every installed RetroArch copy.
        if (config_path is not None and config_path.is_absolute()
                and config_path.name == "retroarch.cfg" and config_path.parent.name == "retroarch"):
            report.update(status="local_candidate", paths=[str(config_path.parent / "states")],
                          reason="Local RetroArch states folder candidate; live output directory not confirmed")
        flags = {}
        for key in STORAGE_KEYS - {"savestate_directory"}:
            value = values.get(key, "").casefold()
            if value not in {"true", "false", "1", "0"}:
                return report
            flags[key] = value in {"true", "1"}
        def expand(value):
            if "\0" in value or value.startswith(":"):
                raise ValueError("Unsupported path")
            if value.startswith("~/"):
                return home / value[2:]
            path = Path(value)
            if path.is_absolute():
                return path
            return (proc_root / str(process.pid) / "cwd").resolve(strict=True) / path
        content = expand(rom)
        raw = values.get("savestate_directory", "")
        if flags["savestates_in_content_dir"]:
            base = content.parent
        elif raw and raw != "default":
            base = expand(raw)
        else:
            return report
        selected = base
        if flags["sort_savestates_by_content_enable"]:
            if content.parent.name in {"", ".", ".."}:
                raise ValueError("Missing content directory name")
            selected /= content.parent.name
        if flags["sort_savestates_enable"]:
            if not core:
                report["reason"] = "Core name unknown; cannot resolve core-sorted states"
                return report
            selected /= core
        report.update(status="configured_candidates", paths=list(dict.fromkeys([str(selected), str(base), *report["paths"]])),
                      reason="Disk-configured and local folder candidates; live output directory not confirmed")
    except (OSError, ValueError, RuntimeError):
        report["reason"] = "Savestate path unavailable or unsupported"
    return report
