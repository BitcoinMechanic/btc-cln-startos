import { IMPOSSIBLE, VersionInfo } from '@start9labs/start-sdk'
export const current = VersionInfo.of({
  version: '#privkeyio:26.6.10:10',
  releaseNotes: { en_US: 'Fix peer read-loop stalls after oversized or queue-dropped gossip. Continue reading pongs and channel messages instead of disconnecting a responsive peer on a false ping timeout.' },
  migrations: { up: IMPOSSIBLE, down: IMPOSSIBLE, other: { '=#privkeyio:26.6.10:9': { up: async () => {} }, '=#privkeyio:26.6.10:8': { up: async () => {} }, '=#privkeyio:26.6.10:7': { up: async () => {} }, '=#privkeyio:26.6.10:6': { up: async () => {} }, '=#privkeyio:26.6.10:5': { up: async () => {} }, '=#privkeyio:26.6.10:4': { up: async () => {} }, '=#privkeyio:26.6.10:3': { up: async () => {} }, '=#privkeyio:26.6.10:1': { up: async () => {} }, '=#privkeyio:26.6.10:2': { up: async () => {} } } },
})
