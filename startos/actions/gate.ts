import { T } from '@start9labs/start-sdk'
import { sdk } from '../sdk'
import { mainMounts, rootDir } from '../utils'
const metadata = (name: string) => async () => ({
  name, description: 'BTC incoming swap gate. Controller live execution remains disabled.',
  warning: null, allowedStatuses: 'only-running' as const,
  group: 'Swap Gate', visibility: 'enabled' as const,
})
async function invoke(effects: T.Effects, operation: string, confirmed = false): Promise<T.ActionResult & { version: '1' }> {
  return sdk.SubContainer.withTemp(effects, { imageId: 'lightning' }, mainMounts,
    'btc-gate-action', async sub => {
      const response = await sub.exec(['/usr/bin/python3', '/usr/local/libexec/btc-controller/gate.py', operation, rootDir], { input: JSON.stringify({ confirmed }) })
      const result = JSON.parse(String(response.stdout))
      if (response.exitCode !== 0) throw new Error(result.error + ' Reason: ' + result.reason)
      return { version: '1', title: 'BTC Swap Gate',
        message: 'If restart required is true, restart Core Lightning and run BTC Swap Gate Status. This does not enable controller execution or publish an invoice.',
        result: { type: 'group', value: Object.entries(result).map(([key, value]) => ({
          name: key.replaceAll('_', ' '), description: null, type: 'single' as const,
          value: String(value), masked: false, copyable: false, qr: false,
        })) },
      }
    })
}
export const btcGateStatus = sdk.Action.withInput('btc-gate-status', metadata('BTC Swap Gate Status'),
  sdk.InputSpec.of({}), async () => {}, async ({ effects }) => invoke(effects, 'status'))
export const activateBtcGate = sdk.Action.withInput('btc-gate-activate', metadata('Enable Bounded BTC Swap Gate'),
  sdk.InputSpec.of({ confirmed: sdk.Value.toggle({ name: 'Enable the single-quote BTC gate on the next service restart', description: 'Fixed pilot: 1,000 BTC sats for 2,000 XBT sats. This is a test profile, not a market price. Does not publish an invoice, create credentials or start a payment. Requires Prepare Coordinator; restored gates stay blocked.', default: false }) }),
  async () => {}, async ({ effects, input }) => invoke(effects, 'activate', input.confirmed))
