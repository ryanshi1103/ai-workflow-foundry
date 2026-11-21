#!/usr/bin/env bash
#
# Reproducibly render the non-photographic Minimal GRUB PNG payload.
# OS icons and PF2 fonts remain derived from vinceliuice/grub2-themes.

set -euo pipefail
IFS=$'\n\t'

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
readonly THEME_DIR="${PROJECT_DIR}/theme"
readonly ASSET_DIR="${THEME_DIR}/assets"
readonly BACKGROUND_DIR="${THEME_DIR}/backgrounds"
readonly FONT_DIR="${THEME_DIR}/fonts"
readonly PREVIEW_DIR="${PROJECT_DIR}/preview"
readonly LOGIN_ART="${PROJECT_DIR}/visuals/dual-os-login-art.png"
readonly DEJAVU_FONT="/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf"

if command -v magick >/dev/null 2>&1; then
  readonly IM="magick"
elif command -v convert >/dev/null 2>&1; then
  readonly IM="convert"
else
  printf 'ImageMagick is required to render the theme assets.\n' >&2
  exit 1
fi

command -v grub2-mkfont >/dev/null 2>&1 \
  || { printf 'grub2-mkfont is required to render the theme fonts.\n' >&2; exit 1; }
[[ -f "${DEJAVU_FONT}" ]] \
  || { printf 'DejaVu Sans is required to render the theme fonts.\n' >&2; exit 1; }

[[ -f "${PROJECT_DIR}/LICENSE" && -f "${THEME_DIR}/.grub-x-minimal-theme" ]] \
  || { printf 'Refusing to render from an invalid project tree: %s\n' "${PROJECT_DIR}" >&2; exit 1; }

render_background() {
  local name="$1"
  local size="$2"
  local width="${size%x*}"
  local height="${size#*x}"
  local panel_left=$((width * 6 / 100))
  local panel_top=$((height * 8 / 100))
  local panel_right=$((width * 52 / 100))
  local panel_bottom=$((height * 92 / 100))
  local panel_radius=$((height / 48))
  local orbit_x=$((width * 81 / 100))
  local orbit_y=$((height * 43 / 100))
  local orbit_inner=$((height * 24 / 100))
  local orbit_middle=$((height * 34 / 100))
  local orbit_outer=$((height * 45 / 100))
  local blue_x=$((width * 84 / 100))
  local blue_y=$((height * 27 / 100))
  local blue_radius=$((height * 25 / 100))
  local violet_x=$((width * 70 / 100))
  local violet_y=$((height * 72 / 100))
  local violet_radius=$((height * 18 / 100))
  local glow_blur=$((height / 10))
  local accent_left=$((width * 10 / 100))
  local accent_top=$((height * 14 / 100))
  local accent_right=$((width * 13 / 100))
  local accent_height=$((height / 270))
  local art_width=$((width * 47 / 100))
  local art_crop="${RENDER_TMP}/login-art-${name}.png"

  # A restrained editorial composition: one quiet glass surface anchors the
  # functional UI while soft light and orbital hairlines give the empty side
  # depth. The right-side artwork is composited separately so the menu and
  # selected item remain live GRUB components.
  "${IM}" -size "${size}" xc:'#070a12' \
    \( -size "${size}" xc:none \
      -fill 'rgba(29,78,216,0.34)' -stroke none \
      -draw "circle ${blue_x},${blue_y} $((blue_x + blue_radius)),${blue_y}" \
      -blur "0x${glow_blur}" \) \
    -compose over -composite \
    \( -size "${size}" xc:none \
      -fill 'rgba(109,40,217,0.18)' -stroke none \
      -draw "circle ${violet_x},${violet_y} $((violet_x + violet_radius)),${violet_y}" \
      -blur "0x${glow_blur}" \) \
    -compose over -composite \
    -fill none -strokewidth 1 \
    -stroke 'rgba(147,197,253,0.12)' \
    -draw "ellipse ${orbit_x},${orbit_y} ${orbit_inner},${orbit_inner} 0,360" \
    -stroke 'rgba(147,197,253,0.075)' \
    -draw "ellipse ${orbit_x},${orbit_y} ${orbit_middle},${orbit_middle} 0,360" \
    -stroke 'rgba(196,181,253,0.055)' \
    -draw "ellipse ${orbit_x},${orbit_y} ${orbit_outer},${orbit_outer} 0,360" \
    -fill 'rgba(8,13,24,0.82)' -stroke 'rgba(148,163,184,0.14)' \
    -draw "roundrectangle ${panel_left},${panel_top} ${panel_right},${panel_bottom} ${panel_radius},${panel_radius}" \
    -fill 'rgba(125,211,252,0.92)' -stroke none \
    -draw "roundrectangle ${accent_left},${accent_top} ${accent_right},$((accent_top + accent_height)) $((accent_height / 2)),$((accent_height / 2))" \
    -colorspace sRGB -depth 8 -strip \
    "${BACKGROUND_DIR}/background-${name}.png"

  "${IM}" "${LOGIN_ART}" -resize "x${height}" \
    -gravity east -crop "${art_width}x${height}+0+0" +repage \
    -depth 8 -strip "${art_crop}"
  "${IM}" "${BACKGROUND_DIR}/background-${name}.png" "${art_crop}" \
    -gravity east -compose over -composite -depth 8 -strip \
    "${BACKGROUND_DIR}/background-${name}.png"
}

