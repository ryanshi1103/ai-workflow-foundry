#!/usr/bin/env bash
#
# Restore the pre-install Fedora GRUB defaults, regenerate the current menu,
# and remove only the Minimal Focus theme payload.

set -euo pipefail
IFS=$'\n\t'

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly BACKUP_SCRIPT="${SCRIPT_DIR}/backup.sh"
readonly STATE_ROOT="/var/lib/grub-x-minimal-theme"
readonly BACKUP_ROOT="${STATE_ROOT}/backups"
readonly ACTIVE_BACKUP_FILE="${STATE_ROOT}/active-backup"
readonly THEME_NAME="grub-x-minimal"

if [[ -t 1 ]] && command -v tput >/dev/null 2>&1; then
  readonly C_INFO="$(tput setaf 6)"
  readonly C_OK="$(tput setaf 2)"
  readonly C_WARN="$(tput setaf 3)"
  readonly C_ERR="$(tput setaf 1)"
  readonly C_RESET="$(tput sgr0)"
else
  readonly C_INFO=""
  readonly C_OK=""
  readonly C_WARN=""
  readonly C_ERR=""
  readonly C_RESET=""
fi

info() { printf '%s[INFO]%s %s\n' "${C_INFO}" "${C_RESET}" "$*"; }
ok() { printf '%s[ OK ]%s %s\n' "${C_OK}" "${C_RESET}" "$*"; }
warn() { printf '%s[WARN]%s %s\n' "${C_WARN}" "${C_RESET}" "$*" >&2; }
die() { printf '%s[FAIL]%s %s\n' "${C_ERR}" "${C_RESET}" "$*" >&2; exit 1; }

confirm() {
  local answer
  [[ -t 0 ]] || die "Interactive confirmation requires a terminal."
  read -r -p "Restore the original GRUB settings and remove the theme? [y/N] " answer
  [[ "${answer}" == "y" || "${answer}" == "Y" ]] || die "Cancelled; nothing changed."
}

require_fedora() {
  [[ -r /etc/os-release ]] || die "Cannot read /etc/os-release."
  # shellcheck disable=SC1091
  source /etc/os-release
  [[ "${ID:-}" == "fedora" ]] \
    || die "This uninstaller supports Fedora only (detected: ${ID:-unknown})."
}

detect_grub_cfg() {
  if [[ -f /boot/grub2/grub.cfg ]]; then
    printf '/boot/grub2/grub.cfg\n'
  elif [[ -f /boot/grub/grub.cfg ]]; then
    printf '/boot/grub/grub.cfg\n'
  else
    die "Could not find /boot/grub2/grub.cfg or /boot/grub/grub.cfg."
  fi
}

detect_mkconfig() {
  if command -v grub2-mkconfig >/dev/null 2>&1; then
    command -v grub2-mkconfig
  elif command -v grub-mkconfig >/dev/null 2>&1; then
    command -v grub-mkconfig
  else
    die "Neither grub2-mkconfig nor grub-mkconfig is installed."
  fi
}

detect_script_check() {
  if command -v grub2-script-check >/dev/null 2>&1; then
    command -v grub2-script-check
  elif command -v grub-script-check >/dev/null 2>&1; then
    command -v grub-script-check
  else
    die "Neither grub2-script-check nor grub-script-check is installed."
  fi
}

safe_remove_theme() {
  local target="$1"
  case "${target}" in
    /boot/grub2/themes/grub-x-minimal|/boot/grub/themes/grub-x-minimal) ;;
    *) die "Refusing to remove unexpected path: ${target}" ;;
  esac
  [[ ! -e "${target}" ]] || find "${target}" -xdev -depth -delete
}

cleanup() {
  local exit_code=$?
  if [[ -n "${TEMP_GRUB_CFG:-}" && -e "${TEMP_GRUB_CFG}" ]]; then
    unlink "${TEMP_GRUB_CFG}"
  fi
  exit "${exit_code}"
}
trap cleanup EXIT

