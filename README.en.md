# Voice Desktop Control for Hyprland (Vosk)

Lightweight, fully local voice control for Linux (tested with Arch + Hyprland). Not cloud, not an LLM: Vosk offline STT + simple intent rules.

## Features

- 100% offline speech-to-text using Vosk
- Launch apps via Hyprland: `ouvre firefox`, `ouvre prism launcher`
- Safe deletion via aliases: `supprime <alias>` (restricted to a base directory)

## Requirements (Arch)

```bash
sudo pacman -S python python-pip portaudio
```

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Vosk French model

Download a French Vosk model and extract it into `models/`.
Then update `vosk_model_path` in `config.json`.

Example path:
- `./models/vosk-model-small-fr-0.22`

## Configure

Edit `config.json`:
- `apps`: spoken name -> shell command
- `delete_aliases`: spoken alias -> real path
- `delete_base_dir`: only paths inside this directory can be deleted

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
- `supprime <alias>`

Note: the command words are French on purpose (you can change patterns in `intents.py`).
