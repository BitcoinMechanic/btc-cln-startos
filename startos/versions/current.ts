import { IMPOSSIBLE, VersionInfo } from '@start9labs/start-sdk'
export const current = VersionInfo.of({
  version: '#privkeyio:26.6.10:5',
  releaseNotes: { en_US: 'Trust a local Swap Controller once: create and renew scoped incoming and outgoing grants automatically. Preserve swap recovery, pause managed grants when trust is disabled, and never restore spending permission from backups.' },
  migrations: { up: IMPOSSIBLE, down: IMPOSSIBLE, other: { '=#privkeyio:26.6.10:4': { up: async () => {} }, '=#privkeyio:26.6.10:3': { up: async () => {} }, '=#privkeyio:26.6.10:1': { up: async () => {} }, '=#privkeyio:26.6.10:2': { up: async () => {} } } },
})
