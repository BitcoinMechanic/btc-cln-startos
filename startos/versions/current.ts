import { IMPOSSIBLE, VersionInfo } from '@start9labs/start-sdk'
export const current = VersionInfo.of({
  version: '#privkeyio:26.6.10:8',
  releaseNotes: { en_US: 'Support routes up to 576 blocks and safely refresh idle automatically managed outgoing grants. Preserve the additional 150-block incoming recovery margin, existing swap authority, manual grants, fee limits and hop limits.' },
  migrations: { up: IMPOSSIBLE, down: IMPOSSIBLE, other: { '=#privkeyio:26.6.10:7': { up: async () => {} }, '=#privkeyio:26.6.10:6': { up: async () => {} }, '=#privkeyio:26.6.10:5': { up: async () => {} }, '=#privkeyio:26.6.10:4': { up: async () => {} }, '=#privkeyio:26.6.10:3': { up: async () => {} }, '=#privkeyio:26.6.10:1': { up: async () => {} }, '=#privkeyio:26.6.10:2': { up: async () => {} } } },
})