split_card() {
  local prefix="$1"
  local width="$2"
  local height="$3"
  local radius="$4"
  local slice="$5"
  local fill="$6"
  local stroke="$7"
  local output_dir="$8"
  local temp_card="${RENDER_TMP}/${prefix}-${height}.png"
  local temp_surface="${RENDER_TMP}/${prefix}-${height}-surface.png"
  local temp_shadow="${RENDER_TMP}/${prefix}-${height}-shadow.png"
  local middle_width=$((width - (slice * 2)))
  local middle_height=$((height - (slice * 2)))

  if [[ "${prefix}" == "selected" ]]; then
    # Reserve a few pixels for a soft shadow. A narrow cyan rail identifies
    # focus without turning the entire row into a loud primary-color button.
    "${IM}" -size "${width}x${height}" xc:none \
      -fill 'rgba(14,116,144,0.34)' -stroke none \
      -draw "roundrectangle 5,5 $((width - 6)),$((height - 4)) ${radius},${radius}" \
      -blur 0x5 -depth 8 "${temp_shadow}"
    "${IM}" -size "${width}x${height}" xc:none \
      -fill "${fill}" -stroke "${stroke}" -strokewidth 1 \
      -draw "roundrectangle 2,1 $((width - 3)),$((height - 6)) ${radius},${radius}" \
      -fill 'rgba(125,211,252,0.98)' -stroke none \
      -draw "roundrectangle 2,$((slice - 2)) 6,$((height - slice - 4)) 2,2" \
      -depth 8 "${temp_surface}"
    "${IM}" "${temp_shadow}" "${temp_surface}" \
      -compose over -composite -strip "${temp_card}"
  else
    "${IM}" -size "${width}x${height}" xc:none \
      -fill "${fill}" -stroke "${stroke}" -strokewidth 1 \
      -draw "roundrectangle 1,1 $((width - 2)),$((height - 2)) ${radius},${radius}" \
      -depth 8 -strip "${temp_card}"
  fi

  "${IM}" "${temp_card}" -crop "${slice}x${slice}+0+0" +repage \
    "${output_dir}/${prefix}_nw.png"
  "${IM}" "${temp_card}" -crop "${middle_width}x${slice}+${slice}+0" +repage \
    "${output_dir}/${prefix}_n.png"
  "${IM}" "${temp_card}" -crop "${slice}x${slice}+$((width - slice))+0" +repage \
    "${output_dir}/${prefix}_ne.png"
  "${IM}" "${temp_card}" -crop "${slice}x${middle_height}+0+${slice}" +repage \
    "${output_dir}/${prefix}_w.png"
  "${IM}" "${temp_card}" -crop "${middle_width}x${middle_height}+${slice}+${slice}" +repage \
    "${output_dir}/${prefix}_c.png"
  "${IM}" "${temp_card}" -crop "${slice}x${middle_height}+$((width - slice))+${slice}" +repage \
    "${output_dir}/${prefix}_e.png"
  "${IM}" "${temp_card}" -crop "${slice}x${slice}+0+$((height - slice))" +repage \
    "${output_dir}/${prefix}_sw.png"
  "${IM}" "${temp_card}" -crop "${middle_width}x${slice}+${slice}+$((height - slice))" +repage \
    "${output_dir}/${prefix}_s.png"
  "${IM}" "${temp_card}" -crop "${slice}x${slice}+$((width - slice))+$((height - slice))" +repage \
    "${output_dir}/${prefix}_se.png"
}

