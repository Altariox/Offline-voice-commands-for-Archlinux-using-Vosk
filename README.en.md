# Voice Desktop Control for Hyprland (Vosk)

Offline voice commands for Hyprland using Vosk. Launch apps and safely delete files via aliases.

## Features

- 100% offline speech-to-text using Vosk
- Launch apps via Hyprland: `ouvre firefox`, `ouvre prism launcher`
- Safe deletion via aliases: `supprime <alias>` (restricted to a base directory)

## Requirements (Arch)

```bash
sudo pacman -S python python-pip portaudio libnotify

# Notification daemon (Wayland/Hyprland)
sudo pacman -S mako
```

In Hyprland, start the daemon (example): add `exec-once = mako` to your Hyprland config.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Vosk French model

`./start.sh` auto-downloads the free FR model (small) if missing and extracts it into `models/`.
Then `vosk_model_path` should point to the model directory (default: `./models/vosk-model-small-fr-0.22`).

## Configure

Edit `config.json`:
- `apps`: spoken name -> shell command
- `delete_aliases`: spoken alias -> real path
- `delete_base_dir`: only paths inside this directory can be deleted

Optional:
- `notifications_enabled`: desktop notifications (via `notify-send`)
- `notification_timeout_ms`: timeout (ms)
- `app_match_threshold`: matching sensitivity (0.5 = very sensitive)

Typos / Vosk variants:
- `app_aliases`: map `app_name` -> list of variants Vosk might output (example: `"prusa slicer": ["processeur", "prusse a cela et"]`).

Maximize:
- `maximize_command`: shell command executed when you say "maximise la fenetre" (set it to the same script used by your Hyprland bind).

## Run

```bash
./start.sh
```

Or:

```bash
source .venv/bin/activate
python main.py --config ./config.json
```

## Voice commands

- `ouvre <app>` / `lance <app>` / `demarre <app>`
- `va au bureau <n>` / `workspace <n>` (switch workspace)
- `maximise la fenetre` (maximize active window, no real fullscreen)
- `supprime <alias>`

Note: the command words are French on purpose (you can change patterns in `intents.py`).
