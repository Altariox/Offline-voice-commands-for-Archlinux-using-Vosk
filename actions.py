from __future__ import annotations

import os
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