render_cards() {
  local density="$1"
  local width="$2"
  local height="$3"
  local radius="$4"
  local slice="$5"
  local scrollbar_width="$6"
  local progress_height="$7"
  local progress_line="$8"
  local output_dir="${ASSET_DIR}/cards-${density}"

  install -d -m 0755 "${output_dir}"
  find "${output_dir}" -maxdepth 1 -type f -name '*.png' -delete

  # Resting entries form one quiet rhythm. Focus adds depth and a slim accent
  # rather than replacing the whole row with a bright blue slab.
  split_card item "${width}" "${height}" "${radius}" "${slice}" \
    'rgba(255,255,255,0.025)' 'rgba(148,163,184,0.10)' "${output_dir}"
  split_card selected "${width}" "${height}" "${radius}" "${slice}" \
    'rgba(24,35,56,0.98)' 'rgba(125,211,252,0.44)' "${output_dir}"

  "${IM}" -size "${scrollbar_width}x$((height / 2))" xc:none \
    -fill 'rgba(125,211,252,0.62)' \
    -draw "roundrectangle 0,0 $((scrollbar_width - 1)),$((height / 2 - 1)) $((scrollbar_width / 2)),$((scrollbar_width / 2))" \
    -depth 8 -strip "${output_dir}/scrollbar_c.png"

  # GRUB advances the cyan segment as the automatic boot deadline approaches.
  local progress_width=$((progress_line * 2))
  for part in c w e; do
    "${IM}" -size "${progress_width}x${progress_height}" xc:none \
      -fill 'rgba(148,163,184,0.18)' -stroke none \
      -draw "rectangle 0,$((progress_height - progress_line)) $((progress_width - 1)),$((progress_height - 1))" \
      -depth 8 -strip "${output_dir}/progress_bar_${part}.png"
  done
  "${IM}" -size "${progress_width}x${progress_height}" xc:none \
    -fill 'rgba(125,211,252,0.98)' -stroke none \
    -draw "rectangle 0,$((progress_height - progress_line)) $((progress_width - 1)),$((progress_height - 1))" \
    -depth 8 -strip "${output_dir}/progress_highlight_c.png"
}

render_font() {
  local size="$1"

  grub2-mkfont \
    -n "Minimal Sans" \
    -s "${size}" \
    -r 0x20-0x7e \
    -o "${FONT_DIR}/minimal-sans-${size}.pf2" \
    "${DEJAVU_FONT}"
}

