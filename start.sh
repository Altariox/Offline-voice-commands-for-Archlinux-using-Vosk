#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

if ! command -v python >/dev/null 2>&1; then
  echo "python introuvable" >&2
  exit 1
fi

if [[ ! -d .venv ]]; then
  python -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip >/dev/null
pip install -r requirements.txt

if [[ ! -d models ]]; then
  echo "INFO: dossier 'models/' absent. Télécharge un modèle Vosk FR et mets-le dans ./models" >&2
fi

exec python main.py --config ./config.json
