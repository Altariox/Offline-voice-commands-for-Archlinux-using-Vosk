# Contrôle du bureau par la voix pour Hyprland (Vosk)

Contrôle vocal léger et 100% local pour Linux (testé sur Arch + Hyprland). Pas de cloud, pas de LLM: Vosk hors-ligne + règles d’intentions simples.

## Fonctions

- Reconnaissance vocale hors ligne via Vosk
- Ouvrir des apps via Hyprland: `ouvre firefox`, `ouvre prism launcher`
- Suppression sécurisée via alias: `supprime <alias>` (limitée à un répertoire base)

## Prérequis (Arch)

```bash
sudo pacman -S python python-pip portaudio
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Modèle Vosk FR

Télécharge un modèle FR et dézippe-le dans `models/`.
Puis ajuste `vosk_model_path` dans `config.json`.

Exemple:
- `./models/vosk-model-small-fr-0.22`

## Configuration

Édite `config.json`:
- `apps`: nom prononcé -> commande shell
- `delete_aliases`: alias prononcé -> chemin réel
- `delete_base_dir`: suppression autorisée uniquement sous ce dossier

## Lancement

```bash
./start.sh
```

## Commandes voix

- `ouvre <app>` / `lance <app>` / `demarre <app>`
- `supprime <alias>`

Note: les mots-clés de commande sont en français (modifiable dans `intents.py`).
