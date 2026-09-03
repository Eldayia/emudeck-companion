"""Read-only UI diagnostics; kept separate to preserve installed recorder copies."""
from __future__ import annotations

import re
from pathlib import Path

from companion_esde_hooks import checked_directory, read_status, regular_file


_NAME = r"[A-Za-z_][A-Za-z0-9_.-]*"
_ATTRIBUTE = re.compile(rf'''\s+({_NAME})\s*=\s*(?:"([^"<]*)"|'([^'<]*)')''')
_OPEN = re.compile(rf'''<({_NAME})((?:\s+{_NAME}\s*=\s*(?:"[^"<]*"|'[^'<]*'))*)\s*(/?)>''')
_CLOSE = re.compile(rf"</({_NAME})\s*>")


def activation_values(text: str) -> list[str | None]:
    """Read ES-DE's flat attribute-based settings, not general-purpose XML.

    Accept fragments or one config wrapper, comments, and empty paired tags.
    No XML imports, entity expansion, DTDs, CDATA or nested setting records.
    Validate the entire supported structure before trusting the target value.
    """
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", text):
        raise ValueError("Invalid control character")
    text = re.sub(r'^\s*<\?xml\s[^?]*\?>', '', text, count=1)
    values = []
    stack: list[str] = []
    wrapper_seen = False
    record_seen = False
    position = 0
    while position < len(text):
        if text[position].isspace():
            position += 1
            continue
        if text.startswith("<!--", position):
            end = text.find("-->", position + 4)
            if end < 0 or "--" in text[position + 4:end]:
                raise ValueError("Invalid comment")
            position = end + 3
            continue
        closing = _CLOSE.match(text, position)
        if closing:
            if not stack or stack.pop() != closing[1]:
                raise ValueError("Unbalanced settings tags")
            position = closing.end()
            continue
        opening = _OPEN.match(text, position)
        if not opening:
            raise ValueError("Unsupported settings markup")
        tag, raw_attributes, self_closing = opening.groups()
        attributes = {}
        for attribute in _ATTRIBUTE.finditer(raw_attributes):
            name, double, single = attribute.groups()
            if name in attributes:
                raise ValueError("Duplicate attribute")
            attributes[name] = double if double is not None else single
        if tag == "config":
            if stack or wrapper_seen or record_seen or attributes:
                raise ValueError("Unexpected config wrapper")
            wrapper_seen = True
        else:
            if stack not in ([], ["config"]) or (wrapper_seen and not stack):
                raise ValueError("Nested or misplaced setting")
            record_seen = True
            if tag == "bool" and attributes.get("name") == "CustomEventScripts":
                values.append(attributes.get("value"))
        if not self_closing:
            stack.append(tag)
        position = opening.end()
    if stack:
        raise ValueError("Unclosed settings tags")
    return values


def read_activation(root: Path | None) -> dict:
    result = {"status": "unknown", "path": None, "reason": "ES-DE data folder not detected"}
    if root is None:
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
        values = activation_values(text)
        if len(values) != 1 or values[0] not in ("true", "false"):
            result["reason"] = "CustomEventScripts missing, duplicated or invalid"
            return result
        result.update(status="enabled_on_disk" if values[0] == "true" else "disabled_on_disk",
                      reason="Saved configuration only; runtime setting may differ")
    except (OSError, ValueError, RecursionError):
        result["reason"] = "Settings file unreadable, invalid or unsupported"
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