render_preview() {
  local canvas="${RENDER_TMP}/preview-canvas.png"
  local selected="${RENDER_TMP}/preview-selected.png"
  local item="${RENDER_TMP}/preview-item.png"
  local shadow="${RENDER_TMP}/preview-shadow.png"

  "${IM}" -size 768x68 xc:none \
    -fill 'rgba(14,116,144,0.34)' -stroke none \
    -draw 'roundrectangle 10,7 758,64 12,12' -blur 0x8 "${shadow}"
  "${IM}" -size 768x68 xc:none \
    -fill 'rgba(24,35,56,0.98)' -stroke 'rgba(125,211,252,0.44)' -strokewidth 1 \
    -draw 'roundrectangle 2,1 765,62 12,12' \
    -fill 'rgba(125,211,252,0.98)' -stroke none \
    -draw 'roundrectangle 2,12 6,48 2,2' "${selected}"
  "${IM}" -size 768x68 xc:none \
    -fill 'rgba(255,255,255,0.025)' -stroke 'rgba(148,163,184,0.10)' -strokewidth 1 \
    -draw 'roundrectangle 2,1 765,66 12,12' "${item}"

  "${IM}" "${BACKGROUND_DIR}/background-1080p.png" \
    "${shadow}" -geometry +202+358 -composite \
    "${selected}" -geometry +202+358 -composite \
    "${item}" -geometry +202+436 -composite \
    "${item}" -geometry +202+514 -composite \
    -font DejaVu-Sans -pointsize 15 -fill '#7f91aa' -kerning 2 \
    -gravity northwest -annotate +202+158 'MINIMAL FOCUS  /  BOOT MANAGER' \
    -font DejaVu-Sans -pointsize 46 -fill '#f5f8fc' -kerning -1 \
    -annotate +202+214 'Choose a system' \
    -font DejaVu-Sans -pointsize 17 -fill '#8fa1b9' -kerning 0 \
    -annotate +202+271 'Select where you want to continue' \
    -font DejaVu-Sans -pointsize 23 \
    -fill '#f8fbff' -annotate +294+379 'Fedora Linux' \
    -fill '#c3cedd' \
    -annotate +294+457 'Windows Boot Manager' \
    -annotate +294+535 'Advanced Options' \
    -font DejaVu-Sans -pointsize 16 -fill '#9aaac0' \
    -annotate +202+792 'AUTO BOOT  /  8 SECONDS' \
    -font DejaVu-Sans -pointsize 14 -fill '#718198' -kerning 1 \
    -annotate +202+944 'UP / DOWN   NAVIGATE        ENTER   BOOT        E   EDIT' \
    -gravity northwest -stroke none \
    -fill 'rgba(148,163,184,0.18)' -draw 'rectangle 202,817 969,819' \
    -fill 'rgba(125,211,252,0.98)' -draw 'rectangle 202,817 739,819' \
    -depth 8 -strip "${canvas}"

  if [[ -f "${ASSET_DIR}/icons-1080p/fedora.png" ]]; then
    "${IM}" "${canvas}" \
      "${ASSET_DIR}/icons-1080p/fedora.png" -geometry 28x28+238+378 -composite \
      "${ASSET_DIR}/icons-1080p/windows.png" -geometry 28x28+238+456 -composite \
      "${ASSET_DIR}/icons-1080p/submenu.png" -geometry 28x28+238+534 -composite \
      -depth 8 -strip "${PREVIEW_DIR}/minimal-focus-1080p.png"
  else
    cp -- "${canvas}" "${PREVIEW_DIR}/minimal-focus-1080p.png"
  fi
}

install -d -m 0755 "${ASSET_DIR}" "${BACKGROUND_DIR}" "${FONT_DIR}" "${PREVIEW_DIR}"
RENDER_TMP="$(mktemp -d "${ASSET_DIR}/.render.XXXXXX")"
readonly RENDER_TMP
trap 'find "${RENDER_TMP}" -xdev -depth -delete' EXIT

render_background 1080p 1920x1080
render_background 2k 2560x1440
render_background 4k 3840x2160
render_background ultrawide 2560x1080
render_background ultrawide2k 3440x1440

render_cards 1080p 320 68 12 14 4 32 3
render_cards 2k 420 92 16 18 6 44 4
render_cards 4k 600 136 24 26 8 62 6

render_font 18
render_font 24
render_font 32
render_font 48
render_font 64
render_font 96

render_preview

# Keep the source tree directly usable as a default 1080p theme.
cp -- "${BACKGROUND_DIR}/background-1080p.png" "${THEME_DIR}/background.png"
cp -- "${THEME_DIR}/config/theme-1080p.txt" "${THEME_DIR}/theme.txt"
find "${THEME_DIR}/cards" -maxdepth 1 -type f -name '*.png' -delete
find "${THEME_DIR}/icons" -maxdepth 1 -type f -name '*.png' -delete
cp -- "${ASSET_DIR}/cards-1080p/"*.png "${THEME_DIR}/cards/"
if compgen -G "${ASSET_DIR}/icons-1080p/*.png" >/dev/null; then
  cp -- "${ASSET_DIR}/icons-1080p/"*.png "${THEME_DIR}/icons/"
fi

printf 'Rendered Minimal GRUB assets and preview.\n'
