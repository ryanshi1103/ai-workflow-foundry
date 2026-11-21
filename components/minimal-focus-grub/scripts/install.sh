#!/usr/bin/env bash
#
# Install only the Minimal Focus GRUB2 visual theme on Fedora.
# Derived from the option/resource flow of vinceliuice/grub2-themes/install.sh.
# Never touches kernels, the ESP, EFI variables, Secure Boot, BLS, NVIDIA,
# os-prober, the default entry, timeout, or kernel command-line arguments.

set -euo pipefail
IFS=$'\n\t'

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
readonly SOURCE_THEME="${PROJECT_DIR}/theme"
readonly BACKUP_SCRIPT="${SCRIPT_DIR}/backup.sh"
readonly STATE_ROOT="/var/lib/grub-x-minimal-theme"
readonly ACTIVE_BACKUP_FILE="${STATE_ROOT}/active-backup"
readonly THEME_NAME="grub-x-minimal"

SCREEN="1080p"

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
  cat <<EOF
Usage: sudo $(basename "$0") [--screen PROFILE]

Profiles:
  1080p          1920x1080 (default)
  2k             2560x1440
  4k             3840x2160
  ultrawide      2560x1080
  ultrawide2k    3440x1440

The script always displays its plan and asks for confirmation.
EOF
}

confirm() {
  local answer
  [[ -t 0 ]] || die "Interactive confirmation requires a terminal."
  read -r -p "Install this visual-only GRUB theme? [y/N] " answer
  [[ "${answer}" == "y" || "${answer}" == "Y" ]] || die "Cancelled; nothing changed."
}

require_fedora() {
  [[ -r /etc/os-release ]] || die "Cannot read /etc/os-release."
  # shellcheck disable=SC1091
  source /etc/os-release
  [[ "${ID:-}" == "fedora" ]] \
    || die "This installer supports Fedora only (detected: ${ID:-unknown})."
}

detect_firmware() {
  if [[ -d /sys/firmware/efi ]]; then
    printf 'UEFI\n'
  else
    printf 'BIOS\n'
  fi
}

detect_grub_cfg() {
  # Fedora 34+ uses /boot/grub2/grub.cfg for both BIOS and UEFI. The file on
  # the ESP is a forwarding stub and is intentionally never considered here.
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

safe_remove_tree() {
  local target="$1"
  case "${target}" in
    "${THEMES_ROOT}/${THEME_NAME}"|"${THEMES_ROOT}/.${THEME_NAME}."*) ;;
    *) die "Refusing to remove unexpected path: ${target}" ;;
  esac
  [[ ! -e "${target}" ]] || find "${target}" -xdev -depth -delete
}

update_grub_setting() {
  local key="$1"
  local value="$2"
  local file="/etc/default/grub"
  local temp
  temp="$(mktemp /etc/default/.grub-x-minimal.XXXXXX)"

  awk -v key="${key}" -v replacement="${key}=\"${value}\"" '
    $0 ~ "^[[:space:]]*#?[[:space:]]*" key "=" {
      if (!replaced) {
        print replacement
        replaced = 1
      }
      next
    }
    { print }
    END {
      if (!replaced) {
        print replacement
      }
    }
  ' "${file}" > "${temp}"

  chmod --reference="${file}" "${temp}"
  chown --reference="${file}" "${temp}"
  mv -- "${temp}" "${file}"
  if command -v restorecon >/dev/null 2>&1; then
    restorecon "${file}" >/dev/null \
      || warn "Could not refresh the SELinux context for ${file}."
  fi
}

cleanup() {
  local exit_code=$?
  if [[ -n "${STAGING_DIR:-}" && -e "${STAGING_DIR}" ]]; then
    safe_remove_tree "${STAGING_DIR}"
  fi
  if [[ -n "${TEMP_GRUB_CFG:-}" && -e "${TEMP_GRUB_CFG}" ]]; then
    unlink "${TEMP_GRUB_CFG}"
  fi
  exit "${exit_code}"
}
trap cleanup EXIT

