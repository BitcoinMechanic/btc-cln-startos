import { IMPOSSIBLE, VersionInfo } from '@start9labs/start-sdk'

export const v_26_6_8_6 = VersionInfo.of({
  version: '26.6.8:6',
  releaseNotes: {
    en_US: 'Experimental BTC swap preparation: pinned inactive modules and identity-bound opt-in. Packaged bidirectional controller regtests passed. Live gates remain disabled; controller pairing required.',
  },
  migrations: { up: async () => {}, down: IMPOSSIBLE },
})
