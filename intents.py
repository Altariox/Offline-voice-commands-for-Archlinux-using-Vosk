from __future__ import annotations

import json
import re
import time
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from itertools import product
from typing import Any, Dict, Optional

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
    # FR + EN verbs (Vosk FR can still output English-ish words sometimes)
    re.compile(r"^(?:ouvre|lance|demarre|open|launch|start|run)\s+(?P<app>.+)$"),
]

_DELETE_PATTERNS = [
    re.compile(r"^(?:supprime|efface|delete)\s+(?P<alias>.+)$"),
]


@dataclass(frozen=True)
class ResolvedApp:
    name: str
    command: str
    score: float
    exact: bool


_APP_ARTICLES = [
    "le",
    "la",
    "les",
    "un",
    "une",
    "du",
    "de",
    "des",
    "mon",
    "ma",
    "mes",
]


def build_apps_map(apps_cfg: Dict[str, str]) -> Dict[str, str]:
    """Build a normalized app map with many aliases.

    Goal: tolerate typical Vosk mis-hearings in FR, plus some EN words.
    - Never overwrites explicit user keys.
    - Generates many extra keys (aliases) per app.
    """
    explicit: Dict[str, str] = {}
    for name, cmd in apps_cfg.items():
        key = normalize_text(name)
        if key:
            explicit[key] = str(cmd)

    expanded: Dict[str, str] = dict(explicit)
    for canonical_name, cmd in explicit.items():
        for alias in _generate_app_aliases(canonical_name):
            if alias and alias not in expanded:
                expanded[alias] = cmd
    return expanded


def _plural_toggle(token: str) -> set[str]:
    if len(token) <= 2:
        return {token}
    if token.endswith("s"):
        return {token, token[:-1]}
    return {token, token + "s"}


def _tokens_variants(tokens: list[str]) -> set[str]:
    if not tokens:
        return set()
    choices = [_plural_toggle(t) for t in tokens]
    out: set[str] = set()
    for combo in product(*choices):
        out.add(" ".join(combo))
    return out


def _generate_app_aliases(canonical_key: str) -> set[str]:
    """Generate lots of normalized aliases for one app key."""
    key = normalize_text(canonical_key)
    if not key:
        return set()

    tokens = key.split()
    variants: set[str] = set()

    # Base forms
    variants.add(key)
    variants.add(key.replace(" ", ""))

    # With common FR articles ("ouvre le firefox")
    for art in _APP_ARTICLES:
        variants.add(f"{art} {key}")

    # Pluralization toggles (clients/client, etc.)
    variants |= _tokens_variants(tokens)

    # Common role words (browser/navigateur/client/launcher/slicer)
    role_words = {
        "browser",
        "navigateur",
        "client",
        "launcher",
        "slicer",
        "sliceur",
        "editor",
        "editeur",
    }
    # If role already present, also accept without it
    base_tokens = [t for t in tokens if t not in role_words]
    base = " ".join(base_tokens) if base_tokens else key
    if base and base != key:
        variants.add(base)
        variants.add(base.replace(" ", ""))

    # Add browser/navigateur for known browsers
    if key in {"firefox", "chromium", "brave", "brave browser"} or "browser" in tokens or "navigateur" in tokens:
        for w in ["browser", "navigateur", "navigateur web"]:
            variants.add(f"{base} {w}")
            variants.add(f"{w} {base}")

    # Add slicer/sliceur for slicers
    if "slicer" in tokens or "sliceur" in tokens or "slicer" in key or "sliceur" in key:
        for w in ["slicer", "sliceur"]:
            variants.add(f"{base} {w}")
            variants.add(f"{w} {base}")

    # Common multi-word join/split
    if len(tokens) >= 2:
        variants.add(tokens[0])
        variants.add(" ".join(tokens[:2]))
        variants.add(" ".join(tokens[-2:]))

    # App-specific high-value aliases (still normalized)
    if key in {"chromium"}:
        variants |= {"chrome", "google chrome", "chrom"}
    if key in {"brave", "brave browser"}:
        variants |= {"brave", "brave navigateur", "navigateur brave"}
    if key in {"lunar client", "lunar-client", "lunarclient", "lunar"}:
        variants |= {"lunar", "lunar clients", "lunare client", "lunare cliants", "lunaire client"}
    if key in {"prism launcher", "prismlauncher"}:
        variants |= {"prism", "prisme launcher", "prisme", "prismlauncher"}
    if key in {"prusa slicer", "prusa"}:
        variants |= {"prusa", "prusa sliceur", "prusa slicer"}
    if key in {"orca slicer", "orca"}:
        variants |= {"orca", "orca sliceur", "orca slicer"}
    if key in {"libreoffice", "libre office"}:
        variants |= {"libreoffice", "libre office", "libre office writer", "libre office calc"}
    if key in {"onlyoffice", "only office"}:
        variants |= {"onlyoffice", "only office", "onmly office", "only ofice", "only ofis"}
    if key in {"discord"}:
        variants |= {"discorde", "discor", "dis code"}
    if key in {"shotcut"}:
        variants |= {"shot cut", "shotcut", "short cut"}

    # Normalize once again to be safe and drop empties
    normalized = {normalize_text(v) for v in variants}
    return {v for v in normalized if v}


