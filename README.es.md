# Control del escritorio por voz para Hyprland (Vosk)

Control por voz ligero y 100% local para Linux (probado en Arch + Hyprland). Sin nube y sin LLM: Vosk offline + reglas simples de intención.

## Funciones

- Reconocimiento de voz offline con Vosk
- Abrir aplicaciones en Hyprland: `ouvre firefox`, `ouvre prism launcher`
- Borrado seguro por alias: `supprime <alias>` (limitado a un directorio base)

## Requisitos (Arch)

```bash
sudo pacman -S python python-pip portaudio libnotify

# Demonio de notificaciones (Wayland/Hyprland)
sudo pacman -S mako
```

En Hyprland, inicia el demonio (ejemplo): añade `exec-once = mako` a tu configuración de Hyprland.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Modelo Vosk en francés

`./start.sh` descarga automáticamente el modelo FR gratuito (small) si falta y lo extrae en `models/`.
Luego `vosk_model_path` debe apuntar al directorio del modelo (por defecto: `./models/vosk-model-small-fr-0.22`).

## Configuración

Edita `config.json`:
- `apps`: nombre hablado -> comando
- `delete_aliases`: alias hablado -> ruta real
- `delete_base_dir`: solo se borran rutas dentro de este directorio

Opcional:
- `notifications_enabled`: notificaciones de escritorio (via `notify-send`)
- `notification_timeout_ms`: duración (ms)
- `app_match_threshold`: sensibilidad del matching (0.5 = muy sensible)

Typos / variantes de Vosk:
- `app_aliases`: mapa `app` -> lista de variantes que Vosk puede devolver.

Maximizar:
- `maximize_command`: comando shell que se ejecuta al decir "maximise la fenetre" (usa el mismo script de tu bind de Hyprland).

## Ejecutar

```bash
./start.sh
```

## Comandos de voz

- `ouvre <app>` / `lance <app>` / `demarre <app>`
- Cambiar de escritorio: `va au bureau 3` / `workspace 3`
- Maximizar ventana activa (sin fullscreen real): `maximise la fenetre`
- `supprime <alias>`

Nota: las palabras de comando están en francés (puedes cambiarlas en `intents.py`).
