"""Read-only UI diagnostics; kept separate to preserve installed recorder copies."""
from __future__ import annotations

import re
from pathlib import Path

from companion_esde_hooks import checked_directory, read_status, regular_file


def read_activation(root: Path | None) -> dict:
    result = {"status": "unknown", "path": None, "reason": "ES-DE data folder not detected"}
    if root is None:
        return result
    # Optional diagnostics must not prevent the plugin from importing when
    # Decky's embedded Python lacks an XML module or its native dependency.
    try:
        from xml.etree import ElementTree as ET
    except ImportError:
        result["reason"] = "XML parser unavailable in the plugin Python runtime"
        return result
    try:
        checked_directory(root)
        files = []
        for relative in ("settings/es_settings.xml", "es_settings.xml"):
            path = root / relative
            if path.parent != root and (path.parent.exists() or path.parent.is_symlink()):
                checked_directory(path.parent)
            try:
                files.append((path, regular_file(path, 1024 * 1024)))
            except FileNotFoundError:
                continue
        if len(files) != 1:
            result["reason"] = "Multiple settings files; active file unknown" if files else "Settings file missing"
            return result
        path, raw = files[0]
        result["path"] = str(path)
        text = raw.decode("utf-8-sig")
        if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
            raise ValueError("XML declarations are not supported")
        # ES-DE also writes XML fragments with multiple top-level settings.
        text = re.sub(r'^\s*<\?xml\s[^?]*\?>', '', text, count=1)
        document = ET.fromstring(f"<settings_fragment>{text}</settings_fragment>")
        nodes = document.findall("bool") + document.findall("config/bool")
        values = [node.get("value") for node in nodes if node.get("name") == "CustomEventScripts"]
        if len(values) != 1 or values[0] not in ("true", "false"):
            result["reason"] = "CustomEventScripts missing, duplicated or invalid"
            return result
        result.update(status="enabled_on_disk" if values[0] == "true" else "disabled_on_disk",
                      reason="Saved configuration only; runtime setting may differ")
    except ImportError:
        result["reason"] = "XML parser unavailable in the plugin Python runtime"
    except (OSError, ValueError, ET.ParseError, RecursionError):
        result["reason"] = "Settings file unreadable or invalid"
    return result


def diagnostic_status(root: Path | None, rom: str | None = None) -> dict:
    result = read_status(root, rom)
    configuration = read_activation(root)
    received = result["status"] == "event_received"
    if configuration["status"] == "enabled_on_disk":
        label = "Enabled in saved ES-DE settings"
    elif configuration["status"] == "disabled_on_disk":
        label = "Disabled in saved ES-DE settings (runtime may differ)"
    else:
        label = "Saved setting unknown"
    label += "; hook event received this boot" if received else "; no valid hook event received this boot"
    result["activation"] = label
    result["activation_config"] = configuration
    return result
