from __future__ import annotations

import json
import re
import time
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from actions import ExecResult, hypr_exec, safe_delete


@dataclass
class IntentContext:
    apps: Dict[str, str]
    delete_base_dir: str
    delete_aliases: Dict[str, str]
    cooldown_ms: int = 800
    _last_action_ts: float = 0.0

    def cooldown_ok(self) -> bool:
        now = time.monotonic()
        if (now - self._last_action_ts) * 1000.0 < self.cooldown_ms:
            return False
        self._last_action_ts = now
        return True


def normalize_text(text: str) -> str:
    text = text.strip().lower()
    # Remove accents
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    # Keep letters/numbers/spaces
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


_OPEN_PATTERNS = [
    re.compile(r"^(?:ouvre|lance|demarre)\s+(?P<app>.+)$"),
]

_DELETE_PATTERNS = [
    re.compile(r"^(?:supprime|efface|delete)\s+(?P<alias>.+)$"),
]


def match_intent(raw_text: str, ctx: IntentContext) -> Optional[ExecResult]:
    text = normalize_text(raw_text)
    if not text:
        return None

    # OPEN
    for pat in _OPEN_PATTERNS:
        m = pat.match(text)
        if m:
            app_spoken = m.group("app").strip()
            command = _resolve_app_command(app_spoken, ctx.apps)
            if not command:
                return ExecResult(False, f"App inconnue: {app_spoken}")
            if not ctx.cooldown_ok():
                return ExecResult(True, "(cooldown)")
            return hypr_exec(command)

    # DELETE (alias-based)
    for pat in _DELETE_PATTERNS:
        m = pat.match(text)
        if m:
            alias = m.group("alias").strip()
            target = _resolve_delete_alias(alias, ctx.delete_aliases)
            if not target:
                return ExecResult(False, f"Alias suppression inconnu: {alias}")
            if not ctx.cooldown_ok():
                return ExecResult(True, "(cooldown)")
            return safe_delete(target=target, base_dir=ctx.delete_base_dir)

    # Optional: show config keys
    if text in {"aide", "help"}:
        return ExecResult(
            True,
            "Commandes: 'ouvre <app>' | 'lance <app>' | 'supprime <alias>'",
        )

    return None


def _resolve_app_command(app_spoken: str, apps: Dict[str, str]) -> Optional[str]:
    key = normalize_text(app_spoken)
    if key in apps:
        return apps[key]

    # Try small heuristics
    key = key.replace("launcher", "launcher").strip()
    if key in apps:
        return apps[key]

    # Match by contains
    for name, cmd in apps.items():
        if key == name or key in name or name in key:
            return cmd
    return None


def _resolve_delete_alias(alias_spoken: str, aliases: Dict[str, str]) -> Optional[str]:
    key = normalize_text(alias_spoken)
    if key in aliases:
        return aliases[key]

    for name, target in aliases.items():
        if key == name or key in name or name in key:
            return target
    return None


def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
