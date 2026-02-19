from __future__ import annotations

import argparse
import json
import queue
import sys
import time
from pathlib import Path

import sounddevice as sd
from vosk import KaldiRecognizer, Model

from intents import IntentContext, build_apps_map, load_config, match_intent, normalize_text


def _print(msg: str) -> None:
    print(msg, flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Assistant vocal local (Vosk + Hyprland)")
    parser.add_argument(
        "--config",
        default="./config.json",
        help="Chemin config JSON (défaut: ./config.json)",
    )
    args = parser.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        _print(f"Config introuvable: {cfg_path}\nCopie config.example.json -> config.json")
        return 2

    cfg = load_config(str(cfg_path))

    model_path = Path(cfg["vosk_model_path"]).expanduser()
    if not model_path.exists():
        _print(f"Modèle Vosk introuvable: {model_path}")
        return 3

    sample_rate = int(cfg.get("sample_rate", 16000))
    device = cfg.get("device", None)

    wake_word = normalize_text(str(cfg.get("wake_word", "assistant")))
    require_wake_word = bool(cfg.get("require_wake_word", False))

    ctx = IntentContext(
        apps=build_apps_map({k: str(v) for k, v in cfg.get("apps", {}).items()}),
        delete_base_dir=str(cfg.get("delete_base_dir", str(Path.home()))),
        delete_aliases={normalize_text(k): v for k, v in cfg.get("delete_aliases", {}).items()},
        cooldown_ms=int(cfg.get("cooldown_ms", 800)),
    )

    _print("Chargement modèle Vosk...")
    model = Model(str(model_path))
    rec = KaldiRecognizer(model, sample_rate)

    audio_queue: queue.Queue[bytes] = queue.Queue()

    def callback(indata, frames, time_info, status):  # noqa: ANN001
        if status:
            # Avoid spamming
            return
        audio_queue.put(bytes(indata))

    _print("Écoute micro... (CTRL+C pour quitter)")
    if require_wake_word:
        _print(f"Wake word actif: '{wake_word}'")

    listening_armed = not require_wake_word
    last_wake_ts = 0.0

    with sd.RawInputStream(
        samplerate=sample_rate,
        blocksize=8000,
        device=device,
        dtype="int16",
        channels=1,
        callback=callback,
    ):
        while True:
            data = audio_queue.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = (result.get("text") or "").strip()
                if not text:
                    continue

                norm = normalize_text(text)

                if require_wake_word:
                    if not listening_armed:
                        if wake_word in norm.split() or norm.endswith(wake_word):
                            listening_armed = True
                            last_wake_ts = time.monotonic()
                            _print("(wake)")
                        continue

                    # Auto-disarm after 6s
                    if time.monotonic() - last_wake_ts > 6.0:
                        listening_armed = False
                        continue

                action = match_intent(text, ctx)
                if action is not None and action.message != "(cooldown)":
                    _print(action.message)

            # else: partials ignored for perf/simplicity


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        _print("Bye")
        raise
