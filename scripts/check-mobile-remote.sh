#!/bin/bash
# Read-only health check for the Tailscale -> OpenSSH -> tmux -> cc path.

set -uo pipefail

TAILSCALE_FIREWALL_ZONE="tailscale-ssh"
SSHD_CONFIG="/etc/ssh/sshd_config.d/60-cc-mobile.conf"
TMUX_SESSION="cc-mobile"
PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() {
    printf '  ✓ %s\n' "$1"
    PASS_COUNT=$((PASS_COUNT + 1))
}

warn() {
    printf '  ! %s\n' "$1"
    WARN_COUNT=$((WARN_COUNT + 1))
}

fail() {
    printf '  ✗ %s\n' "$1"
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

service_active() {
    local unit="$1"
    if systemctl is-active --quiet "$unit" 2>/dev/null; then
        pass "$unit 正在运行"
    else
        fail "$unit 未运行"
    fi
}

echo "手机远程控制健康检查"
echo "========================"

echo ""
echo "[电脑服务]"
service_active tailscaled
service_active sshd
service_active firewalld

if command -v getenforce >/dev/null 2>&1; then
    selinux_mode="$(getenforce 2>/dev/null || true)"
    if [[ "$selinux_mode" == "Enforcing" ]]; then
        pass "SELinux 保持 Enforcing"
    else
        warn "SELinux 当前为 ${selinux_mode:-unknown}"
    fi
fi

echo ""
echo "[Tailscale]"
if ! command -v tailscale >/dev/null 2>&1; then
    fail "未找到 tailscale 命令"
else
    tailscale_ip="$(tailscale ip -4 2>/dev/null | head -n 1 || true)"
    if [[ -n "$tailscale_ip" ]]; then
        pass "本机 Tailscale IPv4: $tailscale_ip"
    else
        fail "本机尚未获得 Tailscale IPv4"
    fi

    tailscale_status="$(tailscale status 2>/dev/null || true)"
    if [[ -n "$tailscale_status" ]]; then
        pass "可以读取 tailnet 状态"
        peer_count="$(printf '%s\n' "$tailscale_status" | awk -v self_ip="$tailscale_ip" '$1 ~ /^100[.]/ && $1 != self_ip {count++} END {print count+0}')"
        if (( peer_count > 0 )); then
            pass "发现 $peer_count 个其他 tailnet 设备"
        else
            warn "未发现其他 tailnet 设备；请检查手机 Tailscale"
        fi
    else
        fail "无法读取 tailnet 状态"
    fi
fi

echo ""
echo "[出口节点]"
if command -v tailscale >/dev/null 2>&1 && tailscale debug prefs 2>/dev/null | grep -Fq '0.0.0.0/0'; then
    pass "本机正在发布 Tailscale 出口节点"
else
    warn "本机未发布出口节点；仅远程控制时可忽略"
fi

ipv4_forward="$(sysctl -n net.ipv4.ip_forward 2>/dev/null || true)"
ipv6_forward="$(sysctl -n net.ipv6.conf.all.forwarding 2>/dev/null || true)"
if [[ "$ipv4_forward" == "1" && "$ipv6_forward" == "1" ]]; then
    pass "IPv4/IPv6 转发均已启用"
else
    warn "转发状态 IPv4=${ipv4_forward:-unknown} IPv6=${ipv6_forward:-unknown}；出口节点需要两者为 1"
fi

if ip link show Mihomo >/dev/null 2>&1; then
    pass "检测到 Clash/Mihomo TUN 接口"
else
    warn "未检测到 Mihomo TUN；出口流量可能不会经过代理"
fi

if firewall-cmd --policy=tailscale-to-mihomo --query-ingress-zone=tailscale-ssh 2>/dev/null | grep -qx yes \
    && firewall-cmd --policy=tailscale-to-mihomo --query-egress-zone=mihomo-tun 2>/dev/null | grep -qx yes; then
    pass "firewalld 允许 Tailscale → Mihomo 转发"
else
    warn "未检测到 Tailscale → Mihomo 转发策略；出口流量可能被过滤"
fi

echo ""
echo "[SSH 边界]"
if [[ -r "$SSHD_CONFIG" ]] || sudo -n test -r "$SSHD_CONFIG" 2>/dev/null; then
    pass "手机 SSH 配置已安装"
elif [[ -d "$(dirname "$SSHD_CONFIG")" && ! -x "$(dirname "$SSHD_CONFIG")" ]]; then
    warn "SSH 配置目录仅 root 可访问；未使用 sudo 检查文件内容"
else
    fail "缺少 $SSHD_CONFIG"
fi

if command -v firewall-cmd >/dev/null 2>&1; then
    if firewall-cmd --zone="$TAILSCALE_FIREWALL_ZONE" --query-interface=tailscale0 2>/dev/null | grep -qx yes; then
        pass "tailscale0 已绑定 $TAILSCALE_FIREWALL_ZONE"
    else
        fail "tailscale0 未绑定 $TAILSCALE_FIREWALL_ZONE"
    fi

    if firewall-cmd --zone="$TAILSCALE_FIREWALL_ZONE" --query-service=ssh 2>/dev/null | grep -qx yes; then
        pass "$TAILSCALE_FIREWALL_ZONE 允许 SSH"
    else
        fail "$TAILSCALE_FIREWALL_ZONE 未允许 SSH"
    fi

    exposed_zones=()
    while IFS= read -r active_zone; do
        [[ -n "$active_zone" && "$active_zone" != "$TAILSCALE_FIREWALL_ZONE" ]] || continue
        if firewall-cmd --zone="$active_zone" --query-service=ssh 2>/dev/null | grep -qx yes; then
            exposed_zones+=("$active_zone")
        fi
    done < <(firewall-cmd --get-active-zones 2>/dev/null | awk '/^[^[:space:]]/ {print $1}')

    if (( ${#exposed_zones[@]} == 0 )); then
        pass "其他活动防火墙区域均未开放 SSH"
    else
        fail "SSH 还暴露在其他活动区域: ${exposed_zones[*]}"
    fi
else
    fail "未找到 firewall-cmd"
fi

echo ""
echo "[免密与会话]"
authorized_keys="$HOME/.ssh/authorized_keys"
if [[ -f "$authorized_keys" ]]; then
    key_mode="$(stat -c '%a' "$authorized_keys" 2>/dev/null || true)"
    if [[ "$key_mode" == "600" ]]; then
        pass "authorized_keys 权限为 600"
    else
        warn "authorized_keys 权限为 ${key_mode:-unknown}，建议设为 600"
    fi
else
    warn "未找到 authorized_keys，手机密钥登录可能不可用"
fi

if command -v tmux >/dev/null 2>&1; then
    if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
        pass "tmux 会话 $TMUX_SESSION 存在"
    else
        warn "tmux 会话 $TMUX_SESSION 尚未创建；首次登录会自动创建"
    fi
else
    fail "未安装 tmux"
fi

if command -v cc >/dev/null 2>&1; then
    pass "cc 启动器可执行: $(command -v cc)"
else
    fail "PATH 中找不到 cc 启动器"
fi

ssh_client_count="$(who 2>/dev/null | awk '$2 ~ /^pts\// && $NF ~ /^\(100[.]/ {count++} END {print count+0}')"
if (( ssh_client_count > 0 )); then
    pass "当前有 $ssh_client_count 个 Tailscale SSH 终端连接"
else
    warn "当前没有检测到 Tailscale SSH 终端；手机断开时这是正常的"
fi

echo ""
echo "结果: $PASS_COUNT 项通过，$WARN_COUNT 项提醒，$FAIL_COUNT 项失败"

if (( FAIL_COUNT > 0 )); then
    echo "建议先运行: systemctl status tailscaled sshd firewalld"
    exit 1
fi

echo "手机远程链路的电脑端配置正常。"