while (($#)); do
  case "$1" in
    -s|--screen)
      (($# >= 2)) || die "Missing value for $1."
      SCREEN="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown option: $1"
      ;;
  esac
done

case "${SCREEN}" in
  1080p)
    CONFIG_NAME="theme-1080p.txt"
    BACKGROUND_NAME="background-1080p.png"
    DENSITY="1080p"
    GFXMODE="1920x1080x32,auto"
    ;;
  2k)
    CONFIG_NAME="theme-2k.txt"
    BACKGROUND_NAME="background-2k.png"
    DENSITY="2k"
    GFXMODE="2560x1440x32,auto"
    ;;
  4k)
    CONFIG_NAME="theme-4k.txt"
    BACKGROUND_NAME="background-4k.png"
    DENSITY="4k"
    GFXMODE="3840x2160x32,auto"
    ;;
  ultrawide)
    CONFIG_NAME="theme-ultrawide.txt"
    BACKGROUND_NAME="background-ultrawide.png"
    DENSITY="1080p"
    GFXMODE="2560x1080x32,auto"
    ;;
  ultrawide2k)
    CONFIG_NAME="theme-ultrawide2k.txt"
    BACKGROUND_NAME="background-ultrawide2k.png"
    DENSITY="2k"
    GFXMODE="3440x1440x32,auto"
    ;;
  *)
    die "Unsupported screen profile: ${SCREEN}"
    ;;
esac
readonly CONFIG_NAME BACKGROUND_NAME DENSITY GFXMODE SCREEN

((EUID == 0)) || die "Run as root with sudo."
require_fedora

readonly FIRMWARE="$(detect_firmware)"
readonly GRUB_CFG="$(detect_grub_cfg)"
readonly GRUB_ROOT="$(dirname -- "${GRUB_CFG}")"
readonly THEMES_ROOT="${GRUB_ROOT}/themes"
readonly THEME_DEST="${THEMES_ROOT}/${THEME_NAME}"
readonly THEME_FILE="${THEME_DEST}/theme.txt"
readonly MKCONFIG="$(detect_mkconfig)"
readonly SCRIPT_CHECK="$(detect_script_check)"
readonly SOURCE_CONFIG="${SOURCE_THEME}/config/${CONFIG_NAME}"
readonly SOURCE_BACKGROUND="${SOURCE_THEME}/backgrounds/${BACKGROUND_NAME}"
readonly SOURCE_CARDS="${SOURCE_THEME}/assets/cards-${DENSITY}"
readonly SOURCE_ICONS="${SOURCE_THEME}/assets/icons-${DENSITY}"

[[ -f /etc/default/grub ]] || die "Missing /etc/default/grub."
[[ -f "${SOURCE_CONFIG}" ]] || die "Missing ${SOURCE_CONFIG}."
[[ -f "${SOURCE_BACKGROUND}" ]] || die "Missing ${SOURCE_BACKGROUND}."
[[ -d "${SOURCE_CARDS}" ]] || die "Missing ${SOURCE_CARDS}."
[[ -d "${SOURCE_ICONS}" ]] || die "Missing ${SOURCE_ICONS}."
[[ -f "${SOURCE_THEME}/.grub-x-minimal-theme" ]] \
  || die "Theme payload marker is missing."
compgen -G "${SOURCE_THEME}/fonts/*.pf2" >/dev/null \
  || die "No PF2 fonts were found."

if [[ -d "${THEME_DEST}" && ! -f "${THEME_DEST}/.grub-x-minimal-theme" ]]; then
  die "${THEME_DEST} exists but is not owned by this project."
fi

