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
      source: {
        dockerBuild: {
          dockerfile: 'scripts/suitbox/Dockerfile.runtime',
          workdir: '.',
        },
      },
      arch: ['x86_64'],
      emulateMissing: false,
    },
    ui: {
      source: {
        dockerBuild: {
          dockerfile: 'Dockerfile.ui',
          workdir: '.',
          buildArgs: {
            IMAGE:
              'ghcr.io/elementsproject/cln-application:26.09@sha256:27684e8e495d077ce661793f74b25d50c2e40f68552cb1ba57d6750dd2585798',
          },
        },
      },
      arch: ['x86_64'],
      emulateMissing: false,
    },
  },
})
