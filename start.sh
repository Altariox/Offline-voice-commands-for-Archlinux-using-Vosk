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

MODEL_URL_DEFAULT="https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip"

read_model_path() {
  if [[ -f ./config.json ]]; then
    python - <<'PY'
import json
from pathlib import Path

cfg_path = Path('config.json')
try:
    cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
    print(cfg.get('vosk_model_path', './models/vosk-model-small-fr-0.22'))
except Exception:
    print('./models/vosk-model-small-fr-0.22')
PY
  else
    echo "./models/vosk-model-small-fr-0.22"
  fi
}

extract_zip_with_python() {
  local zip_path="$1"
  local dest_dir="$2"
  python - "$zip_path" "$dest_dir" <<'PY'
import sys
import zipfile
from pathlib import Path

zip_path = Path(sys.argv[1])
dest_dir = Path(sys.argv[2])
dest_dir.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(zip_path, 'r') as zf:
    zf.extractall(dest_dir)
PY
}

download_file() {
  local url="$1"
  local out_path="$2"
  if command -v curl >/dev/null 2>&1; then
    curl -L --fail --retry 3 --retry-delay 1 -o "$out_path" "$url"
  else
    python - "$url" "$out_path" <<'PY'
import sys
import urllib.request

url = sys.argv[1]
out_path = sys.argv[2]
urllib.request.urlretrieve(url, out_path)
PY
  fi
}

ensure_vosk_model() {
  local model_path
  model_path="$(read_model_path)"

  # Expand ~
  if [[ "$model_path" == ~* ]]; then
    model_path="${model_path/#~/$HOME}"
  fi

  if [[ -d "$model_path" ]]; then
    return 0
  fi

  mkdir -p ./models
  echo "INFO: modèle Vosk manquant: $model_path" >&2
  echo "INFO: téléchargement du modèle FR (gratuit): $MODEL_URL_DEFAULT" >&2

  local tmp_dir zip_file
  tmp_dir="$(mktemp -d)"
  zip_file="$tmp_dir/vosk_fr.zip"
  trap 'rm -rf "$tmp_dir"' EXIT

  download_file "$MODEL_URL_DEFAULT" "$zip_file"

  echo "INFO: extraction du modèle..." >&2
  extract_zip_with_python "$zip_file" "./models"

  if [[ ! -d "$model_path" ]]; then
    echo "ERREUR: modèle extrait mais introuvable à l'emplacement attendu: $model_path" >&2
    echo "Vérifie le contenu de ./models/ et ajuste 'vosk_model_path' dans config.json" >&2
    return 3
  fi
}

ensure_vosk_model

exec python main.py --config ./config.json
