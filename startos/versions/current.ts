import { IMPOSSIBLE, VersionInfo } from '@start9labs/start-sdk'
export const current = VersionInfo.of({
  version: '#privkeyio:26.6.10:7',
  releaseNotes: { en_US: 'Support recipient invoice timelocks within the existing 288-block route budget. Bind final payment checks to the saved route and preserve recovery margins. Report safe invoice and route failures explicitly.' },
  migrations: { up: IMPOSSIBLE, down: IMPOSSIBLE, other: { '=#privkeyio:26.6.10:6': { up: async () => {} }, '=#privkeyio:26.6.10:5': { up: async () => {} }, '=#privkeyio:26.6.10:4': { up: async () => {} }, '=#privkeyio:26.6.10:3': { up: async () => {} }, '=#privkeyio:26.6.10:1': { up: async () => {} }, '=#privkeyio:26.6.10:2': { up: async () => {} } } },
})
