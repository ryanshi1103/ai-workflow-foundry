#!/usr/bin/env bash

set -euo pipefail
IFS=$'\n\t'

readonly TEST_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_DIR="$(cd -- "${TEST_DIR}/.." && pwd)"
readonly THEME_DIR="${PROJECT_DIR}/theme"
[[ -s "${PROJECT_DIR}/visuals/dual-os-login-art.png" ]] \
  || { printf 'FAIL: missing dual-system source artwork\n' >&2; exit 1; }
SANDBOX=""

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

cleanup() {
  if [[ -n "${SANDBOX}" && -e "${SANDBOX}" ]]; then
    find "${SANDBOX}" -xdev -depth -delete
  fi
}
trap cleanup EXIT

for script in "${PROJECT_DIR}"/scripts/*.sh; do
  bash -n "${script}"
done

if command -v shellcheck >/dev/null 2>&1; then
  shellcheck "${PROJECT_DIR}"/scripts/*.sh
else
  printf 'SKIP: shellcheck is not installed.\n'
fi

for profile in 1080p 2k 4k ultrawide ultrawide2k; do
  [[ -s "${THEME_DIR}/config/theme-${profile}.txt" ]] \
    || fail "missing theme config: ${profile}"
  [[ -s "${THEME_DIR}/backgrounds/background-${profile}.png" ]] \
    || fail "missing background: ${profile}"
done

for density in 1080p 2k 4k; do
  for kind in item selected; do
    for part in nw n ne w c e sw s se; do
      [[ -s "${THEME_DIR}/assets/cards-${density}/${kind}_${part}.png" ]] \
        || fail "missing ${density} ${kind}_${part}.png"
    done
  done
  [[ "$(find "${THEME_DIR}/assets/icons-${density}" -maxdepth 1 -type f -name '*.png' | wc -l)" -ge 70 ]] \
    || fail "incomplete icon tier: ${density}"
  for progress in progress_bar_c progress_bar_w progress_bar_e progress_highlight_c; do
    [[ -s "${THEME_DIR}/assets/cards-${density}/${progress}.png" ]] \
      || fail "missing ${density} ${progress}.png"
  done
done

for font in \
  terminus-12.pf2 terminus-14.pf2 terminus-16.pf2 terminus-18.pf2 \
  unifont-16.pf2 unifont-24.pf2 unifont-32.pf2; do
  [[ -s "${THEME_DIR}/fonts/${font}" ]] || fail "missing font: ${font}"
done
for size in 18 24 32 48 64 96; do
  [[ -s "${THEME_DIR}/fonts/minimal-sans-${size}.pf2" ]] \
    || fail "missing Minimal Sans ${size} font"
done

for config in "${THEME_DIR}"/config/*.txt "${THEME_DIR}/theme.txt"; do
  grep -F 'item_pixmap_style = "cards/item_*.png"' "${config}" >/dev/null \
    || fail "unselected card style missing in ${config}"
  grep -F 'selected_item_pixmap_style = "cards/selected_*.png"' "${config}" >/dev/null \
    || fail "selected card style missing in ${config}"
  grep -F 'selected_item_color = "#f8fbff"' "${config}" >/dev/null \
    || fail "selected high-contrast text missing in ${config}"
  grep -F 'text = "MINIMAL FOCUS  /  BOOT MANAGER"' "${config}" >/dev/null \
    || fail "editorial header missing in ${config}"
  grep -F '+ progress_bar {' "${config}" >/dev/null \
    || fail "timeout progress is missing in ${config}"
  if grep -F 'branding/' "${config}" >/dev/null; then
    fail "obsolete branding reference found in ${config}"
  fi
done

if find "${THEME_DIR}" -type f -path '*/branding/*' -print -quit | grep -q .; then
  fail "obsolete branding asset remains in the theme"
fi

identify "${THEME_DIR}/backgrounds/background-1080p.png" \
  | grep -F '1920x1080' >/dev/null || fail "1080p background dimensions"
identify "${THEME_DIR}/backgrounds/background-2k.png" \
  | grep -F '2560x1440' >/dev/null || fail "2k background dimensions"
identify "${THEME_DIR}/backgrounds/background-4k.png" \
  | grep -F '3840x2160' >/dev/null || fail "4k background dimensions"
identify "${THEME_DIR}/backgrounds/background-ultrawide.png" \
  | grep -F '2560x1080' >/dev/null || fail "ultrawide background dimensions"
identify "${THEME_DIR}/backgrounds/background-ultrawide2k.png" \
  | grep -F '3440x1440' >/dev/null || fail "ultrawide2k background dimensions"

identify -format '%[channels]' \
  "${THEME_DIR}/assets/cards-1080p/item_c.png" \
  | grep -qi 'a' || fail "unselected card lacks alpha"

[[ -s "${PROJECT_DIR}/preview/minimal-focus-1080p.png" ]] \
  || fail "preview is missing"

# Exercise the installer's profile-to-payload contract entirely inside the
# project. This intentionally never mounts or writes a real /boot directory.
SANDBOX="$(mktemp -d "${PROJECT_DIR}/.install-sandbox.XXXXXX")"
for mapping in \
  '1080p:1080p:background-1080p.png' \
  '2k:2k:background-2k.png' \
  '4k:4k:background-4k.png' \
  'ultrawide:1080p:background-ultrawide.png' \
  'ultrawide2k:2k:background-ultrawide2k.png'; do
  IFS=: read -r profile density background <<< "${mapping}"
  destination="${SANDBOX}/${profile}"
  install -d "${destination}/cards" "${destination}/icons"
  install -m 0644 "${THEME_DIR}/config/theme-${profile}.txt" "${destination}/theme.txt"
  install -m 0644 "${THEME_DIR}/backgrounds/${background}" "${destination}/background.png"
  install -m 0644 "${THEME_DIR}"/fonts/*.pf2 "${destination}/"
  install -m 0644 "${THEME_DIR}/assets/cards-${density}/"*.png "${destination}/cards/"
  install -m 0644 "${THEME_DIR}/assets/icons-${density}/"*.png "${destination}/icons/"
  [[ -s "${destination}/theme.txt" && -s "${destination}/background.png" ]] \
    || fail "profile payload staging failed: ${profile}"
  [[ "$(find "${destination}/icons" -maxdepth 1 -type f -name '*.png' | wc -l)" -ge 70 ]] \
    || fail "profile icon staging failed: ${profile}"
done

"${PROJECT_DIR}/scripts/install.sh" --help >/dev/null
if "${PROJECT_DIR}/scripts/install.sh" --screen invalid-profile >/dev/null 2>&1; then
  fail "installer accepted an invalid screen profile"
fi

# The delivered scripts may describe forbidden areas in comments/output, but
# must not invoke mutation tools or use an EFI path as a write destination.
if rg -n '(^|[;&|[:space:]])(grub2-install|grub-install|efibootmgr|mokutil|grubby)([;&|[:space:]]|$)' \
  "${PROJECT_DIR}"/scripts/*.sh | rg -v 'printf|#|never|Never'; then
  fail "forbidden boot mutation command found"
fi

if rg -n '(cp|mv|install|rm|unlink|find|mktemp)[^\n]*/boot/efi' \
  "${PROJECT_DIR}"/scripts/*.sh; then
  fail "write operation targeting /boot/efi found"
fi

printf 'PASS: Minimal Focus project validation completed.\n'
