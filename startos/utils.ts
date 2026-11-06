import { lstat, readFile } from 'node:fs/promises'
import { join } from 'node:path'
import { T } from '@start9labs/start-sdk'
import {
  rpcHostId as btcRpcHostId,
  rpcPort as btcRpcPort,
} from 'bitcoin-core-startos/startos/utils'
import { sdk } from './sdk'

export const uiPort = 4500
export const wsPort = 4269
export const rpcPort = 8080
export const peerPort = 9735
export const clnrestPort = 3010
export const watchtowerPort = 9814
export const websocketPort = 7272
export const grpcPort = 2106

export const rootDir = '/root/.lightning'
export const bitcoinDataDir = '/mnt/bitcoin'

/** Host path of the rune the CLN Application UI authenticates with. */
export const commandoEnv = '/media/startos/volumes/main/.commando-env'

export const mainMounts = sdk.Mounts.of().mountVolume({
  volumeId: 'main',
  subpath: null,
  mountpoint: rootDir,
  readonly: false,
})

export function cliJson<T>(stdout: unknown): T | null {
  if (typeof stdout !== 'string') return null
  try {
    return JSON.parse(stdout.slice(stdout.indexOf('{'))) as T
  } catch {
    return null
  }
}

// lightning-cli reports an RPC error as a JSON object on stdout, exit code 1, sometimes after `# …` progress lines.
export const errorMessage = (res: { stdout: unknown; stderr: unknown }) => {
  const raw = String(res.stdout || res.stderr).trim()
  const parsed = cliJson<{ message?: unknown }>(raw)
  return parsed?.message ? String(parsed.message) : raw || 'unknown'
}

/**
 * bitcoind's RPC bridge address, resolved through `sdk.host.getBridgeAddress` and
 * split into the `{ host, port }` pair lightningd's config, teos.toml, and the
 * sync health check consume. `.const()` stays churn-free: bitcoind's assigned
 * RPC port persists across its updates/restarts, so CLN restarts only if
 * bitcoind is (re)installed on a new port. `null` while bitcoind's binding is
 * absent, so callers omit the address rather than writing a placeholder.
 */
export const bitcoindRpcBridge = async (effects: T.Effects) => {
  const addr = await sdk.host
    .getBridgeAddress(effects, {
      packageId: 'bitcoind',
      hostId: btcRpcHostId,
      internalPort: btcRpcPort,
      ssl: false,
    })
    .const()
  if (!addr) return null
  const [host, port] = addr.split(':')
  return { host, port: Number(port) }
}

// Network/genesis alone are shared with XBT. Require the configured SHA256
// backend's post-activation header shape as well, before starting this engine.
export function verifyBtcBackend(chain: any, checkpoint: unknown, header: unknown) {
  if (chain?.chain !== 'main' || chain.initialblockdownload !== false || chain.pruned !== false ||
      !Number.isSafeInteger(chain.blocks) || chain.blocks < 961640 ||
      typeof checkpoint !== 'string' || !/^[0-9a-f]{64}$/.test(checkpoint) ||
      checkpoint === '0000000000000050c1e5f69672f459293be14f46e5a494e7a8c8541396f18eeb' ||
      typeof header !== 'string' || !/^[0-9a-f]{160}$/.test(header)) {
    throw new Error('BTC requires a synced, unpruned SHA256 mainnet backend')
  }
}

/** Read-only admission for the exact official 26.6.10:0 same-volume update. */
export async function verifyOfficialBtcUpgrade(root: string) {
  const present = async (path: string) => {
    try { return await lstat(path) } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') return null
      throw error
    }
  }
  for (const rel of ['', 'bitcoin']) {
    const stat = await present(join(root, rel))
    if (!stat?.isDirectory() || stat.isSymbolicLink()) throw new Error('Expected the existing mainnet wallet volume')
  }
  for (const rel of ['bitcoin/hsm_secret', 'bitcoin/lightningd.sqlite3', 'store.json']) {
    const stat = await present(join(root, rel))
    if (!stat?.isFile() || stat.isSymbolicLink() || stat.nlink !== 1 || stat.size === 0) throw new Error('Unsupported wallet layout; existing files preserved')
  }
  const store = JSON.parse(await readFile(join(root, 'store.json'), 'utf8'))
  if (!store || typeof store !== 'object' || store.restore) throw new Error('Finish backup recovery before a coordinator update')
  const refused = ['xbt', 'xbt-regtest', 'regtest', 'testnet', 'signet', 'node-restored.json', 'swap-restored.json',
    'btc-gate-restored.json', 'forward-pilot-restored.json', 'btc-gate-activation.json', 'coordinator-preparation.json',
    'forward-pilot.json', 'forward-session.json', 'forward-sessions', 'forward-swaps', 'reverse-session.json',
    'reverse-sessions', 'reverse-swaps', 'swap-coordinator-v1', 'swap-gate-v1', 'bounded-authority-v1',
    'customer-remote-v1', 'customer-invoices-v1', 'coordinator-admin-v1']
  for (const base of [root, join(root, 'bitcoin')]) {
    for (const rel of refused) if (await present(join(base, rel))) throw new Error('Existing swap, restore or foreign-network state requires a separate reviewed update')
  }
}
