import { copyFile, unlink, writeFile } from 'fs/promises'
import { rescanBlockchain } from './actions/rescanBlockchain'
import { storeJson } from './fileModels/store.json'
import { i18n } from './i18n'
import { sdk } from './sdk'

export const { createBackup, restoreInit } = sdk.setupBackups(
  async ({ effects }) =>
    sdk.Backups.ofVolumes('main')
      .setOptions({
        exclude: [
        'forward-session.json', 'forward-sessions', 'forward-swaps',
        'forward-pilot.json', 'forward-pilot.lock',
        'controller-inspection-read-only.json',
        'controller-inspection-read-only.lock',
          'btc-gate-activation.json',
          'btc-gate.lock',
          'coordinator-preparation.json',
          'coordinator-preparation.lock',
          'bitcoin/lightning-rpc',
          'bitcoin/lightningd.sqlite3',
          'bitcoin/lightningd.sqlite3-wal',
          'bitcoin/lightningd.sqlite3-shm',
          'bitcoin/gossip_store',
          'data/app/application-cln.log',
        ],
      })
      .setPostRestore(async (effects) => {
      await writeFile(sdk.volumes.main.subpath('forward-pilot-restored.json'), JSON.stringify({blocked:true}), {mode:0o600})
        await writeFile('/media/startos/volumes/main/btc-gate-restored.json', JSON.stringify({ schema: 1, blocked: true }), { mode: 0o600 })
        await unlink('/media/startos/volumes/main/btc-gate-activation.json').catch((error: NodeJS.ErrnoException) => {
          if (error.code !== 'ENOENT') throw error
        })

      await unlink(sdk.volumes.main.subpath('controller-inspection-read-only.json')).catch((error: NodeJS.ErrnoException) => {
        if (error.code !== 'ENOENT') throw error
      })
        // Preparation is local opt-in, never restored as coordinator authority.
        await unlink('/media/startos/volumes/main/coordinator-preparation.json')
          .catch((error: NodeJS.ErrnoException) => {
            if (error.code !== 'ENOENT') throw error
          })
        // CLN's chanbackup plugin keeps emergency.recover describing the
        // CURRENT channel set, so once the restored node processes (and
        // forgets) the old channels, it rewrites the file without them.
        // Snapshot the restored copy first: it is the last file that can
        // rebuild recovery stubs for the pre-backup channels (lightning-cli
        // emergencyrecover / recoverchannel), and this copy is never touched.
        const scb = '/media/startos/volumes/main/bitcoin/emergency.recover'
        await copyFile(
          scb,
          `${scb}.restored-${new Date().toISOString().slice(0, 10)}`,
        ).catch(() => {})

        await storeJson.merge(effects, { restore: true })

        // A restored wallet database is empty: the balance reads zero until a
        // blockchain rescan re-discovers the wallet's coins, and nothing else
        // in the UI says so.
        await sdk.action.createOwnTask(effects, rescanBlockchain, 'important', {
          reason: i18n(
            'After restoring from backup, your on-chain balance reads zero until the blockchain is rescanned. Run this action with a blockheight from before your node was first created, prefixed with a hyphen (for example -800000). The rescan takes hours; the Synced health check stays red while it works — leave Core Lightning and Bitcoin running until it turns green.',
          ),
        })
      }),
)
