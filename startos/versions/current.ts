import { IMPOSSIBLE, VersionInfo } from '@start9labs/start-sdk'

export const current = VersionInfo.of({
  version: '26.6.8:9',
  releaseNotes: {
    en_US: 'Add a separate restricted BTC gate observation credential. Controller live execution remains disabled.',
  },
  migrations: { up: async () => {}, down: IMPOSSIBLE },
})
