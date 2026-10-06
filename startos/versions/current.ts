import { IMPOSSIBLE, VersionInfo } from '@start9labs/start-sdk'

export const current = VersionInfo.of({
  version: '26.6.8:10',
  releaseNotes: {
    en_US: 'Add a dedicated read-only inspection credential for swap preflight. No spending or gate authority.',
  },
  migrations: { up: async () => {}, down: IMPOSSIBLE },
})
