/**
 * Tailscale detection — checks if Tailscale is active and finds known peers.
 *
 * Used during `charli init` to auto-suggest the server URL
 * when both the CLI machine and the Mac Mini are on the same Tailnet.
 *
 * Gracefully returns disconnected status if Tailscale isn't installed.
 */

import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import type { TailscaleStatus, TailscalePeer } from '../types.js';

const execFileAsync = promisify(execFile);

/**
 * Get Tailscale connection status and peer list.
 */
export async function getTailscaleStatus(): Promise<TailscaleStatus> {
  try {
    const { stdout } = await execFileAsync('tailscale', ['status', '--json'], {
      timeout: 5000,
    });

    const data = JSON.parse(stdout);

    // Extract our own info
    const self = data.Self;
    const hostname = self?.HostName || undefined;
    const tailscaleIps: string[] = self?.TailscaleIPs || [];
    const tailscaleIp = tailscaleIps[0] || undefined;

    // Extract peers
    const peers: TailscalePeer[] = [];
    if (data.Peer) {
      for (const peer of Object.values(data.Peer) as Array<Record<string, unknown>>) {
        const peerIps = (peer.TailscaleIPs as string[]) || [];
        peers.push({
          hostname: peer.HostName as string,
          tailscaleIp: peerIps[0] || '',
          online: peer.Online as boolean,
        });
      }
    }

    return { connected: true, hostname, tailscaleIp, peers };
  } catch {
    // Tailscale not installed, not running, or command failed
    return { connected: false };
  }
}

/**
 * Find a CHARLI server among Tailscale peers.
 * Looks for common server hostnames.
 */
export function findServerPeer(status: TailscaleStatus): TailscalePeer | null {
  if (!status.peers) return null;

  const serverNames = ['charli-server', 'mac-mini', 'macmini'];
  return status.peers.find(
    (p) => p.online && serverNames.some((name) => p.hostname.toLowerCase().includes(name)),
  ) || null;
}
