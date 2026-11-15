import { setupManifest } from '@start9labs/start-sdk'
import { long, short } from './i18n'

export const manifest = setupManifest({
  id: 'c-lightning',
  title: 'Core Lightning (SHA256 Companion)',
  license: 'mit',
  packageRepo: 'https://github.com/BitcoinMechanic/btc-cln-startos',
  upstreamRepo: 'https://github.com/ElementsProject/lightning',
  marketingUrl: 'https://blockstream.com/lightning',
  donationUrl: null,
  description: { short, long },
  volumes: ['main', 'public'],
  virtualNetworking: true,
  images: {
    lightning: {
      source: { ociLayout: { path: '.build-inputs/lightning-x86_64.tar' } },
      arch: ['x86_64'],
      emulateMissing: false,
    },
    ui: {
      source: { ociLayout: { path: '.build-inputs/ui-x86_64.tar' } },
      arch: ['x86_64'],
      emulateMissing: false,
    },
  },
})
