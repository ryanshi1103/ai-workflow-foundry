import { describe, expect, it } from 'vitest';
import { smbAddress } from './connection';

describe('SMB display address', () => {
  it('encodes a share name that contains spaces', () => {
    expect(smbAddress('192.168.1.23', 'Family Files')).toBe('smb://192.168.1.23/Family%20Files');
  });

  it.each(['192.168.1.256', '192.168.1', '127.0.0.1\nexample.com'])('rejects invalid IPv4: %s', ip => {
    expect(() => smbAddress(ip, 'Files')).toThrow('Invalid IPv4');
  });

  it.each(['', '..', 'Files/Other', 'Files\\Other', 'Files\nOther'])('rejects invalid share name: %s', name => {
    expect(() => smbAddress('192.168.1.23', name)).toThrow('Invalid share name');
  });
});
