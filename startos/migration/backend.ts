// Network/genesis alone are shared with XBT. Require the configured SHA256
// backend's post-activation header shape as well, before starting this engine.
export function verifyBackend(chain: any, checkpoint: unknown, header: unknown) {
  if (chain?.chain !== 'main' || chain.initialblockdownload !== false || chain.pruned !== false ||
      !Number.isSafeInteger(chain.blocks) || chain.blocks < 961640 ||
      typeof checkpoint !== 'string' || !/^[0-9a-f]{64}$/.test(checkpoint) ||
      checkpoint === '0000000000000050c1e5f69672f459293be14f46e5a494e7a8c8541396f18eeb' ||
      typeof header !== 'string' || !/^[0-9a-f]{160}$/.test(header)) {
    throw new Error('BTC requires a synced, unpruned SHA256 mainnet backend')
  }
}
