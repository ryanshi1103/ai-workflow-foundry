/** A display address, never an authorization decision. */
export function smbAddress(ipv4: string, shareName: string): string {
  const octets = ipv4.split('.');
  if (octets.length !== 4 || octets.some(part => !/^\d{1,3}$/.test(part) || Number(part) > 255)) {
    throw new Error('Invalid IPv4 address');
  }
  if (!shareName || shareName === '.' || shareName === '..' || /[\\/\u0000-\u001f]/.test(shareName)) {
    throw new Error('Invalid share name');
  }
  return `smb://${octets.map(Number).join('.')}/${encodeURIComponent(shareName)}`;
}