(($# == 0)) || die "This uninstaller takes no options and always asks for confirmation."
((EUID == 0)) || die "Run as root with sudo."
require_fedora

[[ -f "${ACTIVE_BACKUP_FILE}" ]] || die "No active pre-install backup was found."
backup_dir="$(head -n 1 "${ACTIVE_BACKUP_FILE}")"
case "${backup_dir}" in
  "${BACKUP_ROOT}/"*) ;;
  *) die "The active backup path is outside ${BACKUP_ROOT}." ;;
esac

[[ -d "${backup_dir}" ]] || die "Backup directory is missing: ${backup_dir}"
[[ -f "${backup_dir}/default-grub" ]] || die "Backup is missing default-grub."
[[ -f "${backup_dir}/grub.cfg" ]] || die "Backup is missing emergency grub.cfg."
[[ -f "${backup_dir}/SHA256SUMS" ]] || die "Backup is missing SHA256SUMS."

(
  cd "${backup_dir}"
  sha256sum --check --status SHA256SUMS
) || die "Backup checksum verification failed."

readonly GRUB_CFG="$(detect_grub_cfg)"
readonly GRUB_ROOT="$(dirname -- "${GRUB_CFG}")"
readonly THEME_DEST="${GRUB_ROOT}/themes/${THEME_NAME}"
readonly MKCONFIG="$(detect_mkconfig)"
readonly SCRIPT_CHECK="$(detect_script_check)"

printf '\nUninstall plan:\n'
printf '  Safety-backup current state under: %s\n' "${BACKUP_ROOT}"
printf '  Restore settings: %s -> /etc/default/grub\n' "${backup_dir}/default-grub"
printf '  Regenerate menu:  %s\n' "${GRUB_CFG}"
printf '  Remove theme:     %s\n' "${THEME_DEST}"
printf '  Keep snapshots:   %s\n' "${BACKUP_ROOT}"
printf '\nThe old grub.cfg remains an emergency snapshot only. Regenerating avoids\n'
printf 'discarding kernels installed since the theme was enabled.\n'
printf '\nExplicitly unchanged: kernels, BLS, /boot/efi, EFI variables,\n'
printf 'Secure Boot, NVIDIA, os-prober and kernel arguments.\n\n'

confirm
"${BACKUP_SCRIPT}" --assume-confirmed

install -m 0644 "${backup_dir}/default-grub" /etc/default/grub
if command -v restorecon >/dev/null 2>&1; then
  restorecon /etc/default/grub >/dev/null \
    || warn "Could not refresh the SELinux context for /etc/default/grub."
fi

TEMP_GRUB_CFG="$(mktemp "${GRUB_ROOT}/.grub.cfg.XXXXXX")"
info "Regenerating the current GRUB menu from the restored settings..."
"${MKCONFIG}" -o "${TEMP_GRUB_CFG}"
"${SCRIPT_CHECK}" "${TEMP_GRUB_CFG}"

chmod --reference="${GRUB_CFG}" "${TEMP_GRUB_CFG}"
chown --reference="${GRUB_CFG}" "${TEMP_GRUB_CFG}"
mv -- "${TEMP_GRUB_CFG}" "${GRUB_CFG}"
TEMP_GRUB_CFG=""

if command -v restorecon >/dev/null 2>&1; then
  restorecon "${GRUB_CFG}" >/dev/null \
    || warn "Could not refresh the SELinux context for ${GRUB_CFG}."
fi

if [[ -e "${THEME_DEST}" ]]; then
  [[ -f "${THEME_DEST}/.grub-x-minimal-theme" ]] \
    || die "Theme path lacks this project's ownership marker; refusing deletion."
  safe_remove_theme "${THEME_DEST}"
fi

unlink "${ACTIVE_BACKUP_FILE}"

ok "Original GRUB settings were restored, the current menu regenerated, and the theme removed."
info "All backup archives remain at ${BACKUP_ROOT}."
warn "No reboot was performed."
