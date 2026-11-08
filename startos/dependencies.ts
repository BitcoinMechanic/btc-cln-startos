import { sdk } from './sdk'

const bitcoind = sdk.Dependency.required('knots-prerdts', {
  description: { en_US: 'Paul’s SHA256 companion with its historical-block fetching proxy. Pruning is supported.' },
  metadata: {
    title: 'Bitcoin Knots (SHA256) Companion',
    icon: 'https://raw.githubusercontent.com/Start9Labs/bitcoin-core-startos/feec0b1dae42961a257948fe39b40caf8672fce1/dep-icon.svg',
  },
  versionRange: '>=#knotsprerdts:31.2:0',
  kind: 'running',
  healthChecks: ['bitcoind', 'sync-progress'],
})

export const dependencies = sdk.Dependencies.of().addDependency(bitcoind)
