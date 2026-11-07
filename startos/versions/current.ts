import { IMPOSSIBLE, VersionInfo } from '@start9labs/start-sdk'
export const current = VersionInfo.of({
  version: '#privkeyio:26.6.10:3',
  releaseNotes: { en_US: 'Automatic same-server BTC/XBT controller pairing using approved bounded grants, discovered HTTPS endpoints and the StartOS root CA. Preserves manual pairings, existing swaps and restore fences.' },
  migrations: { up: IMPOSSIBLE, down: IMPOSSIBLE, other: { '=#privkeyio:26.6.10:1': { up: async () => {} }, '=#privkeyio:26.6.10:2': { up: async () => {} } } },
})
