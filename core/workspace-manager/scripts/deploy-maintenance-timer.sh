#!/usr/bin/env bash
# Deploy only the project quarantine purge timer from this source tree.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_TIMER="${SCRIPT_DIR}/../config/systemd/cc-projects-purge.timer"
USER_SYSTEMD_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
TARGET_TIMER="${USER_SYSTEMD_DIR}/cc-projects-purge.timer"
STATE_BACKUPS="${XDG_STATE_HOME:-$HOME/.local/state}/cc-projects/backups"

case "${1:---dry-run}" in
  --dry-run)
    printf 'Would install %s -> %s\n' "${SOURCE_TIMER}" "${TARGET_TIMER}"
    printf 'Would reload user systemd and enable/restart cc-projects-purge.timer\n'
    exit 0
    ;;
  --apply) ;;
  *) printf 'Usage: %s [--dry-run|--apply]\n' "$0" >&2; exit 2 ;;
esac

[[ -s "${SOURCE_TIMER}" ]] || { printf 'Missing source timer\n' >&2; exit 1; }
command -v systemctl >/dev/null 2>&1 || { printf 'systemctl is required\n' >&2; exit 1; }

install -d -m 0755 "${USER_SYSTEMD_DIR}" "${STATE_BACKUPS}"
if [[ -e "${TARGET_TIMER}" ]]; then
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  backup="${STATE_BACKUPS}/cc-projects-purge.timer.${stamp}"
  [[ ! -e "${backup}" ]] || { printf 'Backup exists: %s\n' "${backup}" >&2; exit 1; }
  cp -p -- "${TARGET_TIMER}" "${backup}"
  printf 'Backed up previous timer: %s\n' "${backup}"
fi

install -m 0644 "${SOURCE_TIMER}" "${TARGET_TIMER}"
systemctl --user daemon-reload
systemctl --user enable --now cc-projects-purge.timer
systemctl --user restart cc-projects-purge.timer
systemctl --user is-active --quiet cc-projects-purge.timer
printf 'Installed daily 14-day quarantine purge timer: %s\n' "${TARGET_TIMER}"
