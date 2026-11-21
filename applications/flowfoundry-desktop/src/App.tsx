import { useEffect, useState } from 'react';
import { getEnvironmentSnapshot, type EnvironmentSnapshot } from './bridge';

function sambaSummary(snapshot: EnvironmentSnapshot | null): string {
  if (!snapshot) return '正在读取本机状态。';
  if (!snapshot.linuxSamba) return snapshot.mode === 'preview'
    ? '浏览器预览无法读取本机 Samba 状态。'
    : '当前系统没有 Linux Samba 诊断。';
  const { config, usershare, service } = snapshot.linuxSamba;
  const parts = [
    config === 'valid' ? 'Samba 配置可解析' : config === 'missing' ? '未找到 Samba 配置检查工具' : 'Samba 配置检查失败',
    service === 'active' ? '服务运行中' : service === 'inactive' ? '服务未运行' : '服务状态未知',
    usershare === 'accessible' ? '当前用户可读取 usershare' : usershare === 'permission_denied' ? '当前用户无权访问 usershare' : usershare === 'missing' ? '未找到 usershare 工具' : 'usershare 状态读取失败',
  ];
  return `${parts.join('；')}。此处仅作只读诊断。`;
}

const steps = [
  '在 Linux 电脑上选择要共享的文件夹，并为 Samba 配置已授权账户。',
  '确认共享权限、文件夹权限和防火墙范围后，复制 SMB 地址。',
  'iPhone 打开「文件」→「浏览」→「…」→「连接服务器」。',
  '输入 SMB 地址，选择「注册用户」，使用 Samba 账户登录。',
];

export function App() {
  const [snapshot, setSnapshot] = useState<EnvironmentSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      setError(null);
      setSnapshot(await getEnvironmentSnapshot());
    } catch (cause) {
      setError(`无法读取本机状态：${String(cause)}`);
    }
  }

  useEffect(() => { void refresh(); }, []);

  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">F</span><div><strong>FlowFoundry</strong><small>DESKTOP</small></div></div>
      <nav aria-label="主导航">
        <a className="selected" href="#overview">总览</a>
        <a href="#bridge">File Bridge</a>
        <a href="#guide">首个连接场景</a>
      </nav>
      <div className="sidebar-foot">本地控制中心 · 预览版</div>
    </aside>
    <main id="overview">
      <header><div><div className="eyebrow">FLOWFOUNDRY DESKTOP</div><h1>让文件在设备间自由流动</h1><p>统一管理共享状态、连接入口和后续的智能体文件权限。</p></div><span className="phase">基础框架</span></header>
      <section className="hero" id="bridge">
        <div><div className="eyebrow">FILE BRIDGE</div><h2>电脑与手机文件桥</h2><p>目标覆盖 Windows、Linux、iPhone、Android；首个验收组合是 Linux 与 iPhone。</p></div>
        <div className="status"><span className="dot" />{snapshot?.fileBridge === 'unavailable' ? '尚未启用' : '正在检测'}</div>
      </section>
      <div className="grid">
        <section className="card"><div className="card-label">本机环境</div><h3>{snapshot?.platform ?? '正在检测…'}</h3><p>{error ?? snapshot?.message ?? '正在读取本机状态。'}</p><button className="secondary" onClick={() => void refresh()}>刷新状态</button></section>
        <section className="card"><div className="card-label">Linux Samba 诊断</div><h3>{snapshot?.linuxSamba ? '只读检查' : '等待本机检查'}</h3><p>{error ?? sambaSummary(snapshot)}</p></section>
        <section className="card"><div className="card-label">SMB 连接地址</div><h3>尚未创建共享</h3><p>主机端共享接入后，这里会显示可复制的局域网连接地址。</p><button className="secondary" disabled>复制地址</button></section>
        <section className="card"><div className="card-label">共享文件夹</div><h3>0 个已登记共享</h3><p>仅管理由 FlowFoundry 创建并登记的共享，不影响系统中的其他共享。</p><button className="primary" disabled>创建共享 · 待接入</button></section>
      </div>
      <section className="guide" id="guide"><div className="eyebrow">首个验收场景 · 尚未接入</div><h2>Linux 与 iPhone</h2><ol>{steps.map(step => <li key={step}>{step}</li>)}</ol><p className="note">仅使用经身份验证的账户。首次连接前请确认两台设备位于可信局域网。Windows 主机适配和 Android 手机连接也在目标范围内，尚待分别验收。</p></section>
    </main>
  </div>;
}