printf '\nInstallation plan:\n'
printf '  Fedora firmware: %s\n' "${FIRMWARE}"
printf '  Screen profile:  %s (%s)\n' "${SCREEN}" "${GFXMODE}"
printf '  Back up:         /etc/default/grub\n'
printf '  Back up:         %s\n' "${GRUB_CFG}"
printf '  Install theme:   %s\n' "${THEME_DEST}"
printf '  Rebuild config:  %s\n' "${GRUB_CFG}"
printf '\nExplicitly unchanged:\n'
printf '  kernels, BLS, menu entries, default entry, timeout, os-prober,\n'
printf '  /boot/efi, EFI variables, Secure Boot, NVIDIA and kernel arguments\n\n'

confirm
"${BACKUP_SCRIPT}" --assume-confirmed --activate

install -d -m 0755 "${THEMES_ROOT}"
STAGING_DIR="$(mktemp -d "${THEMES_ROOT}/.${THEME_NAME}.XXXXXX")"
install -d -m 0755 \
  "${STAGING_DIR}/cards" \
  "${STAGING_DIR}/icons"

install -m 0644 "${SOURCE_CONFIG}" "${STAGING_DIR}/theme.txt"
install -m 0644 "${SOURCE_BACKGROUND}" "${STAGING_DIR}/background.png"
install -m 0644 "${SOURCE_THEME}/.grub-x-minimal-theme" \
  "${STAGING_DIR}/.grub-x-minimal-theme"
install -m 0644 "${SOURCE_THEME}"/fonts/*.pf2 "${STAGING_DIR}/"
install -m 0644 "${SOURCE_CARDS}"/*.png "${STAGING_DIR}/cards/"
install -m 0644 "${SOURCE_ICONS}"/*.png "${STAGING_DIR}/icons/"

if [[ -d "${THEME_DEST}" ]]; then
  safe_remove_tree "${THEME_DEST}"
fi
mv -- "${STAGING_DIR}" "${THEME_DEST}"
STAGING_DIR=""

if command -v restorecon >/dev/null 2>&1; then
  restorecon -R "${THEME_DEST}" >/dev/null \
    || warn "Could not refresh the SELinux context for ${THEME_DEST}."
fi

update_grub_setting "GRUB_THEME" "${THEME_FILE}"
update_grub_setting "GRUB_GFXMODE" "${GFXMODE}"
update_grub_setting "GRUB_TERMINAL_OUTPUT" "gfxterm"

TEMP_GRUB_CFG="$(mktemp "${GRUB_ROOT}/.grub.cfg.XXXXXX")"
info "Generating and checking a candidate GRUB configuration..."
"${MKCONFIG}" -o "${TEMP_GRUB_CFG}"
"${SCRIPT_CHECK}" "${TEMP_GRUB_CFG}"
grep -F -- "/${THEME_NAME}/theme.txt" "${TEMP_GRUB_CFG}" >/dev/null \
  || die "Generated configuration does not reference the installed theme."
grep -E -- 'minimal-sans-(24|32|48)\.pf2' "${TEMP_GRUB_CFG}" >/dev/null \
  || die "Generated configuration does not load the theme fonts."

chmod --reference="${GRUB_CFG}" "${TEMP_GRUB_CFG}"
chown --reference="${GRUB_CFG}" "${TEMP_GRUB_CFG}"
mv -- "${TEMP_GRUB_CFG}" "${GRUB_CFG}"
TEMP_GRUB_CFG=""
if command -v restorecon >/dev/null 2>&1; then
  restorecon "${GRUB_CFG}" >/dev/null \
    || warn "Could not refresh the SELinux context for ${GRUB_CFG}."
fi

ok "Minimal Focus was installed; the generated GRUB config passed syntax checking."
printf 'Uninstall: sudo %s\n' "${SCRIPT_DIR}/uninstall.sh"
if [[ -r "${ACTIVE_BACKUP_FILE}" ]]; then
  printf 'Original backup: %s\n' "$(head -n 1 "${ACTIVE_BACKUP_FILE}")"
fi
warn "No reboot was performed."
