# Contrôle du bureau par la voix pour Hyprland (Vosk)

Contrôle vocal léger et 100% local pour Linux (testé sur Arch + Hyprland). Pas de cloud, pas de LLM: Vosk hors-ligne + règles d’intentions simples.

## Fonctions

- Reconnaissance vocale hors ligne via Vosk
- Ouvrir des apps via Hyprland: `ouvre firefox`, `ouvre prism launcher`
- Suppression sécurisée via alias: `supprime <alias>` (limitée à un répertoire base)

## Prérequis (Arch)

```bash
sudo pacman -S python python-pip portaudio libnotify

# Daemon de notifications (Wayland/Hyprland)
sudo pacman -S mako
```

Dans Hyprland, lance le daemon (exemple): ajoute `exec-once = mako` à ta config Hyprland.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Modèle Vosk FR

`./start.sh` auto-télécharge le modèle FR gratuit (small) si absent et l’extrait dans `models/`.
Puis `vosk_model_path` doit pointer vers le dossier du modèle (défaut: `./models/vosk-model-small-fr-0.22`).

## Configuration

Édite `config.json`:
- `apps`: nom prononcé -> commande shell
- `delete_aliases`: alias prononcé -> chemin réel
- `delete_base_dir`: suppression autorisée uniquement sous ce dossier

Optionnel:
- `notifications_enabled`: notifications bureau (via `notify-send`)
- `notification_timeout_ms`: durée (ms)
- `app_match_threshold`: sensibilité du matching (0.5 = très sensible)

Typos / mots mal reconnus (recommandé):
- `app_aliases`: ajoute des variantes entendues par Vosk pour une app, ex:
	- `"prusa slicer": ["processeur", "prusse a cela et"]`

Maximiser la fenêtre:
- `maximize_command`: commande shell à exécuter (mets la même que ton bind Hyprland, ex: ton `windowpin.sh`).

## Lancement

```bash
./start.sh
```

## Commandes voix

Note: pour `ouvre/lance`, le nom d’app est matché de façon approximative ("marge d’erreur") si tu ne prononces pas exactement la clé de `apps`.

- Changer de bureau: `va au bureau 3` (ou `workspace 3`)
- Maximiser fenêtre active (sans vrai fullscreen): `maximise la fenetre`

Note: les mots-clés de commande sont en français (modifiable dans `intents.py`).
