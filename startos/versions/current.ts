import { IMPOSSIBLE, VersionInfo } from '@start9labs/start-sdk'

export const current = VersionInfo.of({
  version: '26.6.8:8',
  releaseNotes: {
    en_US: 'Add explicit bounded BTC gate opt-in and status with persistent journal and restore invalidation. Controller live execution remains disabled.',
  },
  migrations: { up: async () => {}, down: IMPOSSIBLE },
})