def match_intent(raw_text: str, ctx: IntentContext) -> Optional[ExecResult]:
    text = normalize_text(raw_text)
    if not text:
        return None

    # OPEN
    for pat in _OPEN_PATTERNS:
        m = pat.match(text)
        if m:
            app_spoken = m.group("app").strip()
            resolved = _resolve_app(app_spoken, ctx.apps)
            if resolved is None:
                return ExecResult(False, f"App inconnue: {app_spoken}")
            if not ctx.cooldown_ok():
                return ExecResult(True, "(cooldown)")
            result = hypr_exec(resolved.command)
            if not resolved.exact and result.ok:
                return ExecResult(
                    True,
                    f"{result.message} (deviné: '{app_spoken}' -> '{resolved.name}', score={resolved.score:.2f})",
                )
            if not resolved.exact and not result.ok:
                return ExecResult(
                    False,
                    f"{result.message} (tenté: '{app_spoken}' -> '{resolved.name}', score={resolved.score:.2f})",
                )
            return result

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
            "Commandes: 'ouvre <app>' | 'lance <app>' | 'supprime <alias>' (apps: match approximatif)",
        )

    return None


def _token_set(text: str) -> set[str]:
    return {t for t in text.split() if t}


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _app_match_score(spoken_key: str, app_key: str) -> float:
    """Lightweight fuzzy score in [0, 1]."""
    if not spoken_key or not app_key:
        return 0.0

    # Strong boost for substring relationship on non-trivial inputs
    if len(spoken_key) >= 4 and (spoken_key in app_key or app_key in spoken_key):
        base = 0.88
    else:
        base = 0.0

    spoken_nospace = spoken_key.replace(" ", "")
    app_nospace = app_key.replace(" ", "")
    char_sim = max(
        _similarity(spoken_key, app_key),
        _similarity(spoken_nospace, app_nospace),
    )
    st = _token_set(spoken_key)
    at = _token_set(app_key)
    if st and at:
        token_jaccard = len(st & at) / len(st | at)
    else:
        token_jaccard = 0.0

    # Combine: mostly char-level, with token overlap as stabilizer.
    # Important: never penalize strong char similarity just because tokenization differs
    # (e.g. "fire fox" vs "firefox").
    combined = (0.80 * char_sim) + (0.20 * token_jaccard)
    return max(base, combined, char_sim)


def _resolve_app(app_spoken: str, apps: Dict[str, str]) -> Optional[ResolvedApp]:
    key = normalize_text(app_spoken)
    if not key:
        return None

    if key in apps:
        return ResolvedApp(name=key, command=apps[key], score=1.0, exact=True)

    # Match by contains first (cheap + usually safe)
    for name, cmd in apps.items():
        if key == name or (len(key) >= 4 and (key in name or name in key)):
            return ResolvedApp(name=name, command=cmd, score=0.90, exact=False)

    # Fuzzy: pick best match above threshold
    best: Optional[ResolvedApp] = None
    for name, cmd in apps.items():
        score = _app_match_score(key, name)
        if best is None or score > best.score:
            best = ResolvedApp(name=name, command=cmd, score=score, exact=False)

    if best is None:
        return None

    # Avoid accidental launches on extremely short inputs
    if len(key) < 4 and best.score < 0.90:
        return None

    # Threshold avoids launching random apps on very weak matches
    if best.score < 0.72:
        return None
    return best


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
