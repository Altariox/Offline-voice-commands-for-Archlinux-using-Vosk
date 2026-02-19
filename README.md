# Voice Desktop Control for Hyprland (Vosk)

README languages:
- English: README.en.md
- Español: README.es.md
- Français: README.fr.md

Quick summary: offline voice commands for Hyprland using Vosk. Launch apps and safely delete files via aliases.

## Quick start

### System deps (Arch)

```bash
sudo pacman -S python python-pip portaudio libnotify

# Notification daemon (Wayland/Hyprland)
sudo pacman -S mako
```

In Hyprland, start the daemon (example): add `exec-once = mako` to your Hyprland config.

### Python deps

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Vosk French model

`./start.sh` auto-télécharge le modèle FR gratuit (small) si absent et l’extrait dans `models/`.
Ensuite `vosk_model_path` doit pointer vers le dossier du modèle (défaut: `./models/vosk-model-small-fr-0.22`).

## Config

1) Copie l’exemple:

```bash
cp config.example.json config.json
```

2) Édite `config.json`:
- `apps`: dictionnaire "nom prononcé" -> commande shell
- `delete_aliases`: dictionnaire "alias prononcé" -> chemin réel
- `delete_base_dir`: répertoire racine autorisé pour la suppression

Optionnel:
- `notifications_enabled`: active les notifications (via `notify-send`)
- `notification_timeout_ms`: durée (ms)
- `app_match_threshold`: sensibilité du matching (0.5 = très sensible)

Typos / variantes Vosk:
- `app_aliases`: dictionnaire `nom_app` -> liste de variantes entendues (ex: `"prusa slicer": ["processeur", "prusse a cela et"]`).

Maximiser:
- `maximize_command`: commande shell exécutée quand tu dis "maximise la fenetre" (mets le même script que ton bind Hyprland).

Important: `supprime ...` only deletes targets inside `delete_base_dir`.

## Run

```bash
./start.sh
```

## Voice commands

- `ouvre firefox`
- `lance prism launcher`
- `va au bureau 3`
- `maximise la fenetre`
- `supprime downloads` (alias défini dans la config)

## (Option) Démarrage auto (systemd --user)

Crée `~/.config/systemd/user/voice-recorgnizer.service`:

```ini
[Unit]
Description=Local voice control (Vosk)
After=graphical-session.target

[Service]
Type=simple
WorkingDirectory=%h/Documents/Code_projects/voice recorgnizer
ExecStart=%h/Documents/Code_projects/voice recorgnizer/.venv/bin/python %h/Documents/Code_projects/voice recorgnizer/main.py --config %h/Documents/Code_projects/voice recorgnizer/config.json
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
```

Puis:

```bash
systemctl --user daemon-reload
systemctl --user enable --now voice-recorgnizer.service
```
