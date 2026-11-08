import { IMPOSSIBLE, VersionInfo } from '@start9labs/start-sdk'
export const current = VersionInfo.of({
  version: '#privkeyio:26.6.10:4',
  releaseNotes: { en_US: 'Use the knots-prerdts SHA256 companion and its pruned-block fetching proxy. Preserve swap-controller integration, existing channels and restore fences; verify historical block access before startup.' },
  migrations: { up: IMPOSSIBLE, down: IMPOSSIBLE, other: { '=#privkeyio:26.6.10:3': { up: async () => {} }, '=#privkeyio:26.6.10:1': { up: async () => {} }, '=#privkeyio:26.6.10:2': { up: async () => {} } } },
})
