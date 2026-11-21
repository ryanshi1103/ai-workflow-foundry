#!/usr/bin/env bash
#
# Create a recoverable snapshot of Fedora's GRUB defaults and generated config.
# This script never changes boot settings, kernels, the ESP, Secure Boot,
# drivers, or kernel command-line arguments.

set -euo pipefail
IFS=$'\n\t'

readonly STATE_ROOT="/var/lib/grub-x-minimal-theme"
readonly BACKUP_ROOT="${STATE_ROOT}/backups"
readonly ACTIVE_BACKUP_FILE="${STATE_ROOT}/active-backup"

ASSUME_CONFIRMED=false
ACTIVATE=false

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

usage() {
  printf 'Usage: sudo %s\n' "$(basename "$0")"
}

confirm() {
  local answer
  [[ -t 0 ]] || die "Interactive confirmation requires a terminal."
  read -r -p "Create this backup? [y/N] " answer
  [[ "${answer}" == "y" || "${answer}" == "Y" ]] || die "Cancelled; nothing changed."
}

require_fedora() {
  [[ -r /etc/os-release ]] || die "Cannot read /etc/os-release."
  # shellcheck disable=SC1091
  source /etc/os-release
  [[ "${ID:-}" == "fedora" ]] || die "This project supports Fedora only (detected: ${ID:-unknown})."
}

detect_firmware() {
  if [[ -d /sys/firmware/efi ]]; then
    printf 'UEFI\n'
  else
    printf 'BIOS\n'
  fi
}

detect_grub_cfg() {
  if [[ -f /boot/grub2/grub.cfg ]]; then
    printf '/boot/grub2/grub.cfg\n'
    return
  fi

  if [[ -f /boot/grub/grub.cfg ]]; then
    printf '/boot/grub/grub.cfg\n'
    return
  fi

  die "Could not find /boot/grub2/grub.cfg or /boot/grub/grub.cfg."
}

while (($#)); do
  case "$1" in
    --assume-confirmed)
      # Internal use by install.sh/uninstall.sh after their consolidated prompt.
      ASSUME_CONFIRMED=true
      ;;
    --activate)
      # Internal use: record the first pre-install snapshot for uninstall.
      ACTIVATE=true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown option: $1"
      ;;
  esac
  shift
done

((EUID == 0)) || die "Run as root with sudo."
require_fedora

readonly FIRMWARE="$(detect_firmware)"
readonly GRUB_CFG="$(detect_grub_cfg)"
readonly DEFAULT_GRUB="/etc/default/grub"

[[ -f "${DEFAULT_GRUB}" ]] || die "Missing ${DEFAULT_GRUB}."
[[ -r "${GRUB_CFG}" ]] || die "Cannot read ${GRUB_CFG}."

printf '\nBackup plan (no boot behavior will be changed):\n'
printf '  Firmware:       %s\n' "${FIRMWARE}"
printf '  Read:           %s\n' "${DEFAULT_GRUB}"
printf '  Read:           %s\n' "${GRUB_CFG}"
printf '  Create under:   %s\n\n' "${BACKUP_ROOT}"

${ASSUME_CONFIRMED} || confirm

install -d -m 0700 "${BACKUP_ROOT}"

timestamp="$(date -u +'%Y%m%dT%H%M%SZ')"
backup_dir="${BACKUP_ROOT}/${timestamp}"
counter=0
while [[ -e "${backup_dir}" ]]; do
  ((counter += 1))
  backup_dir="${BACKUP_ROOT}/${timestamp}-${counter}"
done

install -d -m 0700 "${backup_dir}"
cp --archive -- "${DEFAULT_GRUB}" "${backup_dir}/default-grub"
cp --archive -- "${GRUB_CFG}" "${backup_dir}/grub.cfg"

{
  printf 'CREATED_UTC=%q\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  printf 'FIRMWARE=%q\n' "${FIRMWARE}"
  printf 'DEFAULT_GRUB=%q\n' "${DEFAULT_GRUB}"
  printf 'GRUB_CFG=%q\n' "${GRUB_CFG}"
} > "${backup_dir}/manifest"

(
  cd "${backup_dir}"
  sha256sum default-grub grub.cfg manifest > SHA256SUMS
)
chmod 0600 "${backup_dir}/default-grub" "${backup_dir}/grub.cfg" \
  "${backup_dir}/manifest" "${backup_dir}/SHA256SUMS"

if ${ACTIVATE}; then
  install -d -m 0700 "${STATE_ROOT}"
  if [[ -f "${ACTIVE_BACKUP_FILE}" ]]; then
    warn "An original pre-install backup is already active; it was not replaced."
  else
    printf '%s\n' "${backup_dir}" > "${ACTIVE_BACKUP_FILE}"
    chmod 0600 "${ACTIVE_BACKUP_FILE}"
  fi
fi

ok "Backup created: ${backup_dir}"
printf 'Manual recovery copies:\n'
printf '  %s/default-grub -> %s\n' "${backup_dir}" "${DEFAULT_GRUB}"
printf '  %s/grub.cfg     -> %s\n' "${backup_dir}" "${GRUB_CFG}"
