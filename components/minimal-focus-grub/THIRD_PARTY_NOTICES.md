# Third-party notices

## vinceliuice/grub2-themes

Primary and sole GRUB theme engineering basis:

- Project: `vinceliuice/grub2-themes`
- URL: https://github.com/vinceliuice/grub2-themes
- Pinned revision: `80dd04ddf3ba7b284a7b1a5df2b1e95ee2aad606`
- License: GNU General Public License v3.0
- Copyright: upstream authors and contributors

The following portions are copied or modified from that revision:

- The five `theme.txt` profile structures and their percentage-based
  `boot_menu`, image, timeout, font, icon, and resolution relationships.
- Terminus 12/14/16/18 PF2 files.
- Unifont 16/24/32 PF2 files, including the upstream 4K font choice.
- The white 32/48/64 pixel OS/function icon sets, recolored to neutral gray
  while preserving filenames, dimensions, and alpha.
- The resource selection and screen-profile approach used by `install.sh`.

The derivative remains GPL-3.0. The complete license text is in `LICENSE`.

## Theme syntax research not incorporated as assets

The following projects were inspected to validate established GRUB2 syntax:

- `shvchk/fallout-grub-theme`: verified real-world use of
  `item_pixmap_style` for unselected item skins.
- GNU/Fedora GRUB Starfield: checked standard nine-slice and component syntax.
- `HenriqueLopes42/themeGrub.CyberEXS`: inspected only; its repository has no
  declared license, so no code, image, font, or icon was copied.
- `ftonneau/grub-evodevo`: studied its menu/countdown composition and
  antialiased-entry technique; the generated fake-entry mechanism was not
  copied because it is incompatible with dynamic Fedora kernel updates.
- `Coopydood/HyperFluent-GRUB-Theme`: studied its keyboard affordances and
  layout hierarchy.
- `shvchk/poly-dark`: studied its restrained focus treatment.

No Fallout, Starfield, CyberEXS, EvoDevo, HyperFluent, Poly Dark, Windows,
macOS, Nothing OS, or X/Twitter background or logo asset is included.

## DejaVu Sans

DejaVu Sans is used by `scripts/render-assets.sh` to render preview text and
the bundled `Minimal Sans` PF2 menu fonts.

The DejaVu license is included at `licenses/DEJAVU-LICENSE`.

## Programmatically rendered assets

The following assets are reproducibly rendered by
`scripts/render-assets.sh`:

- five dark radial-gradient backgrounds;
- the left-side surfaces of five backgrounds, combined with the original
  project-generated `visuals/dual-os-login-art.png` on the right;
- transparent resting-entry and light focus-surface nine-slices;
- scrollbar and timeout progress textures;
- four sizes of the DejaVu-based `Minimal Sans` PF2 font;
- the 1920x1080 preview image.

The right-side artwork is an AI-generated abstract login-style illustration
created for this component. It contains no real user account or copied
commercial UI screenshot. The other generated assets contain no photographic
wallpaper or copied commercial artwork.
