import { sdk } from './sdk'
import { btcBackendId } from './utils'

const bitcoind = sdk.Dependency.optional('knots-prerdts', {
  enabled: async ({ effects }) => (await btcBackendId(effects)) === 'knots-prerdts',
  description: { en_US: 'Paul’s SHA256 companion with its historical-block fetching proxy. Pruning is supported.' },
  metadata: {
    title: 'Bitcoin Knots (SHA256) Companion',
    icon: 'https://raw.githubusercontent.com/Start9Labs/bitcoin-core-startos/feec0b1dae42961a257948fe39b40caf8672fce1/dep-icon.svg',
  },
  versionRange: '>=#knotsprerdts:31.2:0',
  kind: 'running',
  healthChecks: ['bitcoind', 'sync-progress'],
})

const standardBitcoin = sdk.Dependency.optional('bitcoind', {
  description: { en_US: 'SHA256 Bitcoin backend used when the companion is not installed. Historical blocks must be available.' },
  metadata: {
    title: 'Bitcoin',
    icon: 'https://raw.githubusercontent.com/Start9Labs/bitcoin-core-startos/feec0b1dae42961a257948fe39b40caf8672fce1/dep-icon.svg',
  },
  versionRange: '*',
  kind: 'running',
  healthChecks: ['bitcoind', 'sync-progress'],
  enabled: async ({ effects }) => (await btcBackendId(effects)) === 'bitcoind',
})

export const dependencies = sdk.Dependencies.of().addDependency(bitcoind).addDependency(standardBitcoin)
