import { T } from '@start9labs/start-sdk'
import { sdk } from '../sdk'
import { rootDir, verifyOfficialBtcUpgrade } from '../utils'
import { legacyUpgradeProgram } from './legacyUpgradeProgram'

/** StartOS stops the service before this migration. The wallet mount is read-only. */
export async function verifyLegacyOfficialBtcUpgrade(effects: T.Effects) {
  await verifyOfficialBtcUpgrade(sdk.volumes.main.subpath(''), async () => {
    const mounts = sdk.Mounts.of().mountVolume({ volumeId: 'main', subpath: null, mountpoint: rootDir, readonly: true })
    await sdk.SubContainer.withTemp(effects, { imageId: 'lightning' }, mounts, 'legacy-btc-upgrade-check', async sub => {
      const result = await sub.exec(['python3', '-B', '-c', legacyUpgradeProgram, rootDir])
      let report: any
      try { report = JSON.parse(String(result.stdout)) } catch { throw new Error('Legacy BTC history could not be verified; all records preserved.') }
      if (result.exitCode !== 0 || report?.admitted !== true || report?.legacy_records_preserved !== true || report?.legacy_authority_imported !== false) {
        const reason = typeof report?.reason === 'string' && /^[a-z_]{1,80}$/.test(report.reason) ? report.reason : 'legacy_state_unverified'
        throw new Error('Legacy BTC update refused: ' + reason + '. All records preserved.')
      }
    })
  })
}
