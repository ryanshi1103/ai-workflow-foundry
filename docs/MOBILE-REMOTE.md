# 手机远程控制 cc

## 目标架构

Android 手机通过 Tailscale 加入与 Fedora 电脑相同的私有 tailnet，再用 Termux
或 ConnectBot 建立 SSH 终端。电脑端由 `tmux` 保持会话，终端中运行正式部署的
`~/.local/bin/cc`。这会复用同一个启动器、项目目录、AI 登录状态和权限菜单。

```text
Android: Tailscale + SSH 终端
               │ WireGuard tailnet
               ▼
Fedora: Tailscale → OpenSSH → tmux → cc → Claude / DeepSeek / Codex
```

## 电脑端安装

在本项目中运行：

```bash
./scripts/setup-mobile-remote.sh
```

脚本必须由普通桌面用户启动，并会在需要修改软件包和系统服务时调用 `sudo`。
它使用 Tailscale 官方 Fedora 仓库，启用 `tailscaled` 和 Fedora OpenSSH。SSH 仅在
firewalld 的 `tailscale-ssh` 区域（`tailscale0` 接口）开放；不会开放公网端口、
关闭 SELinux 或修改路由器。

Fedora 默认启用 SELinux 强制模式，而 Tailscale 内置 SSH 会提示可能受 SELinux
限制。脚本因此使用 Fedora 原生、支持 SELinux 的 OpenSSH，并把 Tailscale 只作为
加密私网。它还会从其他当前活动防火墙区域移除 `ssh` 服务，避免启用 `sshd` 后从
Wi-Fi 或有线局域网暴露端口 22。

安装过程中会显示登录链接。用手机浏览器打开，并使用准备在 Android Tailscale
应用中登录的同一账号完成认证。

官方参考：

- <https://tailscale.com/docs/install/linux>
- <https://tailscale.com/docs/install/android>
- <https://tailscale.com/docs/features/tailscale-ssh>
- <https://tailscale.com/docs/reference/messages/client/ssh-unavailable-selinux-enabled>
- <https://tailscale.com/docs/reference/ssh-over-tailscale>
- <https://tailscale.com/docs/features/access-control>

## 手机端使用

1. 安装 Tailscale Android 应用并登录同一账号。
2. 安装 Termux（完整终端体验）或 ConnectBot（简单 SSH 客户端）。
3. 使用电脑的 MagicDNS 名称或 Tailscale IP 登录。
4. 进入持久会话并启动 `cc`：

```bash
ssh ryan@<电脑名称>
tmux new-session -A -s cc-mobile
~/.local/bin/cc
```

手机网络断开不会结束 `tmux` 中的 AI 任务。重新 SSH 并再次运行
`tmux new-session -A -s cc-mobile` 即可返回原会话。

### ConnectBot 一键免密连接

在 ConnectBot 主机列表中创建永久主机 `ryan@100.66.61.58:22`，不要只通过
`ssh://` Intent 建立临时会话。为手机生成无密码的 Ed25519 密钥 `cc-mobile`：

- 开启“启动时载入密钥”，关闭“使用前确认”；
- 将公钥追加到电脑的 `~/.ssh/authorized_keys`，文件权限保持 `600`；
- 在主机设置中把“使用密钥验证”显式设为 `cc-mobile`；
- 开启“保持连接”；
- 把“登录后自动运行”设为 `tmux new-session -A -s cc-mobile`，末尾必须包含换行。

这样重启 ConnectBot 后只需点击一次主机即可免密登录，并直接回到正在运行的 `cc`
会话。手机丢失时，除在 Tailscale 管理台撤销设备外，还应从
`~/.ssh/authorized_keys` 删除注释为 `cc-mobile` 的公钥行。

### ConnectBot 中输入中文

ConnectBot 当前正式版的普通终端输入路径使用直接按键模式，Android 中文、日文、
韩文输入法无法在该模式中完成拼音/候选词组合。官方正在开发 Compose Mode (IME)：
<https://github.com/connectbot/connectbot/pull/2105>。

在正式版中使用内置的浮动文本输入框：

1. 显示手机软键盘和 ConnectBot 的特殊按键栏；
2. 点击特殊按键栏最右侧的铅笔图标；
3. 在弹出的标准文本输入框中切换到“中文（简体）→ 拼音”；
4. 输入中文并点击发送箭头，把文字注入终端；
5. 返回终端后按回车，将消息发送给 Claude、DeepSeek 或 Codex。

