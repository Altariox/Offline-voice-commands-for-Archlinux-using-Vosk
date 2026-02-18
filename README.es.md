# Control del escritorio por voz para Hyprland (Vosk)

Control por voz ligero y 100% local para Linux (probado en Arch + Hyprland). Sin nube y sin LLM: Vosk offline + reglas simples de intención.

## Funciones

- Reconocimiento de voz offline con Vosk
- Abrir aplicaciones en Hyprland: `ouvre firefox`, `ouvre prism launcher`
- Borrado seguro por alias: `supprime <alias>` (limitado a un directorio base)

## Requisitos (Arch)

```bash
sudo pacman -S python python-pip portaudio
```

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Modelo Vosk en francés

Descarga un modelo Vosk FR y descomprímelo en `models/`.
Después ajusta `vosk_model_path` en `config.json`.

Ejemplo:
- `./models/vosk-model-small-fr-0.22`

## Configuración

Edita `config.json`:
- `apps`: nombre hablado -> comando
- `delete_aliases`: alias hablado -> ruta real
- `delete_base_dir`: solo se borran rutas dentro de este directorio

## Ejecutar

```bash
./start.sh
```

## Comandos de voz

- `ouvre <app>` / `lance <app>` / `demarre <app>`
- `supprime <alias>`

Nota: las palabras de comando están en francés (puedes cambiarlas en `intents.py`).
