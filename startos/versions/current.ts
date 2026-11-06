import { IMPOSSIBLE, VersionInfo } from '@start9labs/start-sdk'
import { verifyLegacyOfficialBtcUpgrade } from '../live/legacyUpgrade'

export const current = VersionInfo.of({
  version: '#privkeyio:26.6.10:1',
  releaseNotes: { en_US: 'Add a guarded update from official 26.6.10:0 with retained, fully checked legacy BTC swap journals. Checks the stopped wallet read-only, including archived funding, terminal payment/HTLC evidence and narrowly scoped failed self-payment attempts for expired incoming invoices. Preserves all records and does not import old coordinator authority. Wallet recovery, pending swaps, unknown state and contradictory evidence are refused. Native engine, plugins and UI are unchanged from candidate :0.' },
  migrations: {
    up: IMPOSSIBLE,
    down: IMPOSSIBLE,
    other: {
      '=26.6.10:0': { up: async ({ effects }) => verifyLegacyOfficialBtcUpgrade(effects) },
      '=#privkeyio:26.6.10:0': { up: async () => {} },
    },
  },
})
