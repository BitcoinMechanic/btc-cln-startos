import { IMPOSSIBLE, VersionInfo } from '@start9labs/start-sdk'
import { sdk } from '../sdk'
import { verifyOfficialBtcUpgrade } from '../utils'

export const current = VersionInfo.of({
  version: '#privkeyio:26.6.10:0',
  releaseNotes: { en_US: 'Add explicitly enabled, bounded swap coordinator actions to the 26.06.10 security-release baseline. Normal same-volume update from the official 26.6.10:0 package; existing wallet, channels, UI and watchtower data stay in place. Legacy swap authority and restored wallets are not imported.' },
  migrations: {
    up: IMPOSSIBLE,
    down: IMPOSSIBLE,
    other: {
      '=26.6.10:0': { up: async () => verifyOfficialBtcUpgrade(sdk.volumes.main.subpath('')) },
    },
  },
})
