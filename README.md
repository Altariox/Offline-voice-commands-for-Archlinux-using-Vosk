# Voice Desktop Control for Hyprland (Vosk)

README languages:
- English: README.en.md
- Español: README.es.md
- Français: README.fr.md

Quick summary: fully local voice control for Arch/Hyprland (offline Vosk STT + simple intent rules).

## Quick start

### System deps (Arch)

```bash
sudo pacman -S python python-pip portaudio
```

### Python deps

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Vosk French model

Télécharge un modèle FR (ex: small) et dézippe dans `models/`.
Dans la config, pointe `vosk_model_path` vers le dossier du modèle.

Exemples (à adapter):
- `models/vosk-model-small-fr-0.22/`

## Config

1) Copie l’exemple:

```bash
cp config.example.json config.json
```

2) Édite `config.json`:
- `apps`: dictionnaire "nom prononcé" -> commande shell
- `delete_aliases`: dictionnaire "alias prononcé" -> chemin réel
- `delete_base_dir`: répertoire racine autorisé pour la suppression

Important: `supprime ...` only deletes targets inside `delete_base_dir`.

## Run

```bash
./start.sh
```

## Voice commands

- `ouvre firefox`
- `lance prism launcher`
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