如果看不到铅笔图标，先更新 ConnectBot 并确认特殊按键栏已启用。临时替代方法是
在其他应用中输入中文后复制，再粘贴到终端。需要持续直接输入 CJK 文字时，也可以
改用 Termux SSH 客户端。

## 远程安全行为

`cc` 通过 `SSH_CONNECTION` 或 `SSH_TTY` 识别远程会话。远程模式保留所有项目、
工具和权限选择，但 Codex `danger-full-access` 与 Claude/DeepSeek
`bypassPermissions` 需要先输入 `remote-yes`，之后仍需原有的 `yes` 启动确认。

电脑必须保持开机、联网且未进入会关闭网络的睡眠状态。不要启用免密 sudo，不要
把系统 SSH 端口映射到公网；手机丢失时应立即在 Tailscale 管理台撤销该设备。

## Android 上已有其他 VPN

Android 的个人用户空间同一时间只能由一个应用占用系统 VPN 通道。如果 v2rayNG、
Clash 或其他代理 VPN 正在运行，Tailscale 可能已经登录并出现在设备列表中，但数据
通道仍无法建立。需要先在原 VPN 应用中停止连接，再回到 Tailscale 打开连接；用完
远程控制后可以反向切回。不要把节点“在线”误认为端到端链路已经可用，应以
`tailscale ping <手机地址>` 或实际 SSH 连接为准。

## 同时访问大陆外网络：出口节点

Android 和 iOS 通常不能让 Tailscale 与另一个基于系统 VPN 通道的客户端同时工作。
可以让手机只连接 Tailscale，并把这台电脑发布为出口节点：

```text
手机 → Tailscale ┬→ OpenSSH → tmux → cc
                 └→ 电脑 Clash/Mihomo TUN → Internet
```

本机已运行 Clash/Mihomo TUN 时，在项目中执行：

```bash
./scripts/setup-mobile-exit-node.sh
```

脚本会持久启用 IPv4/IPv6 转发并发布 Tailscale 出口路由，不会修改 Clash 节点或
订阅。Fedora 的 firewalld 默认阻止跨区域转发，因此脚本还会创建仅允许
`tailscale-ssh` → `mihomo-tun` 的单向转发策略，不会开放新的入站端口。随后按
Tailscale 管理后台提示批准出口节点，并在手机 Tailscale 的“出口节点”中选择本机。
电脑和 Clash 必须保持在线。

撤销发布：

```bash
./scripts/setup-mobile-exit-node.sh --disable
```

如果电脑端代理不接管转发流量，可改用境外 VPS 上的 Tailscale 出口节点或官方
Mullvad 出口节点附加服务。不要为此把电脑的 SSH 端口直接暴露到公网。

### Android 上 Tailscale DNS 导致网页打不开

如果固定 IP 的 SSH 能连接，但 Chrome 显示 `DNS_PROBE_FINISHED_BAD_SECURE_CONFIG`
或无法解析公网域名，进入 Tailscale → Settings → DNS settings，关闭
`Use Tailscale DNS`，让 Android 使用原有系统 DNS。该设置不关闭 Tailscale 隧道，
也不影响通过 `100.66.61.58` 连接本机；只是不能再依赖 MagicDNS 主机名。

本机实测的完整成功条件为：手机路由表默认路由指向 `tun0`、手机与电脑的公网出口
IP 一致、境外 HTTPS 返回成功，并且 ConnectBot 仍能连接 `100.66.61.58:22`。

## 验证

电脑端优先运行项目内的只读健康检查：

```bash
./scripts/check-mobile-remote.sh
```

它会检查 Tailscale、OpenSSH、firewalld/SELinux、SSH 暴露边界、
`authorized_keys` 权限、`tmux` 会话和 `cc`，不会修改系统配置，也不会输出密钥。

也可以分别运行：

```bash
tailscale status
tailscale ip -4
systemctl is-active tailscaled
systemctl is-active sshd
```

预期 `tailscaled` 和 `sshd` 均为 `active`。另请确认只有 Tailscale 防火墙区域允许
SSH：

```bash
firewall-cmd --zone=tailscale-ssh --query-service=ssh
firewall-cmd --zone=FedoraWorkstation --query-service=ssh
```

预期依次输出 `yes`、`no`。

Tailscale 状态中的 `active` 表示近期是否有数据流量；设备暂时显示
`active=false` 不等于离线。应结合 `online=true`、`tailscale ping` 或实际 SSH
连接判断。
