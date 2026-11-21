import { invoke, isTauri } from '@tauri-apps/api/core';

export interface EnvironmentSnapshot {
  platform: string;
  mode: 'native' | 'preview';
  fileBridge: 'unavailable';
  message: string;
  linuxSamba: {
    config: 'valid' | 'invalid' | 'missing';
    usershare: 'accessible' | 'permission_denied' | 'error' | 'missing';
    service: 'active' | 'inactive' | 'unknown';
  } | null;
}

const preview: EnvironmentSnapshot = {
  platform: '浏览器预览',
  mode: 'preview',
  fileBridge: 'unavailable',
  message: '当前是界面预览。共享配置与文件操作需要 Linux 或 Windows 原生后端。',
  linuxSamba: null,
};

export async function getEnvironmentSnapshot(): Promise<EnvironmentSnapshot> {
  if (!isTauri()) return preview;
  return invoke<EnvironmentSnapshot>('get_environment_snapshot');
}
