#!/usr/bin/env bash
#
# Package the theme into a disposable standalone x86_64 EFI image.
# This writes only below the project, never to /boot or /boot/efi.

set -euo pipefail
IFS=$'\n\t'

readonly TEST_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_DIR="$(cd -- "${TEST_DIR}/.." && pwd)"
readonly THEME_DIR="${PROJECT_DIR}/theme"

command -v grub2-mkstandalone >/dev/null 2>&1 \
  || { printf 'SKIP: grub2-mkstandalone is not installed.\n'; exit 0; }
command -v grub2-script-check >/dev/null 2>&1 \
  || { printf 'SKIP: grub2-script-check is not installed.\n'; exit 0; }
command -v grub2-file >/dev/null 2>&1 \
  || { printf 'SKIP: grub2-file is not installed.\n'; exit 0; }

[[ -f "${PROJECT_DIR}/LICENSE" && -f "${THEME_DIR}/.grub-x-minimal-theme" ]] \
  || { printf 'Refusing invalid project tree: %s\n' "${PROJECT_DIR}" >&2; exit 1; }

SANDBOX="$(mktemp -d "${PROJECT_DIR}/.standalone-test.XXXXXX")"
readonly SANDBOX
cleanup() {
  local exit_code=$?
  find "${SANDBOX}" -xdev -depth -delete
  return "${exit_code}"
}
trap cleanup EXIT

readonly PAYLOAD="${SANDBOX}/x-minimal"
readonly CONFIG="${SANDBOX}/grub.cfg"
readonly IMAGE="${SANDBOX}/x-minimal-test.efi"

install -d -m 0755 \
  "${PAYLOAD}/cards" \
  "${PAYLOAD}/icons"
install -m 0644 "${THEME_DIR}/theme.txt" "${PAYLOAD}/theme.txt"
install -m 0644 "${THEME_DIR}/background.png" "${PAYLOAD}/background.png"
install -m 0644 "${THEME_DIR}"/fonts/*.pf2 "${PAYLOAD}/"
install -m 0644 "${THEME_DIR}/cards/"*.png "${PAYLOAD}/cards/"
install -m 0644 "${THEME_DIR}/icons/"*.png "${PAYLOAD}/icons/"

cat > "${CONFIG}" <<'GRUB_CFG'
insmod all_video
insmod gfxterm
insmod gfxmenu
insmod png
insmod font

if loadfont /boot/grub/themes/x-minimal/minimal-sans-18.pf2; then
  loadfont /boot/grub/themes/x-minimal/minimal-sans-24.pf2
  loadfont /boot/grub/themes/x-minimal/terminus-18.pf2
fi

terminal_output gfxterm
set gfxmode=1920x1080x32,auto
set timeout=30
set default=0
set theme=/boot/grub/themes/x-minimal/theme.txt
export theme

menuentry "Fedora Linux" --class fedora --class gnu-linux {
  echo "Standalone visual test only"
}

menuentry "Windows Boot Manager" --class windows {
  echo "Standalone visual test only"
}

submenu "Advanced Options" --class submenu {
  menuentry "Fedora Linux (recovery test entry)" --class recovery {
    echo "Standalone visual test only"
  }
}
GRUB_CFG

grub2-script-check "${CONFIG}"

grub2-mkstandalone \
  --format=x86_64-efi \
  --output="${IMAGE}" \
  --compress=xz \
  --fonts="" \
  --locales="" \
  --themes="" \
  --install-modules="normal configfile all_video gfxterm gfxmenu png font echo" \
  --modules="all_video gfxterm gfxmenu png font" \
  "/boot/grub/grub.cfg=${CONFIG}" \
  "/boot/grub/themes/x-minimal=${PAYLOAD}"

grub2-file --is-x86_64-efi "${IMAGE}"
file_output="$(file --brief "${IMAGE}")"
if [[ "${file_output}" != *"EFI"* || "${file_output}" != *"application"* ]]; then
  printf 'Unexpected standalone image type: %s\n' "${file_output}" >&2
  exit 1
fi

printf 'PASS: standalone GRUB EFI packaged successfully (%s bytes); temporary image removed.\n' \
  "$(stat -c '%s' "${IMAGE}")"
