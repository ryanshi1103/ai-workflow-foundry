#!/bin/bash
# Install and enable OpenSSH over Tailscale for mobile access to cc on Fedora.
# Run as the regular desktop user; this script invokes sudo only for the
# package, service, and Tailscale system operations that require it.

set -euo pipefail

TAILSCALE_REPO_URL="https://pkgs.tailscale.com/stable/fedora/tailscale.repo"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SSHD_CONFIG_SOURCE="$PROJECT_ROOT/config/sshd/60-cc-mobile.conf"
SSHD_CONFIG_TARGET="/etc/ssh/sshd_config.d/60-cc-mobile.conf"
TAILSCALE_FIREWALL_ZONE="tailscale-ssh"

if [[ ! -r /etc/os-release ]]; then
    echo "错误: 无法识别当前系统。" >&2
    exit 1
fi

# shellcheck disable=SC1091
source /etc/os-release
if [[ "${ID:-}" != "fedora" ]]; then
    echo "错误: 当前脚本只支持 Fedora；检测到 ${ID:-unknown}。" >&2
    exit 1
fi

if [[ "${EUID}" -eq 0 ]]; then
    echo "错误: 请以普通桌面用户运行，不要直接 sudo 整个脚本。" >&2
    exit 1
fi

echo "即将执行："
echo "  1. 从 Tailscale 官方 Fedora 仓库安装 tailscale"
echo "  2. 启用 tailscaled systemd 服务"
echo "  3. 启用 Fedora OpenSSH，并仅在 tailscale0 防火墙区域开放 SSH"
echo ""
echo "不会执行："
echo "  - 不关闭或放宽 SELinux"
echo "  - 不开放公网 22 端口"
echo "  - 不修改路由器端口转发"
echo "  - 不读取或复制 AI/API 凭据"
echo ""

confirm=""
read -r -p "请输入 'yes' 继续: " confirm
if [[ "$confirm" != "yes" ]]; then
    echo "已取消。"
    exit 1
fi

# Authenticate sudo before changing package or service state.
sudo -v

if [[ ! -r "$SSHD_CONFIG_SOURCE" ]]; then
    echo "错误: 缺少 SSH 配置源文件: $SSHD_CONFIG_SOURCE" >&2
    exit 1
fi

if ! command -v tailscale >/dev/null 2>&1; then
    if dnf --version 2>/dev/null | head -n 1 | grep -q '^dnf5'; then
        sudo dnf config-manager addrepo \
            --from-repofile="$TAILSCALE_REPO_URL"
    else
        sudo dnf config-manager --add-repo "$TAILSCALE_REPO_URL"
    fi
    sudo dnf install -y tailscale openssh-server firewalld
else
    echo "Tailscale 已安装，跳过软件包安装。"
    sudo dnf install -y openssh-server firewalld
fi

sudo systemctl enable --now tailscaled

echo ""
echo "接下来会显示 Tailscale 登录链接。"
echo "请在手机浏览器打开链接，并使用准备绑定手机的同一账号登录。"
echo ""
sudo tailscale up

# Tailscale's built-in SSH can conflict with enforcing SELinux. Use Fedora's
# SELinux-aware OpenSSH server over the encrypted tailnet instead.
sudo tailscale set --ssh=false

sudo install -D -m 0644 "$SSHD_CONFIG_SOURCE" "$SSHD_CONFIG_TARGET"
sudo ssh-keygen -A
sudo sshd -t

sudo systemctl enable --now firewalld
if ! sudo firewall-cmd --permanent --get-zones | tr ' ' '\n' | grep -qx "$TAILSCALE_FIREWALL_ZONE"; then
    sudo firewall-cmd --permanent --new-zone="$TAILSCALE_FIREWALL_ZONE"
fi
sudo firewall-cmd --permanent --zone="$TAILSCALE_FIREWALL_ZONE" --add-interface=tailscale0
sudo firewall-cmd --permanent --zone="$TAILSCALE_FIREWALL_ZONE" --add-service=ssh

# Fedora Workstation permits SSH in its default zone even when sshd is initially
# disabled. Remove that permission before enabling sshd so port 22 is reachable
# through tailscale0 only, not through Wi-Fi or Ethernet.
while IFS= read -r active_zone; do
    [[ -z "$active_zone" || "$active_zone" == "$TAILSCALE_FIREWALL_ZONE" ]] && continue
    sudo firewall-cmd --permanent --zone="$active_zone" --remove-service=ssh >/dev/null
done < <(sudo firewall-cmd --get-active-zones | awk '/^[^[:space:]]/ {print $1}')
sudo firewall-cmd --reload

sudo systemctl enable --now sshd

echo ""
echo "Tailscale 状态："
tailscale status
echo ""
echo "本机 Tailscale 地址："
tailscale ip -4
echo ""

echo "OpenSSH 状态："
systemctl is-active sshd
echo "防火墙区域："
sudo firewall-cmd --zone="$TAILSCALE_FIREWALL_ZONE" --list-all

echo ""
echo "电脑端配置完成。手机端："
echo "  1. 安装并登录 Tailscale，使用与电脑相同的 tailnet。"
echo "  2. 安装 Termux 或 ConnectBot。"
echo "  3. 连接: ssh ${USER}@<本机-MagicDNS-名称>"
echo "  4. 运行: tmux new-session -A -s cc-mobile"
echo "  5. 运行: ~/.local/bin/cc"
