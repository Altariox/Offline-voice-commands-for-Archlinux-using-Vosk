from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExecResult:
    ok: bool
    message: str


def _which(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _hypr_dispatch(*args: str) -> bool:
    if not _which("hyprctl"):
        return False
    try:
        subprocess.run(
            ["hyprctl", "dispatch", *args],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def hypr_exec(command: str) -> ExecResult:
    """Execute an app command under Hyprland if possible."""
    command = command.strip()
    if not command:
        return ExecResult(False, "Commande vide")

    if _which("hyprctl"):
        try:
            subprocess.run(
                ["hyprctl", "dispatch", "exec", command],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return ExecResult(True, f"Lancé: {command}")
        except subprocess.CalledProcessError:
            # Fallback below
            pass

    try:
        subprocess.Popen(command, shell=True)
        return ExecResult(True, f"Lancé: {command}")
    except Exception as exc:  # noqa: BLE001
        return ExecResult(False, f"Erreur lancement: {exc}")


def hypr_workspace(number: int) -> ExecResult:
    """Switch to workspace number (Hyprland)."""
    if number <= 0:
        return ExecResult(False, "Numéro de bureau invalide")
    if not _which("hyprctl"):
        return ExecResult(False, "hyprctl introuvable")
    ok = _hypr_dispatch("workspace", str(int(number)))
    if ok:
        return ExecResult(True, f"Bureau: {int(number)}")
    return ExecResult(False, f"Impossible d'aller au bureau {int(number)}")


def hypr_maximize_active() -> ExecResult:
    return hypr_maximize_active_with_command(None)


def hypr_maximize_active_with_command(command: str | None) -> ExecResult:
    """Maximize the active window (Hyprland).

    If `command` is provided, it is executed with `shell=True`.
    This is intended to mirror the user's Hyprland bind, e.g. a window pin/maximize script.

    Otherwise falls back to `hyprctl dispatch fakefullscreen` (best-effort).
    """
    if command is not None:
        cmd = command.strip()
        if cmd:
            try:
                subprocess.Popen(cmd, shell=True)
                return ExecResult(True, "Fenêtre maximisée")
            except Exception as exc:  # noqa: BLE001
                return ExecResult(False, f"Erreur maximisation: {exc}")

    if not _which("hyprctl"):
        return ExecResult(False, "hyprctl introuvable")
    ok = _hypr_dispatch("fakefullscreen")
    if ok:
        return ExecResult(True, "Fenêtre maximisée")
    return ExecResult(False, "Maximisation indisponible")


def close_app(command: str) -> ExecResult:
    """Best-effort close/quit an app based on its launch command.

    Uses `pkill` when available. This is intentionally simple and local.
    """
    command = command.strip()
    if not command:
        return ExecResult(False, "Commande vide")

    if not _which("pkill"):
        return ExecResult(False, "pkill introuvable (installe procps-ng)")

    try:
        parts = shlex.split(command)
    except ValueError:
        parts = [command]

    if not parts:
        return ExecResult(False, "Commande vide")

    exe = Path(parts[0]).name
    if not exe:
        exe = parts[0]

    # Common alternates
    candidates = [exe]
    if exe == "brave":
        candidates.append("brave-browser")
    if exe.lower() == "discord":
        candidates.extend(["Discord", "discord"])
    if exe == "onlyoffice-desktopeditors":
        candidates.append("DesktopEditors")
    if exe == "prismlauncher":
        candidates.extend(["PrismLauncher", "prismlauncher"])
    if exe == "lunar-client":
        candidates.append("lunar")

    # 1) Prefer exact name match
    for name in candidates:
        try:
            proc = subprocess.run(
                ["pkill", "-x", name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if proc.returncode == 0:
                return ExecResult(True, f"Fermé: {name}")
        except Exception:
            # continue to other strategies
            pass

    # 2) Fallback to matching full command line (more permissive)
    for pattern in [exe, command]:
        if not pattern:
            continue
        try:
            proc = subprocess.run(
                ["pkill", "-f", pattern],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if proc.returncode == 0:
                return ExecResult(True, f"Fermé: {exe}")
        except Exception:
            pass

    return ExecResult(False, f"Processus introuvable: {exe}")


def push_notification(
    *,
    title: str,
    message: str,
    ok: bool,
    timeout_ms: int = 2500,
) -> None:
    """Send a desktop notification (best-effort).

    On Hyprland/Wayland this typically requires a notification daemon
    (e.g. mako, dunst) plus `notify-send` (libnotify).
    """
    title = title.strip() or "Voice"
    message = message.strip()
    if not message:
        return

    if not _which("notify-send"):
        return

    urgency = "low" if ok else "normal"
    try:
        subprocess.run(
            [
                "notify-send",
                "-a",
                "voice-recorgnizer",
                "-u",
                urgency,
                "-t",
                str(int(timeout_ms)),
                title,
                message,
            ],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        # Never crash the assistant because notifications failed
        return


def safe_delete(target: str, base_dir: str) -> ExecResult:
    """Delete a file or directory only if it is inside base_dir."""
    base = Path(base_dir).expanduser().resolve()
    path = Path(target).expanduser().resolve()

    try:
        path.relative_to(base)
    except ValueError:
        return ExecResult(False, f"Refusé (hors base): {path}")

    if not path.exists():
        return ExecResult(False, f"Introuvable: {path}")

    try:
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()
        return ExecResult(True, f"Supprimé: {path}")
    except Exception as exc:  # noqa: BLE001
        return ExecResult(False, f"Erreur suppression: {exc}")
