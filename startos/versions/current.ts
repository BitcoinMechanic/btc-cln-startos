import { IMPOSSIBLE, VersionInfo } from '@start9labs/start-sdk'
export const current = VersionInfo.of({
  version: '#privkeyio:26.6.9:0',
  releaseNotes: { en_US: 'Dedicated BTC coordinator test candidate: native CLN and bounded swap authority with explicit setup. Fresh installation only; no legacy package migration.' },
  migrations: { up: IMPOSSIBLE, down: IMPOSSIBLE },
})
