#!/usr/bin/env bash
set -euo pipefail

# Toggle maximize of the currently focused window on Hyprland.
# Not a real fullscreen: uses floating + resize/move to the monitor's usable area.
# State is stored per-window so it can restore the previous geometry.

usage() {
  cat <<'EOF'
windowpin.sh — Hyprland maximize toggle (no fullscreen)

Usage:
  windowpin.sh
  windowpin.sh --help

Behavior:
  - First run: makes active window floating and resizes/moves it to the monitor usable area.
  - Second run: restores previous geometry and floating/tiled state.

Requires:
  - hyprctl (Hyprland)
  - python3 (for JSON parsing; avoids jq dependency)
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! command -v hyprctl >/dev/null 2>&1; then
  echo "hyprctl introuvable" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 introuvable" >&2
  exit 1
fi

_looks_like_json() {
  local s="${1:-}"
  [[ -n "$s" && "$s" =~ ^[[:space:]]*[{\[] ]]
}

runtime_dir="${XDG_RUNTIME_DIR:-/tmp}/voice-recorgnizer"
state_dir="$runtime_dir/maximize"
mkdir -p "$state_dir"

active_json="$(hyprctl -j activewindow 2>/dev/null || true)"
if [[ -z "$active_json" ]]; then
  echo "Hyprland indisponible (hyprctl n'a rien renvoyé)" >&2
  exit 2
fi
if [[ "$active_json" == "null" ]]; then
  echo "Aucune fenêtre active" >&2
  exit 2
fi
if ! _looks_like_json "$active_json"; then
  echo "Hyprland indisponible (hyprctl n'a pas renvoyé du JSON)" >&2
  exit 2
fi

# Extract needed fields using python (avoid jq dependency)
read -r addr monitor_id at_x at_y size_w size_h is_floating < <(
  python3 - <<'PY'
import json, sys

try:
  a = json.loads(sys.stdin.read())
except Exception:
  print("", 0, 0, 0, 0, 0, 0)
  sys.exit(0)
addr = a.get('address')
# address can be int or string like '0x...'
if isinstance(addr, int):
    addr = hex(addr)
addr = str(addr or '')
mon = a.get('monitor')
try:
    mon = int(mon)
except Exception:
    mon = 0
at = a.get('at') or [0, 0]
size = a.get('size') or [0, 0]
flt = a.get('floating')
flt = 1 if flt else 0
print(addr, mon, int(at[0]), int(at[1]), int(size[0]), int(size[1]), flt)
PY
<<<"$active_json"
)

if [[ -z "$addr" || "$addr" == "None" ]]; then
  echo "Impossible de lire l'adresse de la fenêtre" >&2
  exit 3
fi

state_file="$state_dir/${addr}.json"

# Helper: try address-specific dispatch first, fallback to active window dispatch.
_hypr_move_resize() {
  local x="$1" y="$2" w="$3" h="$4"

  # Address-specific (preferred)
  if hyprctl dispatch movewindowpixel "exact $x $y,address:$addr" >/dev/null 2>&1 \
    && hyprctl dispatch resizewindowpixel "exact $w $h,address:$addr" >/dev/null 2>&1; then
    return 0
  fi

  # Active-window fallback
  hyprctl dispatch movewindowpixel "exact $x $y" >/dev/null 2>&1 || true
  hyprctl dispatch resizewindowpixel "exact $w $h" >/dev/null 2>&1 || true
  return 0
}

_hypr_toggle_floating() {
  # Address-specific
  if hyprctl dispatch togglefloating "address:$addr" >/dev/null 2>&1; then
    return 0
  fi
  # Fallback
  hyprctl dispatch togglefloating >/dev/null 2>&1 || true
}

# If we already have state, restore it.
if [[ -f "$state_file" ]]; then
  read -r was_floating old_x old_y old_w old_h < <(
  python3 - "$state_file" <<'PY'
import json
from pathlib import Path
import sys

try:
  p = Path(sys.argv[1])
  obj = json.loads(p.read_text(encoding='utf-8'))
  print(int(bool(obj.get('was_floating'))), int(obj.get('x', 0)), int(obj.get('y', 0)), int(obj.get('w', 0)), int(obj.get('h', 0)))
except Exception:
  print(0, 0, 0, 0, 0)
PY
  )

  # If it was tiled before maximize, return to tiling by toggling floating off.
  if [[ "$was_floating" -eq 1 ]]; then
    if [[ "$is_floating" -eq 0 ]]; then
      _hypr_toggle_floating
    fi
    _hypr_move_resize "$old_x" "$old_y" "$old_w" "$old_h"
  else
    # It was tiled: go back to tiled mode.
    if [[ "$is_floating" -eq 1 ]]; then
      _hypr_toggle_floating
    fi
  fi

  rm -f "$state_file"
  echo "RESTORED"
  exit 0
fi

# Save current geometry.
python3 - "$state_file" "$is_floating" "$at_x" "$at_y" "$size_w" "$size_h" <<'PY'
import json
from pathlib import Path
import sys

state_file = sys.argv[1]
was_floating = int(sys.argv[2])
x = int(sys.argv[3])
y = int(sys.argv[4])
w = int(sys.argv[5])
h = int(sys.argv[6])

state = {
  'was_floating': bool(was_floating),
  'x': x,
  'y': y,
  'w': w,
  'h': h,
}
Path(state_file).write_text(json.dumps(state), encoding='utf-8')
PY


# Ensure floating so we can resize/move.
if [[ "$is_floating" -eq 0 ]]; then
  _hypr_toggle_floating
fi

# Compute monitor usable area (subtract reserved).
monitors_json="$(hyprctl -j monitors 2>/dev/null || true)"
if [[ -z "$monitors_json" ]]; then
  echo "Hyprland indisponible (monitors vide)" >&2
  exit 4
fi
if ! _looks_like_json "$monitors_json"; then
  echo "Hyprland indisponible (monitors n'est pas du JSON)" >&2
  exit 4
fi
read -r mon_x mon_y mon_w mon_h res_l res_r res_t res_b < <(
  python3 - "$monitor_id" <<'PY'
import json, sys

try:
  mon_id = int(sys.argv[1])
except Exception:
  mon_id = 0

try:
  mons = json.loads(sys.stdin.read())
except Exception:
  mons = []
mon = None
for m in mons:
    if int(m.get('id', -1)) == mon_id:
        mon = m
        break
if mon is None:
    mon = mons[0] if mons else {'x':0,'y':0,'width':0,'height':0,'reserved':[0,0,0,0]}
res = mon.get('reserved')
# Hyprland sometimes uses dict reserved or list [top,bottom,left,right]
if isinstance(res, dict):
    top = int(res.get('top', 0))
    bottom = int(res.get('bottom', 0))
    left = int(res.get('left', 0))
    right = int(res.get('right', 0))
elif isinstance(res, (list, tuple)) and len(res) == 4:
    top, bottom, left, right = map(int, res)
else:
    top = bottom = left = right = 0
print(int(mon.get('x',0)), int(mon.get('y',0)), int(mon.get('width',0)), int(mon.get('height',0)), left, right, top, bottom)
PY
<<<"$monitors_json"
)

x=$(( mon_x + res_l ))
y=$(( mon_y + res_t ))
w=$(( mon_w - res_l - res_r ))
h=$(( mon_h - res_t - res_b ))

if (( w <= 0 || h <= 0 )); then
  echo "Dimensions écran invalides" >&2
  exit 4
fi

_hypr_move_resize "$x" "$y" "$w" "$h"

echo "MAXIMIZED"
