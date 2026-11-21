#!/usr/bin/env bash
set -euo pipefail

ff_project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ff_tool_root="$ff_project_root/.test-tmp/flowfoundry-desktop-toolchain"

if [[ -x "$ff_tool_root/cargo/bin/cargo" ]]; then
  export RUSTUP_HOME="$ff_tool_root/rustup"
  export CARGO_HOME="$ff_tool_root/cargo"
  export PATH="$ff_tool_root/cargo/bin:$PATH"
fi

if ! command -v cargo >/dev/null 2>&1; then
  echo 'Rust/Cargo is missing. See docs/linux-iphone-setup.md.' >&2
  exit 1
fi

export CARGO_TARGET_DIR="$ff_tool_root/target"
export CC=/usr/bin/gcc
export CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_LINKER=/usr/bin/gcc

cd "$ff_project_root/applications/flowfoundry-desktop/src-tauri"
cargo fmt --check
cargo check --locked
