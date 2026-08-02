#!/bin/bash
# Make this Fedora computer a Tailscale exit node for mobile devices.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SYSCTL_SOURCE="$PROJECT_ROOT/config/sysctl/99-cc-mobile-exit-node.conf"
SYSCTL_TARGET="/etc/sysctl.d/99-cc-mobile-exit-node.conf"
TAILSCALE_FIREWALL_ZONE="tailscale-ssh"
MIHOMO_FIREWALL_ZONE="mihomo-tun"
EXIT_POLICY="tailscale-to-mihomo"
ASSUME_YES=false
DISABLE=false

usage() {
    cat <<'USAGE'
用法:
  ./scripts/setup-mobile-exit-node.sh [--yes]
  ./scripts/setup-mobile-exit-node.sh --disable [--yes]

启用后，手机可以只连接 Tailscale，同时访问电脑并经本机访问互联网。
--disable 撤销出口节点发布；不会修改 Clash/Mihomo 配置。
USAGE
}

while (( $# > 0 )); do
    case "$1" in
        --yes)
            ASSUME_YES=true
            ;;
        --disable)
            DISABLE=true
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "错误: 未知参数: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
    shift
done

if [[ "${EUID}" -eq 0 ]]; then
    echo "错误: 请以普通桌面用户运行；脚本会按需调用 sudo。" >&2
    exit 1
fi

if ! command -v tailscale >/dev/null 2>&1; then
    echo "错误: 未安装 Tailscale。请先运行 setup-mobile-remote.sh。" >&2
    exit 1
fi

if [[ "$DISABLE" == true ]]; then
    echo "即将停止发布本机 Tailscale 出口节点。"
    if [[ "$ASSUME_YES" != true ]]; then
        read -r -p "请输入 'yes' 继续: " confirm
        [[ "$confirm" == "yes" ]] || { echo "已取消。"; exit 1; }
    fi

    sudo -v
    sudo tailscale set --advertise-exit-node=false
    if command -v firewall-cmd >/dev/null 2>&1; then
        if sudo firewall-cmd --permanent --get-policies | tr ' ' '\n' | grep -qx "$EXIT_POLICY"; then
            sudo firewall-cmd --permanent --delete-policy="$EXIT_POLICY"
        fi
        if sudo firewall-cmd --permanent --get-zones | tr ' ' '\n' | grep -qx "$MIHOMO_FIREWALL_ZONE"; then
            sudo firewall-cmd --permanent --delete-zone="$MIHOMO_FIREWALL_ZONE"
        fi
        sudo firewall-cmd --reload
    fi
    echo "已停止发布出口节点。手机将不再能选择本机作为互联网出口。"
    exit 0
fi

if [[ ! -r "$SYSCTL_SOURCE" ]]; then
    echo "错误: 缺少转发配置源文件: $SYSCTL_SOURCE" >&2
    exit 1
fi

echo "即将执行："
echo "  1. 持久启用 IPv4/IPv6 转发"
echo "  2. 将本机发布为 Tailscale 出口节点"
echo "  3. 保留当前 SSH、防火墙和 Clash/Mihomo 配置"
echo ""
echo "手机选中本机作为出口节点后，互联网流量会经过这台电脑。"

if [[ "$ASSUME_YES" != true ]]; then
    read -r -p "请输入 'yes' 继续: " confirm
    [[ "$confirm" == "yes" ]] || { echo "已取消。"; exit 1; }
fi

sudo -v
sudo install -D -m 0644 "$SYSCTL_SOURCE" "$SYSCTL_TARGET"
sudo sysctl -p "$SYSCTL_TARGET"

# Fedora firewalld blocks forwarding between zones by default.  When Clash
# Verge runs in TUN mode, policy routing sends exit-node packets from
# tailscale0 to the Mihomo interface, so permit exactly that one direction.
if command -v firewall-cmd >/dev/null 2>&1 && ip link show Mihomo >/dev/null 2>&1; then
    if ! sudo firewall-cmd --permanent --get-zones | tr ' ' '\n' | grep -qx "$MIHOMO_FIREWALL_ZONE"; then
        sudo firewall-cmd --permanent --new-zone="$MIHOMO_FIREWALL_ZONE"
    fi
    sudo firewall-cmd --permanent --zone="$MIHOMO_FIREWALL_ZONE" --add-interface=Mihomo

    if ! sudo firewall-cmd --permanent --get-policies | tr ' ' '\n' | grep -qx "$EXIT_POLICY"; then
        sudo firewall-cmd --permanent --new-policy="$EXIT_POLICY"
    fi
    sudo firewall-cmd --permanent --policy="$EXIT_POLICY" --add-ingress-zone="$TAILSCALE_FIREWALL_ZONE"
    sudo firewall-cmd --permanent --policy="$EXIT_POLICY" --add-egress-zone="$MIHOMO_FIREWALL_ZONE"
    sudo firewall-cmd --permanent --policy="$EXIT_POLICY" --set-target=ACCEPT
    sudo firewall-cmd --reload
fi

sudo tailscale set --advertise-exit-node

echo ""
if ip link show Mihomo >/dev/null 2>&1; then
    echo "✓ 检测到 Mihomo TUN 接口。"
    if firewall-cmd --policy="$EXIT_POLICY" --query-ingress-zone="$TAILSCALE_FIREWALL_ZONE" 2>/dev/null | grep -qx yes \
        && firewall-cmd --policy="$EXIT_POLICY" --query-egress-zone="$MIHOMO_FIREWALL_ZONE" 2>/dev/null | grep -qx yes; then
        echo "✓ firewalld 已允许 Tailscale → Mihomo 转发。"
    else
        echo "! 未确认 Tailscale → Mihomo 转发策略。"
    fi
else
    echo "! 未检测到 Mihomo TUN；手机仍可联网，但可能不会走 Clash 代理。"
fi

if tailscale debug prefs 2>/dev/null | grep -Fq '0.0.0.0/0'; then
    echo "✓ Tailscale 已发布 IPv4 出口路由。"
else
    echo "! 未能从本机首选项确认出口路由，请检查 tailscale status。"
fi

echo ""
echo "电脑端完成。接下来："
echo "  1. 如 Tailscale 管理后台要求，请批准本机的出口节点路由。"
echo "  2. 手机 Tailscale → Exit node/出口节点 → 选择本机。"
echo "  3. 保持“允许访问本地网络”关闭，除非确实需要访问手机所在局域网。"
echo "  4. 验证手机既能打开境外网站，也能一键进入 cc。"
echo ""
echo "撤销命令: ./scripts/setup-mobile-exit-node.sh --disable"
