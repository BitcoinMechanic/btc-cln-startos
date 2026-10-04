import { IMPOSSIBLE, VersionInfo } from '@start9labs/start-sdk'

export const current = VersionInfo.of({
  version: '26.6.8:7',
  releaseNotes: {
    en_US: 'Add dedicated read-only controller credential actions with identity binding, durable intent and exact-rune revocation. No live swap activation or interface changes.',
  },
  migrations: { up: async () => {}, down: IMPOSSIBLE },
})
